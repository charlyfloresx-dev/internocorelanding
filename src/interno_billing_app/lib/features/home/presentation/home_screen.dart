import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/core/theme/theme_notifier.dart';
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
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (sheetCtx) => _ConfigSheet(),
    );
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

}

// ── Config Bottom Sheet ────────────────────────────────────────────────────────

class _ConfigSheet extends StatelessWidget {
  const _ConfigSheet();

  @override
  Widget build(BuildContext context) {
    final themeNotifier = context.watch<ThemeNotifier>();
    final isDark = themeNotifier.isDark;
    final isEs = context.locale.languageCode == 'es';

    final sheetBg = isDark ? const Color(0xFF0D0D0D) : Colors.white;
    final labelColor = isDark ? Colors.white38 : const Color(0xFF94A3B8);
    final borderColor = isDark ? Colors.white10 : const Color(0xFFE2E8F0);

    return Container(
      decoration: BoxDecoration(
        color: sheetBg,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
      ),
      padding: const EdgeInsets.fromLTRB(24, 16, 24, 40),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: isDark ? Colors.white12 : const Color(0xFFCBD5E1),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Title
          Text(
            'config.title'.tr(),
            style: TextStyle(
              color: isDark ? Colors.white : const Color(0xFF0F172A),
              fontSize: 13,
              fontWeight: FontWeight.w900,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 24),

          // ── TEMA ──────────────────────────────────────────────────────────
          Text('config.theme'.tr(),
              style: TextStyle(color: labelColor, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 2)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: _Chip(
              icon: Icons.dark_mode_outlined,
              label: 'config.dark'.tr(),
              selected: isDark,
              isDark: isDark,
              onTap: () => context.read<ThemeNotifier>().setMode(ThemeMode.dark),
            )),
            const SizedBox(width: 10),
            Expanded(child: _Chip(
              icon: Icons.light_mode_outlined,
              label: 'config.light'.tr(),
              selected: !isDark,
              isDark: isDark,
              onTap: () => context.read<ThemeNotifier>().setMode(ThemeMode.light),
            )),
          ]),
          const SizedBox(height: 24),

          Divider(color: borderColor, height: 1),
          const SizedBox(height: 24),

          // ── IDIOMA ────────────────────────────────────────────────────────
          Text('config.language'.tr(),
              style: TextStyle(color: labelColor, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 2)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(child: _Chip(
              label: 'config.spanish'.tr(),
              selected: isEs,
              isDark: isDark,
              onTap: () => context.setLocale(const Locale('es')),
            )),
            const SizedBox(width: 10),
            Expanded(child: _Chip(
              label: 'config.english'.tr(),
              selected: !isEs,
              isDark: isDark,
              onTap: () => context.setLocale(const Locale('en')),
            )),
          ]),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final bool selected;
  final bool isDark;
  final VoidCallback onTap;
  final IconData? icon;

  const _Chip({
    required this.label,
    required this.selected,
    required this.isDark,
    required this.onTap,
    this.icon,
  });

  @override
  Widget build(BuildContext context) {
    final activeBg = isDark ? Colors.white : const Color(0xFF0F172A);
    final activeText = isDark ? Colors.black : Colors.white;
    final inactiveBg = isDark ? const Color(0xFF1A1A1A) : const Color(0xFFF1F5F9);
    final inactiveBorder = isDark ? Colors.white10 : const Color(0xFFCBD5E1);
    final inactiveText = isDark ? Colors.white38 : const Color(0xFF94A3B8);

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        height: 52,
        decoration: BoxDecoration(
          color: selected ? activeBg : inactiveBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected ? activeBg : inactiveBorder,
            width: selected ? 0 : 1,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (icon != null) ...[
              Icon(icon, size: 15, color: selected ? activeText : inactiveText),
              const SizedBox(width: 6),
            ],
            Text(
              label,
              style: TextStyle(
                color: selected ? activeText : inactiveText,
                fontSize: 11,
                fontWeight: FontWeight.bold,
                letterSpacing: 1,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
