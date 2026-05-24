import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/scanner_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/inventory_stock_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/login_screen.dart';
import 'package:interno_billing_app/features/auth/presentation/warehouse_selection_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _userName = 'Operador Interno';
  String _companyName = 'Cargando...';
  String _warehouseName = 'Sin Almacén';

  @override
  void initState() {
    super.initState();
    _loadUserInfo();
  }

  Future<void> _loadUserInfo() async {
    final prefs = sl<SharedPreferences>();
    setState(() {
      _userName = prefs.getString('user_name') ?? 'Carlos Javier';
      _companyName = prefs.getString('company_name') ?? 'Interno Enterprise';
      _warehouseName = prefs.getString('warehouse_name') ?? 'Almacén Central';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // ─── Header: Perfil Estilo Uber ────────────────────────────────
              _buildProfileHeader(),
              
              const SizedBox(height: 16),
              
              // ─── Quick Actions Grid ───────────────────────────────────────
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    _buildQuickAction(Icons.help_outline, 'Ayuda'),
                    const SizedBox(width: 12),
                    _buildQuickAction(Icons.security_outlined, 'Seguridad'),
                    const SizedBox(width: 12),
                    _buildQuickAction(Icons.settings_outlined, 'Config.', onTap: () => _showConfigMenu()),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // ─── Main Menu Items ──────────────────────────────────────────
              _buildMenuSection('OPERACIONES DE ALMACÉN'),
              _buildMenuItem(
                icon: Icons.inventory_2_rounded,
                title: 'Entradas de Mercancía',
                subtitle: 'Escanear y registrar nuevos ingresos',
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ScannerScreen()),
                ),
              ),
              _buildMenuItem(
                icon: Icons.receipt_long_rounded,
                title: 'Mis Recibos / Documentos',
                subtitle: 'Historial de movimientos realizados',
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const InventoryStockScreen()),
                ),
              ),
              
              const SizedBox(height: 32),
              
              _buildMenuSection('GESTIÓN'),
              _buildMenuItem(
                icon: Icons.person_outline,
                title: 'Perfil del Usuario',
                subtitle: 'Preferencias y sesión activa',
                onTap: () => _showProfileDialog(),
              ),
              _buildMenuItem(
                icon: Icons.support_agent_rounded,
                title: 'Tickets de Soporte',
                subtitle: 'Reportar fallas o solicitar ayuda',
                onTap: () {
                  // This is handled by the tab index in MainNavigationScreen
                  // but we can also navigate directly if needed
                },
              ),
              _buildMenuItem(
                icon: Icons.warehouse_outlined,
                title: 'Cambiar Almacén',
                subtitle: 'Seleccionar ubicación operativa',
                onTap: () async {
                  final prefs = sl<SharedPreferences>();
                  final companyId = prefs.getString('company_id') ?? '';
                  if (context.mounted) {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(
                        builder: (_) => WarehouseSelectionScreen(companyId: companyId),
                      ),
                    );
                  }
                },
              ),
              _buildMenuItem(
                icon: Icons.qr_code_scanner_rounded,
                title: 'Reconectar Servidor',
                subtitle: 'Escanear QR de vinculación del portal',
                accentColor: InternoColors.cyan,
                onTap: () => _confirmReconnect(),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildProfileHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(24),
      margin: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A1A),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 35,
                backgroundColor: InternoColors.success.withValues(alpha:0.2),
                child: const Icon(Icons.person, color: InternoColors.success, size: 40),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _userName.toUpperCase(),
                      style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w900, fontFamily: 'Outfit'),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        const Icon(Icons.star, color: Colors.amber, size: 14),
                        const SizedBox(width: 4),
                        Text('4.96 • Operador Pro', style: TextStyle(color: Colors.white.withValues(alpha:0.5), fontSize: 12)),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Text(
            _companyName,
            style: const TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1),
          ),
          Text(
            _warehouseName,
            style: const TextStyle(color: InternoColors.success, fontSize: 14, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAction(IconData icon, String label, {VoidCallback? onTap}) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            color: const Color(0xFF1A1A1A),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              Icon(icon, color: Colors.white, size: 24),
              const SizedBox(height: 8),
              Text(label, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMenuSection(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: Text(
        title,
        style: TextStyle(color: Colors.white.withValues(alpha:0.3), fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1),
      ),
    );
  }

  Widget _buildMenuItem({required IconData icon, required String title, required String subtitle, required VoidCallback onTap, Color? accentColor}) {
    final color = accentColor ?? Colors.white;
    return ListTile(
      onTap: onTap,
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      leading: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: color.withValues(alpha: 0.08), shape: BoxShape.circle),
        child: Icon(icon, color: color, size: 28),
      ),
      title: Text(title, style: TextStyle(color: color, fontSize: 16, fontWeight: FontWeight.bold)),
      subtitle: Text(subtitle, style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12)),
      trailing: Icon(Icons.chevron_right, color: color.withValues(alpha: 0.3)),
    );
  }

  void _showConfigMenu() {
    _confirmReconnect();
  }

  void _confirmReconnect() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Row(
          children: [
            Icon(Icons.qr_code_scanner_rounded, color: InternoColors.cyan, size: 24),
            SizedBox(width: 12),
            Text('Reconectar Servidor', style: TextStyle(color: Colors.white, fontSize: 18)),
          ],
        ),
        content: const Text(
          'Esto desvinculará este dispositivo del servidor actual. Necesitarás escanear el QR del portal web para volver a conectarte.',
          style: TextStyle(color: Colors.white70, fontSize: 14),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('CANCELAR', style: TextStyle(color: Colors.white38)),
          ),
          TextButton(
            onPressed: () async {
              Navigator.pop(ctx);
              final prefs = sl<SharedPreferences>();
              await prefs.remove('base_url');
              await prefs.remove('access_token');
              await prefs.remove('refresh_token');
              await prefs.remove('company_id');
              await prefs.remove('warehouse_id');
              await prefs.remove('company_name');
              await prefs.remove('warehouse_name');
              if (mounted) {
                Navigator.pushAndRemoveUntil(
                  context,
                  MaterialPageRoute(builder: (_) => const LoginScreen()),
                  (route) => false,
                );
              }
            },
            child: const Text('DESCONECTAR Y ESCANEAR', style: TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  void _showProfileDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text('SESIÓN ACTIVA', style: TextStyle(color: Colors.white)),
        content: Text('Usted está logueado como $_userName en $_companyName.', style: const TextStyle(color: Colors.white70)),
        actions: [
          TextButton(
            onPressed: () async {
              final prefs = sl<SharedPreferences>();
              await prefs.clear();
              if (mounted) {
                Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => const LoginScreen()), (route) => false);
              }
            },
            child: const Text('CERRAR SESIÓN', style: TextStyle(color: Colors.red)),
          ),
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('CERRAR')),
        ],
      ),
    );
  }
}
