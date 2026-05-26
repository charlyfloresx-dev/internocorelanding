import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/partner_repository.dart';
import 'package:interno_billing_app/domain/entities/partner.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';

class PartnerSearchModal extends StatefulWidget {
  const PartnerSearchModal({super.key});

  @override
  State<PartnerSearchModal> createState() => _PartnerSearchModalState();
}

class _PartnerSearchModalState extends State<PartnerSearchModal> {
  final TextEditingController _searchController = TextEditingController();
  List<Partner> _allPartners = [];
  List<Partner> _filtered = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    final mode = context.read<ScannerBloc>().state.mode;
    final type = mode == ScannerMode.entry ? 'SUPPLIER' : 'CUSTOMER';
    try {
      final repo = sl<PartnerRepository>();
      final results = await repo.getPartners(type: type);
      if (!mounted) return;
      setState(() {
        _allPartners = results;
        _filtered = results;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _error = 'Error cargando socios';
      });
    }
  }

  void _onSearch(String query) {
    final q = query.toLowerCase().trim();
    setState(() {
      _filtered = q.isEmpty
          ? _allPartners
          : _allPartners
              .where((p) =>
                  p.name.toLowerCase().contains(q) ||
                  p.code.toLowerCase().contains(q))
              .toList();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mode = context.read<ScannerBloc>().state.mode;
    final title = mode == ScannerMode.entry ? 'SELECCIONAR PROVEEDOR' : 'pos.select_customer'.tr().toUpperCase();

    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        color: Color(0xFF111111),
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          Container(
            width: 40,
            height: 4,
            margin: const EdgeInsets.only(bottom: 20),
            decoration: BoxDecoration(
              color: Colors.white24,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          Text(
            title,
            style: const TextStyle(
              fontFamily: 'Inter',
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: Colors.white70,
              letterSpacing: 2,
            ),
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _searchController,
            onChanged: _onSearch,
            autofocus: false,
            decoration: InputDecoration(
              hintText: 'pos.search_hint'.tr(),
              hintStyle: const TextStyle(color: Colors.white38),
              prefixIcon: const Icon(Icons.search, color: InternoColors.cyan),
              filled: true,
              fillColor: Colors.white.withValues(alpha: 0.05),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
            ),
            style: const TextStyle(color: Colors.white),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
                : _error != null
                    ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                    : _filtered.isEmpty
                        ? Center(
                            child: Text(
                              _searchController.text.isEmpty ? 'Sin resultados' : 'Sin coincidencias',
                              style: const TextStyle(color: Colors.white38, fontSize: 13),
                            ),
                          )
                        : ListView.builder(
                            itemCount: _filtered.length,
                            itemBuilder: (context, index) {
                              final partner = _filtered[index];
                              final current = context.read<ScannerBloc>().state.selectedPartner;
                              return ListTile(
                                title: Text(
                                  partner.name,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                subtitle: Text(partner.code, style: const TextStyle(color: Colors.white54)),
                                trailing: current?.id == partner.id
                                    ? const Icon(Icons.check_circle, color: InternoColors.success, size: 20)
                                    : const Icon(Icons.chevron_right, color: Colors.white24),
                                onTap: () {
                                  context.read<ScannerBloc>().add(SelectPartner(partner));
                                  Navigator.pop(context);
                                },
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}
