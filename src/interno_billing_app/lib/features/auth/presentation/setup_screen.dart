import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/auth/presentation/login_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/warehouse_selection_screen.dart';
import 'package:interno_billing_app/features/navigation/main_navigation_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final MobileScannerController controller = MobileScannerController();
  bool _isProcessing = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _checkExistingSession();
    });
  }

  Future<void> _checkExistingSession() async {
    final prefs = sl<SharedPreferences>();
    final savedApiUrl = prefs.getString('api_url');

    if (savedApiUrl == null || savedApiUrl.isEmpty) return;

    final dio = sl<Dio>();
    dio.options.baseUrl = savedApiUrl;

    final savedRefreshToken = prefs.getString('refresh_token');
    if (savedRefreshToken == null || savedRefreshToken.isEmpty) {
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
      }
      return;
    }

    setState(() => _isProcessing = true);

    try {
      final response = await dio.post('auth/refresh', data: {'refresh_token': savedRefreshToken});

      if (response.statusCode == 200) {
        final responseData = response.data['data'];

        await prefs.setString('access_token', responseData['access_token']);
        if (responseData['refresh_token'] != null) {
          await prefs.setString('refresh_token', responseData['refresh_token']);
        }

        final String companyId = responseData['company_id'] ?? '';
        final String companyName = responseData['company_name'] ?? '';
        final String userId = responseData['user_id'] ?? '';

        await prefs.setString('company_id', companyId);
        await prefs.setString('company_name', companyName);
        await prefs.setString('user_id', userId);

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Row(
                children: [
                  Icon(Icons.offline_bolt_rounded, color: Color(0xFF00E676)),
                  SizedBox(width: 12),
                  Text('Sesión reanudada con éxito', style: TextStyle(fontWeight: FontWeight.bold)),
                ],
              ),
              backgroundColor: Color(0xFF1E1E1E),
              duration: Duration(seconds: 1),
            ),
          );

          final savedWarehouseId = prefs.getString('warehouse_id');
          if (savedWarehouseId != null && savedWarehouseId.isNotEmpty) {
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const MainNavigationScreen()));
          } else {
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => WarehouseSelectionScreen(companyId: companyId)));
          }
        }
      } else {
        throw Exception('Unexpected response code');
      }
    } catch (e) {
      if (e is DioException &&
          e.type != DioExceptionType.connectionTimeout &&
          e.type != DioExceptionType.receiveTimeout &&
          e.response?.statusCode != null &&
          (e.response!.statusCode == 401 || e.response!.statusCode == 403)) {
        await prefs.remove('access_token');
        await prefs.remove('refresh_token');
      }

      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
      }
    } finally {
      if (mounted) setState(() => _isProcessing = false);
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  Future<void> _handleScan(String code) async {
    if (_isProcessing) return;

    String? urlToSave;

    try {
      if (code.startsWith('{')) {
        final Map<String, dynamic> fullConfig = jsonDecode(code);
        final String baseUrl = fullConfig['baseUrl'] ?? '';
        final String apiPrefix = fullConfig['apiPrefix'] ?? '/api/v1';
        if (baseUrl.isNotEmpty) {
          urlToSave = '$baseUrl$apiPrefix${apiPrefix.endsWith('/') ? '' : '/'}';
        }
      } else if (code.startsWith('http')) {
        urlToSave = code;
      }

      if (urlToSave != null) {
        setState(() => _isProcessing = true);

        final prefs = sl<SharedPreferences>();
        await prefs.setString('api_url', urlToSave);
        sl<Dio>().options.baseUrl = urlToSave;

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('CONFIGURACIÓN GUARDADA: $urlToSave'), backgroundColor: InternoColors.success),
          );
          Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
        }
      }
    } catch (e) {
      debugPrint('Scan error: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          MobileScanner(
            controller: controller,
            onDetect: (capture) {
              for (final barcode in capture.barcodes) {
                if (barcode.rawValue != null) _handleScan(barcode.rawValue!);
              }
            },
          ),
          _buildOverlay(),
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(32.0),
              child: Column(
                children: [
                  Text(
                    'setup.connect'.tr(),
                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w900, letterSpacing: 3),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'setup.scan_qr'.tr(),
                    style: const TextStyle(color: Colors.white38, fontSize: 10),
                  ),
                  const Spacer(),
                  if (_isProcessing)
                    const CircularProgressIndicator(color: InternoColors.cyan),
                  const Spacer(),
                  _buildManualFallback(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildOverlay() {
    return Center(
      child: Container(
        width: 250,
        height: 250,
        decoration: BoxDecoration(
          border: Border.all(color: InternoColors.cyan, width: 2),
          borderRadius: BorderRadius.circular(24),
        ),
      ),
    );
  }

  Widget _buildManualFallback() {
    return TextButton(
      onPressed: () => _showManualDialog(),
      child: Text(
        'setup.manual_config'.tr(),
        style: const TextStyle(color: Colors.white24, fontSize: 11, decoration: TextDecoration.underline),
      ),
    );
  }

  void _showManualDialog() {
    final urlController = TextEditingController(text: 'http://10.0.2.2:8000/api/v1/');
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: Text('setup.manual_title'.tr(), style: const TextStyle(color: Colors.white)),
        content: TextField(
          controller: urlController,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            labelText: 'setup.url'.tr(),
            labelStyle: const TextStyle(color: Colors.white38),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('setup.cancel'.tr()),
          ),
          TextButton(
            onPressed: () => _handleScan(urlController.text),
            child: Text('setup.save'.tr()),
          ),
        ],
      ),
    );
  }
}
