import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
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
  List<Partner> _results = [];
  bool _isLoading = false;
  String? _error;

  void _onSearch(String query) async {
    if (query.isEmpty) {
      setState(() => _results = []);
      return;
    }

    setState(() => _isLoading = true);
    try {
      final scannerBloc = context.read<ScannerBloc>();
      final mode = scannerBloc.state.mode;
      final type = mode == ScannerMode.entry ? 'SUPPLIER' : 'CUSTOMER';
      
      final repo = context.read<PartnerRepository>();
      final results = await repo.searchPartners(query, type: type);
      setState(() {
        _results = results;
        _isLoading = false;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _error = 'Error buscando socios';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        color: Color(0xFF111111), // DARK SURFACE
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
            (context.read<ScannerBloc>().state.mode == ScannerMode.entry ? 'SELECCIONAR PROVEEDOR' : 'pos.select_customer'.tr()).toUpperCase(),
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
            decoration: InputDecoration(
              hintText: 'pos.search_hint'.tr(),
              hintStyle: const TextStyle(color: Colors.white38),
              prefixIcon: const Icon(Icons.search, color: InternoColors.cyan),
              filled: true,
              fillColor: Colors.white.withOpacity(0.05),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
            ),
            style: const TextStyle(color: Colors.white),
          ),
          const SizedBox(height: 20),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
                : _error != null
                    ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
                    : ListView.builder(
                        itemCount: _results.length,
                        itemBuilder: (context, index) {
                          final partner = _results[index];
                          return ListTile(
                            title: Text(
                              partner.name,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            subtitle: Text(partner.code, style: const TextStyle(color: Colors.white54)),
                            trailing: const Icon(Icons.chevron_right, color: Colors.white24),
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
