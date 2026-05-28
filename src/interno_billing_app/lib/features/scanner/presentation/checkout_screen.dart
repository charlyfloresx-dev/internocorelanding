import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';
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
        final cs = Theme.of(context).colorScheme;
        final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
        final isEntry = state.mode == ScannerMode.entry;
        final accentColor = isEntry ? InternoColors.success : InternoColors.error;

        return Scaffold(
          backgroundColor: scaffoldBg,
          appBar: AppBar(
            backgroundColor: scaffoldBg,
            elevation: 0,
            title: Text(
              isEntry ? 'checkout.receive'.tr() : 'checkout.confirm_sale'.tr(),
              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, letterSpacing: 1),
            ),
            centerTitle: true,
          ),
          body: Column(
            children: [
              _PartnerSelector(isEntry: isEntry, accentColor: accentColor, state: state),
              Expanded(
                child: state.items.isEmpty
                    ? Center(
                        child: Text(
                          'checkout.no_products'.tr(),
                          style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 13),
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
                              context.read<ScannerBloc>().add(UpdateQuantity(item.product.id, item.quantity + 1));
                            },
                            onDecrement: () {
                              HapticFeedback.selectionClick();
                              if (item.quantity > 1) {
                                context.read<ScannerBloc>().add(UpdateQuantity(item.product.id, item.quantity - 1));
                              } else {
                                context.read<ScannerBloc>().add(RemoveItem(item.product.id));
                              }
                            },
                          );
                        },
                      ),
              ),
              _Footer(state: state, isEntry: isEntry, accentColor: accentColor, warehouseId: warehouseId),
            ],
          ),
        );
      },
    );
  }
}

class _PartnerSelector extends StatelessWidget {
  final bool isEntry;
  final Color accentColor;
  final ScannerState state;

  const _PartnerSelector({required this.isEntry, required this.accentColor, required this.state});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final cardBg = Theme.of(context).cardColor;
    final hasPartner = state.selectedPartner != null;
    final label = isEntry ? 'checkout.provider'.tr() : 'checkout.client'.tr();

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
          color: cardBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: hasPartner ? accentColor.withValues(alpha: 0.4) : cs.onSurface.withValues(alpha: 0.08),
          ),
        ),
        child: Row(
          children: [
            Icon(
              hasPartner ? Icons.business_rounded : Icons.add_circle_outline_rounded,
              size: 16,
              color: hasPartner ? accentColor : cs.onSurface.withValues(alpha: 0.38),
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
                          style: TextStyle(color: cs.onSurface, fontSize: 13, fontWeight: FontWeight.w600),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    )
                  : Text(
                      '${'checkout.select'.tr()} $label',
                      style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 13),
                    ),
            ),
            if (hasPartner)
              GestureDetector(
                onTap: () => context.read<ScannerBloc>().add(SelectPartner(null)),
                child: Padding(
                  padding: const EdgeInsets.only(left: 8),
                  child: Icon(Icons.close_rounded, size: 16, color: cs.onSurface.withValues(alpha: 0.24)),
                ),
              )
            else
              Icon(Icons.chevron_right_rounded, size: 16, color: cs.onSurface.withValues(alpha: 0.24)),
          ],
        ),
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  final dynamic item;
  final Color accentColor;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;

  const _ItemRow({required this.item, required this.accentColor, required this.onIncrement, required this.onDecrement});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final cardBg = Theme.of(context).cardColor;
    final brandSuffix = item.product.brandName != null ? ' · ${item.product.brandName}' : '';
    final uom = item.product.uomName ?? 'PZ';
    final price = item.product.price?.amount?.toStringAsFixed(2) ?? '0.00';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: cs.onSurface.withValues(alpha: 0.05)),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${item.product.name}$brandSuffix',
                  style: TextStyle(color: cs.onSurface, fontSize: 13, fontWeight: FontWeight.w600),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text('\$$price / $uom', style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 11)),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Row(
            children: [
              _QtyButton(
                icon: item.quantity == 1 ? Icons.delete_outline_rounded : Icons.remove_rounded,
                color: item.quantity == 1 ? Colors.red.withValues(alpha: 0.7) : cs.onSurface.withValues(alpha: 0.38),
                onTap: onDecrement,
              ),
              Container(
                width: 36,
                alignment: Alignment.center,
                child: Text('${item.quantity}', style: TextStyle(color: cs.onSurface, fontSize: 15, fontWeight: FontWeight.bold)),
              ),
              _QtyButton(icon: Icons.add_rounded, color: accentColor, onTap: onIncrement),
            ],
          ),
          const SizedBox(width: 12),
          Text(
            '\$${item.lineTotal.toStringAsFixed(2)}',
            style: TextStyle(color: accentColor, fontSize: 13, fontWeight: FontWeight.bold),
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
        decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(7)),
        child: Icon(icon, size: 15, color: color),
      ),
    );
  }
}

class _Footer extends StatelessWidget {
  final ScannerState state;
  final bool isEntry;
  final Color accentColor;
  final String warehouseId;

  const _Footer({required this.state, required this.isEntry, required this.accentColor, required this.warehouseId});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
      decoration: BoxDecoration(
        color: scaffoldBg,
        border: Border(top: BorderSide(color: cs.onSurface.withValues(alpha: 0.08))),
      ),
      child: SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _TotalLabel('checkout.subtotal'.tr(), '\$${state.subtotal.toStringAsFixed(2)}'),
                _TotalLabel(
                  'IVA ${(state.taxRate * 100).toInt()}%',
                  '\$${state.totalTax.toStringAsFixed(2)}',
                  highlight: true,
                  accentColor: accentColor,
                ),
                _TotalLabel(
                  'checkout.total'.tr(),
                  '\$${state.grandTotal.toStringAsFixed(2)}',
                  isTotal: true,
                  accentColor: accentColor,
                ),
              ],
            ),
            const SizedBox(height: 14),
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton(
                onPressed: state.isLoading || state.items.isEmpty
                    ? null
                    : () {
                        if (isEntry) {
                          context.read<ScannerBloc>().add(CheckoutRequested(warehouseId: warehouseId));
                        } else {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (_) => PaymentConfirmationScreen(warehouseId: warehouseId)),
                          );
                        }
                      },
                style: ElevatedButton.styleFrom(
                  backgroundColor: accentColor,
                  foregroundColor: Colors.black,
                  disabledBackgroundColor: cs.onSurface.withValues(alpha: 0.12),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: state.isLoading
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
                    : Text(
                        isEntry ? 'checkout.register_entry'.tr() : 'checkout.process_sale'.tr(),
                        style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14, letterSpacing: 1.2),
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

  const _TotalLabel(this.label, this.value, {this.isTotal = false, this.highlight = false, this.accentColor});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        Text(
          label,
          style: TextStyle(
            color: highlight
                ? (accentColor ?? cs.onSurface).withValues(alpha: 0.6)
                : cs.onSurface.withValues(alpha: 0.38),
            fontSize: 9,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.8,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            color: isTotal || highlight ? (accentColor ?? cs.onSurface) : cs.onSurface.withValues(alpha: 0.6),
            fontSize: isTotal ? 18 : 13,
            fontWeight: isTotal ? FontWeight.w900 : FontWeight.w600,
          ),
        ),
      ],
    );
  }
}
