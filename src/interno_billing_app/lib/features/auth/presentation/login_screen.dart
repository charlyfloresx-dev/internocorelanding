import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/auth/presentation/company_selection_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/warehouse_selection_screen.dart';
import 'package:interno_billing_app/features/kiosk/presentation/kiosk_setup_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isCorporate = true;
  bool _isLoading = false;
  bool _isConfigured = false;
  String? _kioskCompanyId;
  String? _kioskCompanyName;

  @override
  void initState() {
    super.initState();
    _checkConfiguration();
  }

  Future<void> _checkConfiguration() async {
    final prefs = sl<SharedPreferences>();
    setState(() {
      _isConfigured = prefs.getString('api_url') != null;
      _kioskCompanyId = prefs.getString('kiosk_company_id');
      _kioskCompanyName = prefs.getString('kiosk_company_name');
    });
  }

  Future<void> _openKioskSetup() async {
    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const KioskSetupScreen()),
    );
    if (result == true) _checkConfiguration();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final cardBg = Theme.of(context).cardColor;

    return Scaffold(
      backgroundColor: scaffoldBg,
      body: SafeArea(
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 40),
                  Text(
                    _isCorporate ? 'login.corporate_prompt'.tr() : 'login.kiosk_prompt'.tr(),
                    style: TextStyle(
                      color: cs.onSurface,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Outfit',
                    ),
                  ),
                  const SizedBox(height: 32),
                  _buildTypeSelector(cs, cardBg),
                  if (!_isCorporate) ...[
                    const SizedBox(height: 16),
                    _buildKioskCompanyBadge(cs, cardBg),
                  ],
                  const SizedBox(height: 32),
                  _buildTextField(
                    controller: _emailController,
                    hintText: _isCorporate ? 'login.email_hint'.tr() : 'login.collaborator_id'.tr(),
                    icon: _isCorporate ? Icons.alternate_email : Icons.badge_outlined,
                    cs: cs,
                    cardBg: cardBg,
                  ),
                  const SizedBox(height: 16),
                  _buildTextField(
                    controller: _passwordController,
                    hintText: _isCorporate ? 'login.password'.tr() : 'login.pin'.tr(),
                    icon: Icons.lock_outline,
                    isPassword: true,
                    keyboardType: _isCorporate ? TextInputType.text : TextInputType.number,
                    cs: cs,
                    cardBg: cardBg,
                  ),
                  const SizedBox(height: 32),
                  _buildContinueButton(cs),
                  const SizedBox(height: 32),
                  _buildDivider(cs),
                  const SizedBox(height: 32),
                  _buildAuthOption(
                    icon: Icons.fingerprint,
                    label: 'login.biometrics'.tr(),
                    onTap: () {},
                    cs: cs,
                    cardBg: cardBg,
                  ),
                  const SizedBox(height: 16),
                  _buildAuthOption(
                    icon: _isConfigured ? Icons.cloud_done : Icons.qr_code_scanner,
                    label: _isConfigured ? 'login.device_linked'.tr() : 'login.scan_qr'.tr(),
                    color: _isConfigured ? InternoColors.cyan.withValues(alpha: 0.12) : null,
                    onTap: () => _openQRScanner(),
                    cs: cs,
                    cardBg: cardBg,
                  ),
                  const Spacer(),
                  Center(
                    child: Text(
                      'login.version'.tr(),
                      style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 10, letterSpacing: 1),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
            if (_isLoading)
              Container(
                color: Colors.black54,
                child: const Center(child: CircularProgressIndicator(color: InternoColors.cyan)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypeSelector(ColorScheme cs, Color cardBg) {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(color: cardBg, borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Expanded(
            child: _buildTypeButton('login.corporate'.tr(), _isCorporate, () => setState(() => _isCorporate = true), cs),
          ),
          Expanded(
            child: _buildTypeButton('login.kiosk'.tr(), !_isCorporate, () => setState(() => _isCorporate = false), cs),
          ),
        ],
      ),
    );
  }

  Widget _buildTypeButton(String label, bool isActive, VoidCallback onTap, ColorScheme cs) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isActive ? cs.onSurface.withValues(alpha: 0.08) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isActive ? InternoColors.cyan : cs.onSurface.withValues(alpha: 0.38),
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String hintText,
    required IconData icon,
    required ColorScheme cs,
    required Color cardBg,
    bool isPassword = false,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: cs.onSurface.withValues(alpha: 0.05)),
      ),
      child: TextField(
        controller: controller,
        obscureText: isPassword,
        keyboardType: keyboardType,
        style: TextStyle(color: cs.onSurface),
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 14),
          prefixIcon: Icon(icon, color: cs.onSurface.withValues(alpha: 0.38), size: 20),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Widget _buildContinueButton(ColorScheme cs) {
    return ElevatedButton(
      onPressed: _isLoading ? null : () => _handleManualLogin(),
      style: ElevatedButton.styleFrom(
        backgroundColor: cs.onSurface,
        foregroundColor: cs.surface,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: 0,
      ),
      child: Text(
        'login.continue_btn'.tr(),
        style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
      ),
    );
  }

  Widget _buildDivider(ColorScheme cs) {
    return Row(
      children: [
        Expanded(child: Divider(color: cs.onSurface.withValues(alpha: 0.08))),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Text('o', style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24))),
        ),
        Expanded(child: Divider(color: cs.onSurface.withValues(alpha: 0.08))),
      ],
    );
  }

  Widget _buildAuthOption({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
    required ColorScheme cs,
    required Color cardBg,
    Color? color,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color ?? cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: cs.onSurface.withValues(alpha: 0.05)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: cs.onSurface.withValues(alpha: 0.7), size: 20),
            const SizedBox(width: 12),
            Text(label, style: TextStyle(color: cs.onSurface.withValues(alpha: 0.7), fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildKioskCompanyBadge(ColorScheme cs, Color cardBg) {
    final isProvisioned = _kioskCompanyId != null;

    if (isProvisioned) {
      return GestureDetector(
        onLongPress: _openKioskSetup,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: InternoColors.cyan.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: InternoColors.cyan.withValues(alpha: 0.3)),
          ),
          child: Row(
            children: [
              const Icon(Icons.business, size: 16, color: InternoColors.cyan),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  _kioskCompanyName ?? _kioskCompanyId!,
                  style: const TextStyle(color: InternoColors.cyan, fontSize: 12, fontWeight: FontWeight.w600),
                ),
              ),
              GestureDetector(
                onTap: _openKioskSetup,
                child: Icon(Icons.settings_outlined, size: 16, color: cs.onSurface.withValues(alpha: 0.4)),
              ),
            ],
          ),
        ),
      );
    }

    // Unprovisioned — show configuration instructions
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, size: 16, color: Colors.amber),
              const SizedBox(width: 8),
              Text(
                'Kiosko sin empresa asignada',
                style: TextStyle(color: Colors.amber.shade700, fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            'Para activar este kiosko tienes dos opciones:',
            style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6), fontSize: 11),
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.admin_panel_settings_outlined, size: 14, color: cs.onSurface.withValues(alpha: 0.5)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Pide al administrador que configure este dispositivo.',
                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.5), fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.qr_code_scanner, size: 14, color: cs.onSurface.withValues(alpha: 0.5)),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  'Escanea el QR de sincronización desde el portal web (incluye empresa automáticamente).',
                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.5), fontSize: 11),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _openKioskSetup,
              icon: const Icon(Icons.settings_outlined, size: 14),
              label: const Text('Configurar ahora', style: TextStyle(fontSize: 12)),
              style: OutlinedButton.styleFrom(
                foregroundColor: Colors.amber.shade700,
                side: BorderSide(color: Colors.amber.withValues(alpha: 0.4)),
                padding: const EdgeInsets.symmetric(vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _handleManualLogin() async {
    setState(() => _isLoading = true);
    try {
      final dio = sl<Dio>();
      final prefs = sl<SharedPreferences>();

      Response response;
      if (_isCorporate) {
        response = await dio.post('auth/login', data: {
          'email': _emailController.text,
          'password': _passwordController.text,
        });
      } else {
        response = await dio.post('auth/collaborator-login', data: {
          'internal_id': _emailController.text,
          'identity_identifier': _passwordController.text,
          'access_method': 'PIN_PAD',
          if (_kioskCompanyId != null) 'company_id': _kioskCompanyId,
        });
      }

      if (response.statusCode == 200) {
        final data = response.data['data'];
        if (data['selection_token'] != null) {
          await prefs.setString('selection_token', data['selection_token']);
          final List<dynamic> companies = data['companies'] ?? [];
          if (mounted) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => CompanySelectionScreen(initialCompanies: companies)),
            );
          }
        } else if (data['access_token'] != null) {
          final String companyId = data['company_id'] ?? '';
          await prefs.setString('access_token', data['access_token']);
          if (data['refresh_token'] != null) {
            await prefs.setString('refresh_token', data['refresh_token']);
          }
          await prefs.setString('company_id', companyId);
          if (mounted) {
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => WarehouseSelectionScreen(companyId: companyId)),
            );
          }
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${'common.error'.tr()}: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _openQRScanner() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => _QRScannerModal(
        onScan: (data) => _handleAutoLogin(data),
        onManualConfig: () {
          Navigator.pop(context);
          _showManualIPDialog(context, 'http://192.168.1.146:8000', '/api/v1', '', '', '');
        },
      ),
    );
  }

  Future<void> _handleAutoLogin(String data) async {
    if (_isLoading) return;
    setState(() => _isLoading = true);
    try {
      final Map<String, dynamic> config = jsonDecode(data);
      final dio = sl<Dio>();
      final prefs = sl<SharedPreferences>();

      final String baseUrl = config['baseUrl'] ?? '';
      final String apiPrefix = config['apiPrefix'] ?? '/api/v1';
      final String selectionToken = config['selectionToken'] ?? '';
      final String companyId = config['companyId'] ?? '';
      final String companyName = config['companyName'] ?? '';

      if (baseUrl.isEmpty) throw Exception('QR code is missing baseUrl');

      final String cleanBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
      final String cleanPrefix = apiPrefix.startsWith('/') ? apiPrefix : '/$apiPrefix';
      final String fullApiUrl = '$cleanBase$cleanPrefix/';

      final testDio = Dio(BaseOptions(
        connectTimeout: const Duration(seconds: 4),
        receiveTimeout: const Duration(seconds: 4),
      ));

      try {
        final healthResponse = await testDio.get('${fullApiUrl}health');
        if (healthResponse.statusCode != 200) {
          throw Exception('Health check returned status ${healthResponse.statusCode}');
        }
      } catch (e) {
        if (mounted) {
          setState(() => _isLoading = false);
          _showManualIPDialog(context, cleanBase, apiPrefix, selectionToken, companyId, companyName);
        }
        return;
      }

      await prefs.setString('api_url', fullApiUrl);
      dio.options.baseUrl = fullApiUrl;
      // If QR includes company info, pre-provision the kiosk company
      if (companyId.isNotEmpty) {
        await prefs.setString('kiosk_company_id', companyId);
        if (companyName.isNotEmpty) await prefs.setString('kiosk_company_name', companyName);
        if (mounted) setState(() { _kioskCompanyId = companyId; _kioskCompanyName = companyName.isEmpty ? null : companyName; });
      }
      if (mounted) setState(() => _isConfigured = true);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Row(children: [
            const Icon(Icons.check_circle_rounded, color: Colors.greenAccent),
            const SizedBox(width: 12),
            Text('¡Conexión establecida!', style: TextStyle(fontWeight: FontWeight.bold)),
          ]),
          backgroundColor: Theme.of(context).cardColor,
          duration: const Duration(seconds: 2),
        ));
      }

      if (selectionToken.isNotEmpty) {
        final response = await dio.post(
          'auth/select-company',
          data: {'company_id': companyId},
          options: Options(headers: {'Authorization': 'Bearer $selectionToken'}),
        );

        if (response.statusCode == 200) {
          final responseData = response.data['data'];
          await prefs.setString('access_token', responseData['access_token']);
          if (responseData['refresh_token'] != null) {
            await prefs.setString('refresh_token', responseData['refresh_token']);
          }
          await prefs.setString('company_id', companyId);
          await prefs.setString('company_name', companyName);
          if (responseData['user_id'] != null) {
            await prefs.setString('user_id', responseData['user_id'].toString());
          }

          if (mounted) {
            Navigator.pop(context);
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => WarehouseSelectionScreen(companyId: companyId)),
            );
          }
        }
      } else {
        if (mounted) Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${'common.error'.tr()}: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _showManualIPDialog(
    BuildContext context,
    String scannedBase,
    String apiPrefix,
    String selectionToken,
    String companyId,
    String companyName,
  ) {
    final uri = Uri.tryParse(scannedBase);
    final portStr = uri != null && uri.hasPort ? '${uri.port}' : '8000';
    final initialIp = uri != null ? uri.host : scannedBase;

    final TextEditingController ipController = TextEditingController(text: initialIp);
    final TextEditingController portController = TextEditingController(text: portStr);

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) {
        bool isTesting = false;
        String? errorMessage;

        return StatefulBuilder(
          builder: (context, setStateDialog) {
            final cs = Theme.of(context).colorScheme;
            final cardBg = Theme.of(context).cardColor;

            return AlertDialog(
              backgroundColor: cardBg,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: Row(
                children: [
                  const Icon(Icons.wifi_off_rounded, color: Colors.amberAccent),
                  const SizedBox(width: 10),
                  Text('setup.adjust_conn'.tr(), style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold)),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'No se pudo conectar a $scannedBase.\n\nSi estás en desarrollo local, ingresa la IP de tu servidor en la red WiFi:',
                      style: TextStyle(color: cs.onSurface.withValues(alpha: 0.7), fontSize: 13, height: 1.4),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: TextField(
                            controller: ipController,
                            style: TextStyle(color: cs.onSurface, fontSize: 14),
                            decoration: InputDecoration(
                              labelText: 'IP del Servidor',
                              labelStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.5)),
                              hintText: '192.168.1.146',
                              hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.3)),
                              filled: true,
                              fillColor: cs.onSurface.withValues(alpha: 0.05),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 1,
                          child: TextField(
                            controller: portController,
                            keyboardType: TextInputType.number,
                            style: TextStyle(color: cs.onSurface, fontSize: 14),
                            decoration: InputDecoration(
                              labelText: 'Puerto',
                              labelStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.5)),
                              hintText: '8000',
                              hintStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.3)),
                              filled: true,
                              fillColor: cs.onSurface.withValues(alpha: 0.05),
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide.none),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (errorMessage != null) ...[
                      const SizedBox(height: 12),
                      Text(errorMessage!, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: isTesting ? null : () => Navigator.pop(dialogContext),
                  child: Text('common.cancel'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.5))),
                ),
                ElevatedButton(
                  onPressed: isTesting
                      ? null
                      : () async {
                          setStateDialog(() { isTesting = true; errorMessage = null; });

                          final ip = ipController.text.trim();
                          final port = portController.text.trim();
                          final cleanPrefix = apiPrefix.startsWith('/') ? apiPrefix : '/$apiPrefix';
                          final scheme = scannedBase.startsWith('https') ? 'https' : 'http';
                          final newBase = '$scheme://$ip${port.isNotEmpty ? ':$port' : ''}';
                          final testFullApiUrl = '$newBase$cleanPrefix/';

                          final testDio = Dio(BaseOptions(
                            connectTimeout: const Duration(seconds: 4),
                            receiveTimeout: const Duration(seconds: 4),
                          ));

                          try {
                            final healthResponse = await testDio.get('${testFullApiUrl}health');
                            if (healthResponse.statusCode == 200) {
                              final dio = sl<Dio>();
                              final prefs = sl<SharedPreferences>();

                              await prefs.setString('api_url', testFullApiUrl);
                              dio.options.baseUrl = testFullApiUrl;

                              if (mounted) setState(() => _isConfigured = true);

                              if (dialogContext.mounted) Navigator.pop(dialogContext);
                              if (context.mounted) Navigator.pop(context);

                              if (selectionToken.isNotEmpty) {
                                if (mounted) setState(() => _isLoading = true);
                                final response = await dio.post(
                                  'auth/select-company',
                                  data: {'company_id': companyId},
                                  options: Options(headers: {'Authorization': 'Bearer $selectionToken'}),
                                );

                                if (response.statusCode == 200) {
                                  final responseData = response.data['data'];
                                  await prefs.setString('access_token', responseData['access_token']);
                                  await prefs.setString('company_id', companyId);
                                  await prefs.setString('company_name', companyName);

                                  if (context.mounted) {
                                    Navigator.pushReplacement(
                                      context,
                                      MaterialPageRoute(builder: (_) => WarehouseSelectionScreen(companyId: companyId)),
                                    );
                                  }
                                }
                              }
                            } else {
                              throw Exception('Estado: ${healthResponse.statusCode}');
                            }
                          } catch (err) {
                            setStateDialog(() {
                              isTesting = false;
                              errorMessage = 'No se pudo conectar a $newBase.';
                            });
                          } finally {
                            if (mounted) setState(() => _isLoading = false);
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00C853),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: isTesting
                      ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                      : Text('setup.connect_test'.tr()),
                ),
              ],
            );
          },
        );
      },
    );
  }
}

