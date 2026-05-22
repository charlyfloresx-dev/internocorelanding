import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/home/presentation/home_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/company_selection_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/warehouse_selection_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isCorporate = true;
  bool _isLoading = false;
  bool _isConfigured = false;

  @override
  void initState() {
    super.initState();
    _checkConfiguration();
  }

  Future<void> _checkConfiguration() async {
    final prefs = sl<SharedPreferences>();
    setState(() {
      _isConfigured = prefs.getString('api_url') != null;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
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
                    _isCorporate ? '¿Cuál es tu correo o\nID de operador?' : 'Ingresa tu ID y\nPIN de operador',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      fontFamily: 'Outfit',
                    ),
                  ),
                  const SizedBox(height: 32),
                  _buildTypeSelector(),
                  const SizedBox(height: 32),
                  _buildTextField(
                    controller: _emailController,
                    hintText: _isCorporate ? 'Correo electrónico' : 'ID de Colaborador',
                    icon: _isCorporate ? Icons.alternate_email : Icons.badge_outlined,
                  ),
                  const SizedBox(height: 16),
                  _buildTextField(
                    controller: _passwordController,
                    hintText: _isCorporate ? 'Contraseña' : 'PIN de Acceso',
                    icon: Icons.lock_outline,
                    isPassword: true,
                    keyboardType: _isCorporate ? TextInputType.text : TextInputType.number,
                  ),
                  const SizedBox(height: 32),
                  _buildContinueButton(),
                  const SizedBox(height: 32),
                  _buildDivider(),
                  const SizedBox(height: 32),
                  _buildAuthOption(
                    icon: Icons.fingerprint,
                    label: 'Acceder con Biometría',
                    onTap: () {},
                  ),
                  const SizedBox(height: 16),
                  _buildAuthOption(
                    icon: _isConfigured ? Icons.cloud_done : Icons.qr_code_scanner,
                    label: _isConfigured ? 'Dispositivo Vinculado' : 'Escanear QR de Acceso',
                    color: _isConfigured ? InternoColors.cyan : Colors.white10,
                    onTap: () => _openQRScanner(),
                  ),
                  const Spacer(),
                  const Center(
                    child: Text(
                      'V1.0.5 · TERMINAL INDUSTRIAL',
                      style: TextStyle(color: Colors.white24, fontSize: 10, letterSpacing: 1),
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

  Widget _buildTypeSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildTypeButton('CORPORATIVO', _isCorporate, () => setState(() => _isCorporate = true)),
          ),
          Expanded(
            child: _buildTypeButton('KIOSKO', !_isCorporate, () => setState(() => _isCorporate = false)),
          ),
        ],
      ),
    );
  }

  Widget _buildTypeButton(String label, bool isActive, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: BoxDecoration(
          color: isActive ? const Color(0xFF2A2A2A) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Center(
          child: Text(
            label,
            style: TextStyle(
              color: isActive ? InternoColors.cyan : Colors.white38,
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
    bool isPassword = false,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.05)),
      ),
      child: TextField(
        controller: controller,
        obscureText: isPassword,
        keyboardType: keyboardType,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          hintText: hintText,
          hintStyle: const TextStyle(color: Colors.white24, fontSize: 14),
          prefixIcon: Icon(icon, color: Colors.white38, size: 20),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(vertical: 16),
        ),
      ),
    );
  }

  Widget _buildContinueButton() {
    return ElevatedButton(
      onPressed: _isLoading ? null : () => _handleManualLogin(),
      style: ElevatedButton.styleFrom(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        minimumSize: const Size(double.infinity, 56),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        elevation: 0,
      ),
      child: const Text(
        'Continuar',
        style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16),
      ),
    );
  }

  Widget _buildDivider() {
    return Row(
      children: [
        Expanded(child: Divider(color: Colors.white.withOpacity(0.05))),
        const Padding(
          padding: EdgeInsets.symmetric(horizontal: 16),
          child: Text('o', style: TextStyle(color: Colors.white24)),
        ),
        Expanded(child: Divider(color: Colors.white.withOpacity(0.05))),
      ],
    );
  }

  Widget _buildAuthOption({required IconData icon, required String label, required VoidCallback onTap, Color? color}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: color ?? const Color(0xFF1A1A1A),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white.withOpacity(0.05)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: Colors.white70, size: 20),
            const SizedBox(width: 12),
            Text(label, style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold)),
          ],
        ),
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
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error de autenticación: ${e.toString()}')),
      );
    } finally {
      setState(() => _isLoading = false);
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
          Navigator.pop(context); // Cerrar la cámara
          _showManualIPDialog(
            context,
            'http://192.168.1.146:8000', // Sugerencia de IP local activa
            '/api/v1',
            '', // Sin token aún (configuración limpia)
            '',
            '',
          );
        },
      ),
    );
  }

  Future<void> _handleAutoLogin(String data) async {
    if (_isLoading) return; // Evitar procesamientos duplicados si el escáner dispara varias veces
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

      if (baseUrl.isEmpty) {
        throw Exception("QR code is missing baseUrl");
      }

      final String cleanBase = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
      final String cleanPrefix = apiPrefix.startsWith('/') ? apiPrefix : '/$apiPrefix';
      final String fullApiUrl = '$cleanBase$cleanPrefix/';

      // 1. Probar la conexión mediante el endpoint /health antes de guardar
      final testDio = Dio(BaseOptions(
        connectTimeout: const Duration(seconds: 4),
        receiveTimeout: const Duration(seconds: 4),
      ));

      try {
        final healthResponse = await testDio.get('${fullApiUrl}health');
        if (healthResponse.statusCode != 200) {
          throw Exception("Health check returned status ${healthResponse.statusCode}");
        }
      } catch (e) {
        setState(() => _isLoading = false);
        if (mounted) {
          // Mostrar de forma premium la ventana emergente de ajuste de IP manual
          _showManualIPDialog(context, cleanBase, apiPrefix, selectionToken, companyId, companyName);
        }
        return;
      }

      // Conexión exitosa -> Guardar base URL
      await prefs.setString('api_url', fullApiUrl);
      dio.options.baseUrl = fullApiUrl;
      setState(() => _isConfigured = true);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Row(
              children: [
                Icon(Icons.check_circle_rounded, color: Colors.greenAccent),
                SizedBox(width: 12),
                Text(
                  '¡Conexión establecida con éxito!',
                  style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            backgroundColor: Color(0xFF1E1E1E),
            duration: Duration(seconds: 2),
          ),
        );
      }

      if (selectionToken.isNotEmpty) {
        // 2. Intercambiar Selection Token por Access Token
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
            Navigator.pop(context); // Cerrar scanner modal
            Navigator.pushReplacement(
              context,
              MaterialPageRoute(builder: (_) => WarehouseSelectionScreen(companyId: companyId)),
            );
          }
        }
      } else {
        // Si solo se configuró el servidor sin login inmediato
        if (mounted) {
          Navigator.pop(context); // Cerrar scanner modal
        }
      }
    } catch (e) {
      print('QR Scan Error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error al procesar QR: ${e.toString()}'),
            backgroundColor: const Color(0xFF1E1E1E),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
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
            return AlertDialog(
              backgroundColor: const Color(0xFF15181F),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              title: const Row(
                children: [
                  Icon(Icons.wifi_off_rounded, color: Colors.amberAccent),
                  SizedBox(width: 10),
                  Text(
                    'Ajustar Conexión',
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'No se pudo conectar a $scannedBase.\n\n'
                      'Si estás en desarrollo local (Docker), ingresa la dirección IP de tu laptop/servidor en la red WiFi local:',
                      style: TextStyle(color: Colors.grey[300], fontSize: 13, height: 1.4),
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          flex: 3,
                          child: TextField(
                            controller: ipController,
                            style: const TextStyle(color: Colors.white, fontSize: 14),
                            decoration: InputDecoration(
                              labelText: 'IP del Servidor',
                              labelStyle: TextStyle(color: Colors.grey[400]),
                              hintText: '192.168.1.146',
                              hintStyle: TextStyle(color: Colors.grey[600]),
                              filled: true,
                              fillColor: const Color(0xFF1F2430),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: BorderSide.none,
                              ),
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
                            style: const TextStyle(color: Colors.white, fontSize: 14),
                            decoration: InputDecoration(
                              labelText: 'Puerto',
                              labelStyle: TextStyle(color: Colors.grey[400]),
                              hintText: '8000',
                              hintStyle: TextStyle(color: Colors.grey[600]),
                              filled: true,
                              fillColor: const Color(0xFF1F2430),
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(8),
                                borderSide: BorderSide.none,
                              ),
                              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                            ),
                          ),
                        ),
                      ],
                    ),
                    if (errorMessage != null) ...[
                      const SizedBox(height: 12),
                      Text(
                        errorMessage!,
                        style: const TextStyle(color: Colors.redAccent, fontSize: 12),
                      ),
                    ],
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: isTesting ? null : () => Navigator.pop(dialogContext),
                  child: Text('Cancelar', style: TextStyle(color: Colors.grey[400])),
                ),
                ElevatedButton(
                  onPressed: isTesting
                      ? null
                      : () async {
                          setStateDialog(() {
                            isTesting = true;
                            errorMessage = null;
                          });

                          final ip = ipController.text.trim();
                          final port = portController.text.trim();
                          final cleanPrefix = apiPrefix.startsWith('/') ? apiPrefix : '/$apiPrefix';
                          
                          // Construir nueva URL base
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
                              // Conexión exitosa! Guardar e iniciar sesión
                              final dio = sl<Dio>();
                              final prefs = sl<SharedPreferences>();
                              
                              await prefs.setString('api_url', testFullApiUrl);
                              dio.options.baseUrl = testFullApiUrl;
                              
                              if (mounted) {
                                setState(() => _isConfigured = true);
                              }

                              Navigator.pop(dialogContext); // Cerrar diálogo manual
                              Navigator.pop(context); // Cerrar scanner modal

                              if (selectionToken.isNotEmpty) {
                                setState(() => _isLoading = true);
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

                                  if (mounted) {
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
                              errorMessage = 'No se pudo conectar a $newBase.\nVerifica que la IP y el puerto sean correctos.';
                            });
                          } finally {
                            if (mounted) {
                              setState(() => _isLoading = false);
                            }
                          }
                        },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00C853),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  ),
                  child: isTesting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                        )
                      : const Text('Probar y Conectar'),
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
  
  const _QRScannerModal({
    required this.onScan,
    required this.onManualConfig,
  });

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
          const Text('VINCULAR DISPOSITIVO', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, letterSpacing: 2)),
          const SizedBox(height: 32),
          Expanded(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: MobileScanner(
                onDetect: (capture) {
                  final List<Barcode> barcodes = capture.barcodes;
                  for (final barcode in barcodes) {
                    if (barcode.rawValue != null) {
                      onScan(barcode.rawValue!);
                    }
                  }
                },
              ),
            ),
          ),
          const SizedBox(height: 24),
          const Text('Escanea el código del dashboard', style: TextStyle(color: Colors.white38, fontSize: 12)),
          const SizedBox(height: 16),
          TextButton.icon(
            onPressed: onManualConfig,
            icon: const Icon(Icons.settings_ethernet_rounded, color: Colors.cyanAccent, size: 20),
            label: const Text(
              'Ajustar conexión manualmente',
              style: TextStyle(
                color: Colors.cyanAccent,
                fontWeight: FontWeight.bold,
                fontSize: 14,
                letterSpacing: 0.5,
              ),
            ),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              backgroundColor: Colors.white.withOpacity(0.03),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(color: Colors.cyanAccent.withOpacity(0.2)),
              ),
            ),
          ),
          const SizedBox(height: 48),
        ],
      ),
    );
  }
}
