import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/scanner/presentation/payment_confirmation_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/widgets/partner_search_modal.dart';

class CheckoutScreen extends StatelessWidget {
  const CheckoutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final prefs = sl<SharedPreferences>();
    final warehouseId = prefs.getString('warehouse_id') ?? 'MAIN_WH';

    return BlocConsumer<ScannerBloc, ScannerState>(
      listener: (context, state) {
        if (state.successMessage != null && state.items.isEmpty) {
          if (ModalRoute.of(context)?.isCurrent == true) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text(state.successMessage!),
              backgroundColor: InternoColors.success,
              behavior: SnackBarBehavior.floating,
              duration: const Duration(seconds: 2),
            ));
            Future.delayed(const Duration(milliseconds: 600), () {
              if (context.mounted) Navigator.of(context).pop();
            });
          }
        }
        if (state.error != null) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(state.error!),
            backgroundColor: Colors.red,
            behavior: SnackBarBehavior.floating,
          ));
        }
      },
      builder: (context, state) {
        final isEntry = state.mode == ScannerMode.entry;
        final accentColor = isEntry ? InternoColors.success : InternoColors.error;

        return Scaffold(
          backgroundColor: Colors.black,
          appBar: AppBar(
            backgroundColor: Colors.black,
            elevation: 0,
            title: Text(
              isEntry ? 'RECIBIR MERCANCIA' : 'CONFIRMAR VENTA',
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, letterSpacing: 1),
            ),
            centerTitle: true,
          ),
          body: Column(
            children: [
              // ── Partner selector ─────────────────────────────────────────────
              _PartnerSelector(isEntry: isEntry, accentColor: accentColor, state: state),

              // ── Items list ───────────────────────────────────────────────────
              Expanded(
                child: state.items.isEmpty
                    ? Center(
                        child: Text(
                          'Sin productos',
                          style: TextStyle(color: Colors.white24, fontSize: 13),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        itemCount: state.items.length,
                        itemBuilder: (context, index) {
                          final item = state.items[index];
                          return _ItemRow(
                            item: item,
                            accentColor: accentColor,
                            onIncrement: () {
                              HapticFeedback.selectionClick();
                              context.read<ScannerBloc>().add(
                                UpdateQuantity(item.product.id, item.quantity + 1),
                              );
                            },
                            onDecrement: () {
                              HapticFeedback.selectionClick();
                              if (item.quantity > 1) {
                                context.read<ScannerBloc>().add(
                                  UpdateQuantity(item.product.id, item.quantity - 1),
                                );
                              } else {
                                context.read<ScannerBloc>().add(
                                  RemoveItem(item.product.id),
                                );
                              }
                            },
                          );
                        },
                      ),
              ),

              // ── Totals + CTA ─────────────────────────────────────────────────
              _Footer(
                state: state,
                isEntry: isEntry,
                accentColor: accentColor,
                warehouseId: warehouseId,
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── Partner selector row ──────────────────────────────────────────────────────
class _PartnerSelector extends StatelessWidget {
  final bool isEntry;
  final Color accentColor;
  final ScannerState state;

  const _PartnerSelector({
    required this.isEntry,
    required this.accentColor,
    required this.state,
  });

  @override
  Widget build(BuildContext context) {
    final hasPartner = state.selectedPartner != null;
    final label = isEntry ? 'PROVEEDOR' : 'CLIENTE';

    return GestureDetector(
      onTap: () => showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        backgroundColor: Colors.transparent,
        builder: (_) => BlocProvider.value(
          value: context.read<ScannerBloc>(),
          child: const PartnerSearchModal(),
        ),
      ),
      child: Container(
        margin: const EdgeInsets.fromLTRB(12, 0, 12, 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFF111111),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: hasPartner ? accentColor.withValues(alpha: 0.4) : Colors.white12,
          ),
        ),
        child: Row(
          children: [
            Icon(
              hasPartner ? Icons.business_rounded : Icons.add_circle_outline_rounded,
              size: 16,
              color: hasPartner ? accentColor : Colors.white38,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: hasPartner
                  ? Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          label,
                          style: TextStyle(
                            color: accentColor.withValues(alpha: 0.7),
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.2,
                          ),
                        ),
                        const SizedBox(height: 1),
                        Text(
                          state.selectedPartner!.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    )
                  : Text(
                      'Seleccionar $label',
                      style: const TextStyle(color: Colors.white38, fontSize: 13),
                    ),
            ),
            if (hasPartner)
              GestureDetector(
                onTap: () => context.read<ScannerBloc>().add(SelectPartner(null)),
                child: const Padding(
                  padding: EdgeInsets.only(left: 8),
                  child: Icon(Icons.close_rounded, size: 16, color: Colors.white24),
                ),
              )
            else
              const Icon(Icons.chevron_right_rounded, size: 16, color: Colors.white24),
          ],
        ),
      ),
    );
  }
}

// ── Item row ──────────────────────────────────────────────────────────────────
class _ItemRow extends StatelessWidget {
  final dynamic item;
  final Color accentColor;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;

  const _ItemRow({
    required this.item,
    required this.accentColor,
    required this.onIncrement,
    required this.onDecrement,
  });

  @override
  Widget build(BuildContext context) {
    final brandSuffix = item.product.brandName != null ? ' · ${item.product.brandName}' : '';
    final uom = item.product.uomName ?? 'PZ';
    final price = item.product.price?.amount?.toStringAsFixed(2) ?? '0.00';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0E0E0E),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
      ),
      child: Row(
        children: [
          // Product info
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${item.product.name}$brandSuffix',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  '\$$price / $uom',
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          // Quantity controls
          Row(
            children: [
              _QtyButton(
                icon: item.quantity == 1 ? Icons.delete_outline_rounded : Icons.remove_rounded,
                color: item.quantity == 1 ? Colors.red.withValues(alpha: 0.7) : Colors.white38,
                onTap: onDecrement,
              ),
              Container(
                width: 36,
                alignment: Alignment.center,
                child: Text(
                  '${item.quantity}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              _QtyButton(
                icon: Icons.add_rounded,
                color: accentColor,
                onTap: onIncrement,
              ),
            ],
          ),
          const SizedBox(width: 12),
          // Line total
          Text(
            '\$${item.lineTotal.toStringAsFixed(2)}',
            style: TextStyle(
              color: accentColor,
              fontSize: 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _QtyButton extends StatelessWidget {
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _QtyButton({required this.icon, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 28,
        height: 28,
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(7),
        ),
        child: Icon(icon, size: 15, color: color),
      ),
    );
  }
}

// ── Footer with totals + CTA ──────────────────────────────────────────────────
class _Footer extends StatelessWidget {
  final ScannerState state;
  final bool isEntry;
  final Color accentColor;
  final String warehouseId;

  const _Footer({
    required this.state,
    required this.isEntry,
    required this.accentColor,
    required this.warehouseId,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      decoration: const BoxDecoration(
        color: Color(0xFF0A0A0A),
        border: Border(top: BorderSide(color: Colors.white10)),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Totals row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _TotalLabel('Subtotal', '\$${state.subtotal.toStringAsFixed(2)}'),
                _TotalLabel(
                  'IVA ${(state.taxRate * 100).toInt()}%',
                  '\$${state.totalTax.toStringAsFixed(2)}',
                  highlight: true,
                  accentColor: accentColor,
                ),
                _TotalLabel(
                  'TOTAL',
                  '\$${state.grandTotal.toStringAsFixed(2)}',
                  isTotal: true,
                  accentColor: accentColor,
                ),
              ],
            ),
            const SizedBox(height: 14),
            // CTA button
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: state.isLoading || state.items.isEmpty
                    ? null
                    : () {
                        if (isEntry) {
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
                  backgroundColor: accentColor,
                  foregroundColor: Colors.black,
                  disabledBackgroundColor: Colors.white12,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: state.isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2),
                      )
                    : Text(
                        isEntry ? 'REGISTRAR ENTRADA' : 'PROCESAR VENTA',
                        style: const TextStyle(
                          fontWeight: FontWeight.w800,
                          fontSize: 14,
                          letterSpacing: 1.2,
                        ),
                      ),
              ),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}

class _TotalLabel extends StatelessWidget {
  final String label;
  final String value;
  final bool isTotal;
  final bool highlight;
  final Color? accentColor;

  const _TotalLabel(
    this.label,
    this.value, {
    this.isTotal = false,
    this.highlight = false,
    this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          label,
          style: TextStyle(
            color: highlight
                ? (accentColor ?? Colors.white).withValues(alpha: 0.6)
                : Colors.white38,
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            color: isTotal || highlight ? (accentColor ?? Colors.white) : Colors.white60,
            fontSize: isTotal ? 18 : 13,
            fontWeight: isTotal ? FontWeight.w900 : FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
