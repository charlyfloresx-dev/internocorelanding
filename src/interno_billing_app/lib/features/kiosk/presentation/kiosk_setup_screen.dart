import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';

/// Admin provisions this kiosk device to a specific company.
/// After setup, collaborator logins always include the stored company_id.
class KioskSetupScreen extends StatefulWidget {
  const KioskSetupScreen({super.key});

  @override
  State<KioskSetupScreen> createState() => _KioskSetupScreenState();
}

class _KioskSetupScreenState extends State<KioskSetupScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _isLoading = false;
  String? _error;

  // State when we got a selection_token (multiple companies)
  String? _selectionToken;
  List<Map<String, dynamic>> _companies = [];

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  Future<void> _adminLogin() async {
    final email = _emailCtrl.text.trim();
    final pass = _passCtrl.text.trim();
    if (email.isEmpty || pass.isEmpty) {
      setState(() => _error = 'Ingresa email y contraseña.');
      return;
    }
    setState(() { _isLoading = true; _error = null; });
    try {
      final dio = sl<Dio>();
      final resp = await dio.post('auth/login', data: {'email': email, 'password': pass});
      final data = resp.data['data'] as Map<String, dynamic>;

      if (data['selection_token'] != null) {
        final List<dynamic> raw = data['companies'] ?? [];
        setState(() {
          _selectionToken = data['selection_token'] as String;
          _companies = raw.cast<Map<String, dynamic>>();
        });
      } else {
        await _finalizeProvisioning(
          companyId: data['company_id'] as String,
          companyName: data['company_name'] as String? ?? '',
        );
      }
    } on DioException catch (e) {
      setState(() => _error = e.response?.data?['message'] ?? 'Error de conexión.');
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _selectCompany(String companyId, String companyName) async {
    if (_selectionToken == null) return;
    setState(() { _isLoading = true; _error = null; });
    try {
      final dio = sl<Dio>();
      await dio.post(
        'auth/select-company',
        data: {'company_id': companyId},
        options: Options(headers: {'Authorization': 'Bearer $_selectionToken'}),
      );
      await _finalizeProvisioning(companyId: companyId, companyName: companyName);
    } on DioException catch (e) {
      setState(() => _error = e.response?.data?['message'] ?? 'Error al seleccionar empresa.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _finalizeProvisioning({required String companyId, required String companyName}) async {
    final prefs = sl<SharedPreferences>();
    await prefs.setString('kiosk_company_id', companyId);
    await prefs.setString('kiosk_company_name', companyName);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Kiosko configurado para: $companyName'),
          backgroundColor: Colors.green.shade700,
        ),
      );
      Navigator.of(context).pop(true); // return true → LoginScreen refreshes
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final cardBg = Theme.of(context).cardColor;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: Icon(Icons.arrow_back_ios, color: cs.onSurface),
          onPressed: () => Navigator.of(context).pop(false),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 16),
              Text(
                'Configurar Kiosko',
                style: TextStyle(
                  color: cs.onSurface,
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  fontFamily: 'Outfit',
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Ingresa credenciales de administrador para vincular este kiosko a una empresa.',
                style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6), fontSize: 14),
              ),
              const SizedBox(height: 32),

              if (_selectionToken == null) ...[
                // ── Admin login form ──────────────────────────────────────────
                _buildField(label: 'Email del administrador', ctrl: _emailCtrl, icon: Icons.alternate_email, cs: cs, cardBg: cardBg),
                const SizedBox(height: 16),
                _buildField(label: 'Contraseña', ctrl: _passCtrl, icon: Icons.lock_outline, cs: cs, cardBg: cardBg, obscure: true),
                const SizedBox(height: 8),
                if (_error != null) _buildError(_error!),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _adminLogin,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: InternoColors.cyan,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: _isLoading
                        ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                        : const Text('Continuar', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                  ),
                ),
              ] else ...[
                // ── Company selection ─────────────────────────────────────────
                Text(
                  'Selecciona la empresa para este kiosko:',
                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.7), fontSize: 14),
                ),
                const SizedBox(height: 16),
                if (_error != null) _buildError(_error!),
                ..._companies.map((c) {
                  final cId = c['company_id'] as String? ?? '';
                  final cName = c['company_name'] as String? ?? cId;
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      onTap: _isLoading ? null : () => _selectCompany(cId, cName),
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: cardBg,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: cs.onSurface.withValues(alpha: 0.15)),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.business_outlined, color: InternoColors.cyan),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(cName, style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.w600)),
                            ),
                            Icon(Icons.chevron_right, color: cs.onSurface.withValues(alpha: 0.4)),
                          ],
                        ),
                      ),
                    ),
                  );
                }),
                if (_isLoading)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Center(child: CircularProgressIndicator()),
                  ),
              ],
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildField({
    required String label,
    required TextEditingController ctrl,
    required IconData icon,
    required ColorScheme cs,
    required Color cardBg,
    bool obscure = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6), fontSize: 12, fontWeight: FontWeight.w600)),
        const SizedBox(height: 6),
        Container(
          decoration: BoxDecoration(color: cardBg, borderRadius: BorderRadius.circular(12)),
          child: TextField(
            controller: ctrl,
            obscureText: obscure,
            style: TextStyle(color: cs.onSurface),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: cs.onSurface.withValues(alpha: 0.5), size: 20),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildError(String msg) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: Colors.red.shade900.withValues(alpha: 0.3), borderRadius: BorderRadius.circular(8)),
          child: Row(
            children: [
              const Icon(Icons.error_outline, color: Colors.redAccent, size: 16),
              const SizedBox(width: 8),
              Expanded(child: Text(msg, style: const TextStyle(color: Colors.redAccent, fontSize: 12))),
            ],
          ),
        ),
      );
}
