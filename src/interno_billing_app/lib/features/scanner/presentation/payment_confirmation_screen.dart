import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/core/enums/payment_method.dart';
import 'package:interno_billing_app/core/enums/app_reference.dart';
import 'package:easy_localization/easy_localization.dart';

class PaymentConfirmationScreen extends StatefulWidget {
  final String warehouseId;

  const PaymentConfirmationScreen({Key? key, required this.warehouseId}) : super(key: key);

  @override
  _PaymentConfirmationScreenState createState() => _PaymentConfirmationScreenState();
}

class _PaymentConfirmationScreenState extends State<PaymentConfirmationScreen> {
  PaymentMethod _selectedPayment = PaymentMethod.cash;
  final TextEditingController _referenceController = TextEditingController();

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

  void _simulatePrintTicket(String saleId) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        backgroundColor: Colors.grey[900],
        title: const Text('Imprimiendo Ticket...', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: InternoColors.cyan),
            const SizedBox(height: 16),
            const Text('Simulando conexión con impresora térmica...', style: TextStyle(color: Colors.white70)),
          ],
        ),
      ),
    );

    Future.delayed(const Duration(seconds: 2), () {
      if (!mounted) return;
      Navigator.of(context).pop();
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Venta $saleId completada y ticket impreso exitosamente.'),
          backgroundColor: InternoColors.success,
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<ScannerBloc, ScannerState>(
      listener: (context, state) {
        if (state.successMessage != null && state.items.isEmpty) {
          _simulatePrintTicket('POS-EXITOSO');
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
            title: const Text('Confirmar Venta'),
            centerTitle: true,
          ),
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Total
                Center(
                  child: Column(
                    children: [
                      const Text('Total a Pagar', style: TextStyle(color: Colors.white60, fontSize: 16)),
                      const SizedBox(height: 8),
                      Text(
                        '\$${state.grandTotal.toStringAsFixed(2)}',
                        style: const TextStyle(
                          color: InternoColors.cyan,
                          fontSize: 36,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 32),

                // Payment Method selector
                const Text(
                  'Método de Pago',
                  style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
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
                                ? InternoColors.cyan.withValues(alpha: 0.2)
                                : Colors.grey[900],
                            border: Border.all(
                              color: isSelected ? InternoColors.cyan : Colors.transparent,
                              width: 2,
                            ),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Center(
                            child: Text(
                              method.displayName,
                              style: TextStyle(
                                color: isSelected ? InternoColors.cyan : Colors.white,
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

                // Reference field — only for CARD or TRANSFER
                if (_showReferenceField) ...[
                  const Text(
                    'Datos Complementarios',
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
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
                      prefixIcon: Icon(_referenceIcon, color: InternoColors.cyan),
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
                      backgroundColor: InternoColors.cyan,
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
          ),
        );
      },
    );
  }

  @override
  void dispose() {
    _referenceController.dispose();
    super.dispose();
  }
}