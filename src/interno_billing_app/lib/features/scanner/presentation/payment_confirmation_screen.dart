import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/core/enums/payment_method.dart';
import 'package:interno_billing_app/core/enums/app_reference.dart';

class PaymentConfirmationScreen extends StatefulWidget {
  final String warehouseId;

  const PaymentConfirmationScreen({super.key, required this.warehouseId});

  @override
  State<PaymentConfirmationScreen> createState() => _PaymentConfirmationScreenState();
}

class _PaymentConfirmationScreenState extends State<PaymentConfirmationScreen> {
  PaymentMethod _selectedPayment = PaymentMethod.cash;
  final TextEditingController _referenceController = TextEditingController();
  final ScrollController _itemsScrollController = ScrollController();

  bool _saleCompleted = false;
  String? _completedFolio;

  bool get _showReferenceField =>
      _selectedPayment == PaymentMethod.card || _selectedPayment == PaymentMethod.transfer;

  String get _referenceLabel => _selectedPayment == PaymentMethod.card
      ? 'payment.card_auth'.tr()
      : 'payment.transfer_folio'.tr();

  IconData get _referenceIcon => _selectedPayment == PaymentMethod.card
      ? Icons.credit_card_rounded
      : Icons.receipt_long_rounded;

  void _processPayment() {
    context.read<ScannerBloc>().add(
          CheckoutRequested(
            warehouseId: widget.warehouseId,
            comments: _showReferenceField ? _referenceController.text : null,
            paymentMethod: _selectedPayment.value,
            appReference: AppReference.mobileScanner.value,
          ),
        );
  }

