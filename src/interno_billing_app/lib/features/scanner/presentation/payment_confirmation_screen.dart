import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/core/enums/payment_method.dart';
import 'package:interno_billing_app/core/enums/app_reference.dart';

class PaymentConfirmationScreen extends StatefulWidget {
  final String warehouseId;

  const PaymentConfirmationScreen({super.key, required this.warehouseId});

  @override
  _PaymentConfirmationScreenState createState() =>
      _PaymentConfirmationScreenState();
}

class _PaymentConfirmationScreenState
    extends State<PaymentConfirmationScreen> {
  PaymentMethod _selectedPayment = PaymentMethod.cash;
  final TextEditingController _referenceController = TextEditingController();
  final ScrollController _itemsScrollController = ScrollController();

  bool _saleCompleted = false;
  String? _completedFolio;

  bool get _showReferenceField =>
      _selectedPayment == PaymentMethod.card ||
      _selectedPayment == PaymentMethod.transfer;

  String get _referenceLabel => _selectedPayment == PaymentMethod.card
      ? 'No. de autorización de terminal'
      : 'Folio de transferencia';

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
            SnackBar(
              content: Text(state.error!),
              backgroundColor: Colors.red,
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      },
      builder: (context, state) {
        return Scaffold(
          backgroundColor: Colors.black,
          appBar: _saleCompleted
              ? null
              : AppBar(
                  backgroundColor: Colors.black,
                  title: const Text('Confirmar Venta'),
                  centerTitle: true,
                ),
          body: _saleCompleted
              ? _buildSuccessView(context)
              : _buildPaymentView(context, state),
        );
      },
    );
  }

  // ── Success view ────────────────────────────────────────────────────────────
  Widget _buildSuccessView(BuildContext context) {
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
                decoration: BoxDecoration(
                  color: InternoColors.success.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.check_circle_rounded,
                  color: InternoColors.success,
                  size: 60,
                ),
              ),
              const SizedBox(height: 24),
              const Text(
                'VENTA COMPLETADA',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w900,
                  fontSize: 22,
                  letterSpacing: 1.5,
                ),
              ),
              if (_completedFolio != null) ...[
                const SizedBox(height: 8),
                Text(
                  _completedFolio!,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 14,
                    letterSpacing: 1,
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Text(
                '${_selectedPayment.displayName} · ${_referenceController.text.isNotEmpty ? _referenceController.text : "—"}',
                style: const TextStyle(color: Colors.white24, fontSize: 12),
              ),
              const SizedBox(height: 48),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton(
                  onPressed: () => Navigator.of(context).pop(),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00E676),
                    foregroundColor: Colors.black,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: const Text(
                    'NUEVA VENTA',
                    style: TextStyle(
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
    );
  }

  // ── Payment form ────────────────────────────────────────────────────────────
  Widget _buildPaymentView(BuildContext context, ScannerState state) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Total breakdown
          Center(
            child: Column(
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _buildTotalRow('Subtotal', '\$${state.subtotal.toStringAsFixed(2)}', small: true),
                    const SizedBox(width: 24),
                    _buildTotalRow(
                      'IVA ${(state.taxRate * 100).toInt()}%',
                      '\$${state.totalTax.toStringAsFixed(2)}',
                      small: true,
                      highlight: true,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Text(
                  'Total a Pagar',
                  style: TextStyle(color: Colors.white60, fontSize: 16),
                ),
                const SizedBox(height: 4),
                Text(
                  '\$${state.grandTotal.toStringAsFixed(2)}',
                  style: const TextStyle(
                    color: InternoColors.error,
                    fontSize: 36,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 32),

          // Products
          const Text(
            'Productos a Confirmar',
            style: TextStyle(
                color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Container(
            constraints: const BoxConstraints(maxHeight: 180),
            decoration: BoxDecoration(
              color: const Color(0xFF161616),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.white10),
            ),
            child: state.items.isEmpty
                ? const Center(
                    child: Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text(
                        'No hay productos seleccionados',
                        style: TextStyle(color: Colors.white60),
                      ),
                    ),
                  )
                : Scrollbar(
                    thumbVisibility: true,
                    controller: _itemsScrollController,
                    child: ListView.separated(
                      controller: _itemsScrollController,
                      shrinkWrap: true,
                      padding: const EdgeInsets.symmetric(
                          vertical: 8, horizontal: 16),
                      itemCount: state.items.length,
                      separatorBuilder: (context, index) =>
                          const Divider(color: Colors.white10, height: 1),
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
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                        fontSize: 14,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '${item.quantity} ${item.product.uomName ?? "PZ"} x \$${item.product.price?.amount.toStringAsFixed(2) ?? "0.00"}',
                                      style: const TextStyle(
                                        color: Colors.white60,
                                        fontSize: 12,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(
                                '\$${item.lineTotal.toStringAsFixed(2)}',
                                style: const TextStyle(
                                  color: InternoColors.error,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
                  ),
          ),
          const SizedBox(height: 32),

          // Payment method selector
          const Text(
            'Método de Pago',
            style: TextStyle(
                color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
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
                      color: isSelected
                          ? InternoColors.error.withValues(alpha: 0.2)
                          : Colors.grey[900],
                      border: Border.all(
                        color:
                            isSelected ? InternoColors.error : Colors.transparent,
                        width: 2,
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Center(
                      child: Text(
                        method.displayName,
                        style: TextStyle(
                          color: isSelected ? InternoColors.error : Colors.white,
                          fontWeight: isSelected
                              ? FontWeight.bold
                              : FontWeight.normal,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 32),

          // Reference field (card / transfer only)
          if (_showReferenceField) ...[
            const Text(
              'Datos Complementarios',
              style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _referenceController,
              style: const TextStyle(color: Colors.white),
              keyboardType: _selectedPayment == PaymentMethod.card
                  ? TextInputType.number
                  : TextInputType.text,
              decoration: InputDecoration(
                labelText: _referenceLabel,
                labelStyle: const TextStyle(color: Colors.white60),
                filled: true,
                fillColor: Colors.grey[900],
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
                prefixIcon: Icon(_referenceIcon, color: InternoColors.error),
              ),
            ),
            const SizedBox(height: 48),
          ] else
            const SizedBox(height: 48),

          // Process button
          SizedBox(
            width: double.infinity,
            height: 60,
            child: ElevatedButton(
              onPressed: state.isLoading ? null : _processPayment,
              style: ElevatedButton.styleFrom(
                backgroundColor: InternoColors.error,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
              ),
              child: state.isLoading
                  ? const CircularProgressIndicator(color: Colors.black)
                  : const Text(
                      'PROCESAR Y EMITIR TICKET',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        letterSpacing: 1.2,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTotalRow(String label, String value, {bool small = false, bool highlight = false}) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            color: highlight ? InternoColors.error.withValues(alpha: 0.8) : Colors.white38,
            fontSize: 11,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            color: highlight ? InternoColors.error : Colors.white60,
            fontSize: small ? 14 : 16,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
