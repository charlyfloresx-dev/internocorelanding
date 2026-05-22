import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/scanner/presentation/payment_confirmation_screen.dart';

class CheckoutScreen extends StatelessWidget {
  const CheckoutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final prefs = sl<SharedPreferences>();
    final warehouseId = prefs.getString('warehouse_id') ?? 'MAIN_WH';
    final terminalName = prefs.getString('terminal_name') ?? 'POS_01';

    return BlocConsumer<ScannerBloc, ScannerState>(
      listener: (context, state) {
        if (state.successMessage != null && state.items.isEmpty) {
          // Sale completed → go back
          Navigator.of(context).pop();
        }
        if (state.error != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.error!), backgroundColor: Colors.red),
          );
        }
      },
      builder: (context, state) {
        return Scaffold(
          backgroundColor: Colors.black,
          appBar: AppBar(
            backgroundColor: Colors.black,
            title: Text(state.mode == ScannerMode.entry ? 'RESUMEN DE ENTRADA' : 'pos.sale_summary'.tr()),
            centerTitle: true,
          ),
          body: Column(
            children: [
              // ── Header Info ──────────────────────────────────────────────────
              Container(
                padding: const EdgeInsets.all(16),
                color: (state.mode == ScannerMode.entry ? InternoColors.success : InternoColors.cyan).withOpacity(0.05),
                child: Row(
                  children: [
                    const Icon(Icons.location_on, color: InternoColors.cyan, size: 16),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${'pos.terminal'.tr()}: $terminalName | ${'pos.warehouse'.tr()}: ${warehouseId.length > 8 ? warehouseId.substring(0, 8) : warehouseId}...',
                        style: const TextStyle(color: Colors.white70, fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                  ],
                ),
              ),

              // ── Items List ───────────────────────────────────────────────────
              Expanded(
                child: ListView.builder(
                  itemCount: state.items.length,
                  itemBuilder: (context, index) {
                    final item = state.items[index];
                    return ListTile(
                      title: Text(
                        '${item.product.name} ${item.product.brandName != null ? "(${item.product.brandName})" : ""}', 
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)
                      ),
                      subtitle: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${item.quantity} ${item.product.uomName ?? "PZ"} x \$${item.product.price?.amount?.toStringAsFixed(2) ?? "0.00"}',
                            style: const TextStyle(color: Colors.white60),
                          ),
                          if (item.product.currentStock != null)
                            Text(
                              'Stock: ${item.product.currentStock} ${item.product.uomName ?? ""}',
                              style: TextStyle(
                                fontSize: 10,
                                color: (item.product.currentStock ?? 0) > 0 ? (state.mode == ScannerMode.entry ? InternoColors.success : InternoColors.cyan) : Colors.red,
                              ),
                            ),
                        ],
                      ),
                      trailing: Text(
                        '\$${(item.lineTotal).toStringAsFixed(2)}',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    );
                  },
                ),
              ),

              // ── Totals Footer ────────────────────────────────────────────────
              Container(
                padding: const EdgeInsets.all(24),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A1A1A),
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.5),
                      blurRadius: 20,
                      offset: const Offset(0, -5),
                    ),
                  ],
                ),
                child: SafeArea(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _buildRow('pos.subtotal'.tr(), '\$${state.subtotal.toStringAsFixed(2)}'),
                      const SizedBox(height: 8),
                      _buildRow('pos.tax'.tr(args: ['${(state.taxRate * 100).toInt()}']), '\$${state.totalTax.toStringAsFixed(2)}'),
                      const Divider(height: 32, color: Colors.white10),
                      _buildRow(
                        'pos.total'.tr().toUpperCase(),
                        '\$${state.grandTotal.toStringAsFixed(2)}',
                        isTotal: true,
                      ),
                      const SizedBox(height: 32),
                      SizedBox(
                        width: double.infinity,
                        height: 60,
                        child: ElevatedButton(
                          onPressed: state.isLoading
                              ? null
                              : () {
                                  if (state.mode == ScannerMode.entry) {
                                    context.read<ScannerBloc>().add(
                                      CheckoutRequested(warehouseId: warehouseId),
                                    );
                                  } else {
                                    Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (_) => PaymentConfirmationScreen(warehouseId: warehouseId),
                                      ),
                                    );
                                  }
                                },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: state.mode == ScannerMode.entry ? InternoColors.success : InternoColors.cyan,
                            foregroundColor: Colors.black,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                          ),
                          child: state.isLoading
                              ? const CircularProgressIndicator(color: Colors.black)
                              : Text(
                                  state.mode == ScannerMode.entry ? 'REGISTRAR ENTRADA' : 'pos.process_payment'.tr().toUpperCase(),
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                    letterSpacing: 1.2,
                                  ),
                                ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildRow(String label, String value, {bool isTotal = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: TextStyle(
            color: isTotal ? Colors.white : Colors.white60,
            fontSize: isTotal ? 18 : 14,
            fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            color: isTotal ? InternoColors.cyan : Colors.white,
            fontSize: isTotal ? 24 : 14,
            fontWeight: isTotal ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }
}