  @override
  void dispose() {
    _referenceController.dispose();
    _itemsScrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<ScannerBloc, ScannerState>(
      listener: (context, state) {
        if (state.successMessage != null && state.items.isEmpty) {
          setState(() {
            _saleCompleted = true;
            _completedFolio = state.lastCreatedFolio;
          });
        }
        if (state.error != null) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(state.error!), backgroundColor: Colors.red, behavior: SnackBarBehavior.floating),
          );
        }
      },
      builder: (context, state) {
        final cs = Theme.of(context).colorScheme;
        final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;

        return Scaffold(
          backgroundColor: scaffoldBg,
          appBar: _saleCompleted
              ? null
              : AppBar(
                  backgroundColor: scaffoldBg,
                  title: Text('payment.title'.tr()),
                  centerTitle: true,
                ),
          body: _saleCompleted
              ? _buildSuccessView(context, cs)
              : _buildPaymentView(context, state, cs),
        );
      },
    );
  }

  Widget _buildSuccessView(BuildContext context, ColorScheme cs) {
    return SafeArea(
      child: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(color: InternoColors.success.withValues(alpha: 0.15), shape: BoxShape.circle),
                child: const Icon(Icons.check_circle_rounded, color: InternoColors.success, size: 60),
              ),
              const SizedBox(height: 24),
              Text(
                'payment.completed'.tr(),
                style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.w900, fontSize: 22, letterSpacing: 1.5),
              ),
              if (_completedFolio != null) ...[
                const SizedBox(height: 8),
                Text(
                  _completedFolio!,
                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 14, letterSpacing: 1),
                ),
              ],
              const SizedBox(height: 12),
              Text(
                '${_selectedPayment.displayName} · ${_referenceController.text.isNotEmpty ? _referenceController.text : "—"}',
                style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 12),
              ),
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: InternoColors.success,
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  child: Text(
                    'payment.new_sale'.tr(),
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPaymentView(BuildContext context, ScannerState state, ColorScheme cs) {
    final cardBg = Theme.of(context).cardColor;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildTotalRow('checkout.subtotal'.tr(), '\$${state.subtotal.toStringAsFixed(2)}', cs, small: true),
                    const SizedBox(width: 24),
                    _buildTotalRow(
                      'IVA ${(state.taxRate * 100).toInt()}%',
                      '\$${state.totalTax.toStringAsFixed(2)}',
                      cs,
                      small: true,
                      highlight: true,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Text('payment.total_to_pay'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6), fontSize: 16)),
                const SizedBox(height: 4),
                Text(
                  '\$${state.grandTotal.toStringAsFixed(2)}',
                  style: const TextStyle(color: InternoColors.error, fontSize: 36, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),
          Text('payment.products'.tr(), style: TextStyle(color: cs.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Container(
            constraints: const BoxConstraints(maxHeight: 180),
            decoration: BoxDecoration(
              color: cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: cs.onSurface.withValues(alpha: 0.08)),
            ),
            child: state.items.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(16.0),
                      child: Text('payment.no_products'.tr(), style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6))),
                    ),
                  )
                : Scrollbar(
                    thumbVisibility: true,
                    controller: _itemsScrollController,
                    child: ListView.separated(
                      controller: _itemsScrollController,
                      shrinkWrap: true,
                      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
                      itemCount: state.items.length,
                      separatorBuilder: (context, index) => Divider(color: cs.onSurface.withValues(alpha: 0.08), height: 1),
                      itemBuilder: (context, index) {
                        final item = state.items[index];
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 8.0),
                          child: Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.product.brandName != null
                                          ? '${item.product.name} (${item.product.brandName})'
                                          : item.product.name,
                                      style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold, fontSize: 14),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '${item.quantity} ${item.product.uomName ?? "PZ"} x \$${item.product.price?.amount.toStringAsFixed(2) ?? "0.00"}',
                                      style: TextStyle(color: cs.onSurface.withValues(alpha: 0.6), fontSize: 12),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '\$${item.lineTotal.toStringAsFixed(2)}',
                                style: const TextStyle(color: InternoColors.error, fontWeight: FontWeight.bold, fontSize: 14),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
          ),
          const SizedBox(height: 32),
          Text('payment.payment_method'.tr(), style: TextStyle(color: cs.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: PaymentMethod.values.map((method) {
              final isSelected = _selectedPayment == method;
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() {
                    _selectedPayment = method;
                    _referenceController.clear();
                  }),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 4),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    decoration: BoxDecoration(
                      color: isSelected ? InternoColors.error.withValues(alpha: 0.2) : cardBg,
                      border: Border.all(color: isSelected ? InternoColors.error : Colors.transparent, width: 2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Center(
                      child: Text(
                        method.displayName,
                        style: TextStyle(
                          color: isSelected ? InternoColors.error : cs.onSurface,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 32),
          if (_showReferenceField) ...[
            Text('payment.complementary'.tr(), style: TextStyle(color: cs.onSurface, fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            TextField(
              controller: _referenceController,
              style: TextStyle(color: cs.onSurface),
              keyboardType: _selectedPayment == PaymentMethod.card ? TextInputType.number : TextInputType.text,
              decoration: InputDecoration(
                labelText: _referenceLabel,
                labelStyle: TextStyle(color: cs.onSurface.withValues(alpha: 0.6)),
                filled: true,
                fillColor: cardBg,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                prefixIcon: Icon(_referenceIcon, color: InternoColors.error),
              ),
            ),
            const SizedBox(height: 48),
          ] else
            const SizedBox(height: 48),
          SizedBox(
            width: double.infinity,
            height: 60,
            child: ElevatedButton(
              onPressed: state.isLoading ? null : _processPayment,
              style: ElevatedButton.styleFrom(
                backgroundColor: InternoColors.error,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: state.isLoading
                  ? const CircularProgressIndicator(color: Colors.black)
                  : Text(
                      'payment.process'.tr(),
                      style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTotalRow(String label, String value, ColorScheme cs, {bool small = false, bool highlight = false}) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            color: highlight ? InternoColors.error.withValues(alpha: 0.8) : cs.onSurface.withValues(alpha: 0.38),
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            color: highlight ? InternoColors.error : cs.onSurface.withValues(alpha: 0.6),
            fontSize: small ? 14 : 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
