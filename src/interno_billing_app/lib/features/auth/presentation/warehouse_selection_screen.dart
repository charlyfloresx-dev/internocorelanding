import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/auth/data/auth_repository.dart';
import 'package:interno_billing_app/features/navigation/main_navigation_screen.dart';

class WarehouseSelectionScreen extends StatefulWidget {
  final String companyId;
  const WarehouseSelectionScreen({super.key, required this.companyId});

  @override
  State<WarehouseSelectionScreen> createState() => _WarehouseSelectionScreenState();
}

class _WarehouseSelectionScreenState extends State<WarehouseSelectionScreen> {
  List<Map<String, dynamic>> _warehouses = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadWarehouses();
  }

  Future<void> _loadWarehouses() async {
    try {
      final repo = sl<AuthRepository>();
      final warehouses = await repo.getWarehouses(widget.companyId);
      if (mounted) {
        setState(() {
          _warehouses = warehouses;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = 'Error al cargar almacenes: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text('SELECCIONAR ALMACÉN', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 2)),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: InternoColors.success))
          : _errorMessage != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
                        const SizedBox(height: 16),
                        Text(_errorMessage!, style: const TextStyle(color: Colors.white70), textAlign: TextAlign.center),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: () {
                            setState(() { _isLoading = true; _errorMessage = null; });
                            _loadWarehouses();
                          },
                          style: ElevatedButton.styleFrom(backgroundColor: InternoColors.cyan),
                          child: const Text('Reintentar'),
                        ),
                      ],
                    ),
                  ),
                )
              : _warehouses.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.warehouse_outlined, color: Colors.white24, size: 64),
                          const SizedBox(height: 16),
                          const Text('Sin almacenes disponibles', style: TextStyle(color: Colors.white38, fontSize: 16)),
                          const SizedBox(height: 8),
                          Text('Empresa: ${widget.companyId.substring(0, 8)}...', style: const TextStyle(color: Colors.white24, fontSize: 12)),
                        ],
                      ),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(24),
                      itemCount: _warehouses.length,
                      itemBuilder: (context, index) {
                        final warehouse = _warehouses[index];
                        final String whId = '${warehouse['id'] ?? ''}';
                        final String whName = warehouse['name'] ?? 'Almacén Sin Nombre';
                        final String whCode = warehouse['code'] ?? 'S/C';

                        return Card(
                          color: Colors.white.withValues(alpha: 0.05),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                          margin: const EdgeInsets.only(bottom: 16),
                          child: ListTile(
                            contentPadding: const EdgeInsets.all(16),
                            leading: const Icon(Icons.warehouse_outlined, color: InternoColors.success),
                            title: Text(whName, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            subtitle: Text(whCode, style: const TextStyle(color: Colors.white38)),
                            trailing: const Icon(Icons.chevron_right, color: Colors.white24),
                            onTap: () async {
                              final prefs = sl<SharedPreferences>();
                              await prefs.setString('warehouse_id', whId);
                              await prefs.setString('warehouse_name', whName);

                              if (mounted) {
                                Navigator.pushAndRemoveUntil(
                                  context,
                                  MaterialPageRoute(builder: (_) => const MainNavigationScreen()),
                                  (route) => false,
                                );
                              }
                            },
                          ),
                        );
                      },
                    ),
    );
  }
}