class _QRScannerModal extends StatelessWidget {
  final Function(String) onScan;
  final VoidCallback onManualConfig;

  const _QRScannerModal({required this.onScan, required this.onManualConfig});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.8,
      decoration: const BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 24),
          Text('setup.link_device'.tr(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)),
          const SizedBox(height: 32),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: MobileScanner(
                onDetect: (capture) {
                  for (final barcode in capture.barcodes) {
                    if (barcode.rawValue != null) onScan(barcode.rawValue!);
                  }
                },
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text('setup.scan_dashboard'.tr(), style: const TextStyle(color: Colors.white38, fontSize: 12)),
          const SizedBox(height: 16),
          TextButton.icon(
            onPressed: onManualConfig,
            icon: const Icon(Icons.settings_ethernet_rounded, color: Colors.cyanAccent, size: 20),
            label: Text(
              'setup.adjust_manual'.tr(),
              style: const TextStyle(color: Colors.cyanAccent, fontWeight: FontWeight.bold, fontSize: 14, letterSpacing: 0.5),
            ),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              backgroundColor: Colors.white.withValues(alpha: 0.03),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: Colors.cyanAccent.withValues(alpha: 0.2)),
              ),
            ),
          ),
          const SizedBox(height: 48),
        ],
      ),
    );
  }
}
