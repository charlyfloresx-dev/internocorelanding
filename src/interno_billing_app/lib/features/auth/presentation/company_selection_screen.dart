import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/auth/data/auth_repository.dart';
import 'package:interno_billing_app/features/auth/presentation/warehouse_selection_screen.dart';

class CompanySelectionScreen extends StatefulWidget {
  final List<dynamic>? initialCompanies;
  const CompanySelectionScreen({super.key, this.initialCompanies});

  @override
  State<CompanySelectionScreen> createState() => _CompanySelectionScreenState();
}

class _CompanySelectionScreenState extends State<CompanySelectionScreen> {
  List<dynamic> _companies = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    if (widget.initialCompanies != null) {
      _companies = widget.initialCompanies!;
      _isLoading = false;
    } else {
      _loadCompanies();
    }
  }

  Future<void> _loadCompanies() async {
    try {
      final repo = sl<AuthRepository>();
      final companies = await repo.getCompanies();
      if (mounted) {
        setState(() {
          _companies = companies;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar empresas: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        title: const Text('SELECCIONAR EMPRESA', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, letterSpacing: 2)),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
          : ListView.builder(
              padding: const EdgeInsets.all(24),
              itemCount: _companies.length,
              itemBuilder: (context, index) {
                final company = _companies[index];
                return Card(
                  color: Colors.white.withOpacity(0.05),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  margin: const EdgeInsets.only(bottom: 16),
                  child: ListTile(
                    contentPadding: const EdgeInsets.all(16),
                    leading: CircleAvatar(
                      backgroundColor: InternoColors.cyan.withOpacity(0.1),
                      child: Text((company['name'] ?? company['company_name'] ?? '?')[0].toUpperCase(), style: const TextStyle(color: InternoColors.cyan)),
                    ),
                    title: Text(company['name'] ?? company['company_name'] ?? 'Empresa Sin Nombre', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                    subtitle: Text(company['tax_id'] ?? 'RFC NO DISPONIBLE', style: const TextStyle(color: Colors.white38)),
                    trailing: const Icon(Icons.chevron_right, color: Colors.white24),
                    onTap: () async {
                      final prefs = sl<SharedPreferences>();
                      final String companyId = company['id'] ?? company['company_id'] ?? '';
                      final String companyName = company['name'] ?? company['company_name'] ?? '';
                      final String selectionToken = prefs.getString('selection_token') ?? '';

                      // Mostrar loader
                      showDialog(
                        context: context,
                        barrierDismissible: false,
                        builder: (context) => const Center(
                          child: CircularProgressIndicator(color: InternoColors.cyan),
                        ),
                      );

                      try {
                        final dio = sl<Dio>();
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
                            await prefs.setString('user_id', responseData['user_id']);
                          }

                          // Quitar loader
                          if (mounted) Navigator.pop(context);

                          if (mounted) {
                            Navigator.pushReplacement(
                              context,
                              MaterialPageRoute(
                                builder: (_) => WarehouseSelectionScreen(companyId: companyId),
                              ),
                            );
                          }
                        } else {
                          throw Exception("Código de estado no exitoso: ${response.statusCode}");
                        }
                      } catch (e) {
                        // Quitar loader
                        if (mounted) Navigator.pop(context);

                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Error al establecer empresa: ${e.toString()}'),
                              backgroundColor: Colors.redAccent,
                            ),
                          );
                        }
                      }
                    },
                  ),
                );
              },
            ),
    );
  }
}
