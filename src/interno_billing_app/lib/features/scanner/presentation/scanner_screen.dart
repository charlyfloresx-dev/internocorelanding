import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:intl/intl.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/scanner/presentation/checkout_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/widgets/cart_item_tile.dart';
import 'package:interno_billing_app/features/scanner/presentation/widgets/partner_search_modal.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';

class ScannerScreen extends StatefulWidget {
  final bool isTabMode;
  const ScannerScreen({super.key, this.isTabMode = false});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController controller = MobileScannerController();
  final TextEditingController _manualController = TextEditingController();

  final FocusNode _keyboardFocusNode = FocusNode();
  final StringBuffer _keyboardBuffer = StringBuffer();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _keyboardFocusNode.requestFocus();
    });
  }

  @override
  void dispose() {
    _keyboardFocusNode.dispose();
    controller.dispose();
    _manualController.dispose();
    super.dispose();
  }

  KeyEventResult _handleKeyEvent(FocusNode node, KeyEvent event) {
    if (event is KeyDownEvent) {
      final key = event.logicalKey;
      
      if (key == LogicalKeyboardKey.enter || key == LogicalKeyboardKey.numpadEnter) {
        final code = _keyboardBuffer.toString().trim();
        if (code.isNotEmpty) {
          context.read<ScannerBloc>().add(BarcodeScanned(code));
          _keyboardBuffer.clear();
        }
        return KeyEventResult.handled;
      }
      
      final char = event.character;
      if (char != null && char.isNotEmpty) {
        _keyboardBuffer.write(char);
        return KeyEventResult.handled;
      } else {
        final label = event.logicalKey.keyLabel;
        if (label.length == 1) {
          _keyboardBuffer.write(label);
          return KeyEventResult.handled;
        }
      }
    }
    return KeyEventResult.ignored;
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        if (!_keyboardFocusNode.hasFocus) {
          _keyboardFocusNode.requestFocus();
        }
      },
      child: Focus(
        focusNode: _keyboardFocusNode,
        autofocus: true,
        onKeyEvent: _handleKeyEvent,
        child: BlocConsumer<ScannerBloc, ScannerState>(
          listener: (context, state) {
            if (state.successMessage != null) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text(state.successMessage!),
                  backgroundColor: InternoColors.success,
                  behavior: SnackBarBehavior.floating,
                ),
              );
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
            
            if (state.detectedProduct != null) {
              _showProductConfirmation(context, state.detectedProduct!, state.mode);
            }
          },
          builder: (context, state) {
            return Scaffold(
              backgroundColor: Colors.black,
              body: Stack(
                children: [
                  // ── Scanner Layer ────────────────────────────────────────────────
                  MobileScanner(
                    controller: controller,
                    onDetect: (capture) {
                      final List<Barcode> barcodes = capture.barcodes;
                      for (final barcode in barcodes) {
                        if (barcode.rawValue != null) {
                          context.read<ScannerBloc>().add(BarcodeScanned(barcode.rawValue!));
                        }
                      }
                    },
                  ),
    
                  // ── Overlay UI ──────────────────────────────────────────────────
                  _buildDarkOverlay(),
                  _buildFloatingTopBar(state),
                  
                  // ── Bottom List Overlay ──────────────────────────────────────────
                  Positioned(
                    bottom: 0,
                    left: 0,
                    right: 0,
                    child: _buildBottomPanel(state),
                  ),
                  
                  if (state.isLoading)
                    const Center(child: CircularProgressIndicator(color: InternoColors.cyan)),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildDarkOverlay() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.4),
      ),
    );
  }

  Widget _buildFloatingTopBar(ScannerState state) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            widget.isTabMode
                ? const SizedBox(width: 48, height: 48)
                : _UberCircleIcon(
                    icon: Icons.close,
                    onTap: () => Navigator.pop(context),
                  ),
            
            // ── Mode Toggle ─────────────────────────────────────────────────
            Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.8),
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: Colors.white12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _ModeButton(
                    label: 'VENTA',
                    isActive: state.mode == ScannerMode.sale,
                    activeColor: InternoColors.error,
                    onTap: () => context.read<ScannerBloc>().add(ModeSelected(ScannerMode.sale)),
                  ),
                  _ModeButton(
                    label: 'ENTRADA',
                    isActive: state.mode == ScannerMode.entry,
                    activeColor: InternoColors.success,
                    onTap: () => context.read<ScannerBloc>().add(ModeSelected(ScannerMode.entry)),
                  ),
                ],
              ),
            ),

            _UberCircleIcon(
              icon: controller.torchEnabled ? Icons.flash_on : Icons.flash_off,
              onTap: () => controller.toggleTorch(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildBottomPanel(ScannerState state) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.45,
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        children: [
          _buildUberHeaderBar(state),
          const Divider(height: 1, color: Colors.white10),
          _buildPartnerChip(state),
          Expanded(
            child: state.items.isEmpty 
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: state.items.length,
                  itemBuilder: (context, index) => CartItemTile(item: state.items[index]),
                ),
          ),
          _buildCheckoutAction(state),
        ],
      ),
    );
  }

  Widget _buildUberHeaderBar(ScannerState state) {
    return Container(
      height: 70,
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'ESCANEANDO: ${state.items.length} PRODUCTOS (${state.totalItems} UNIDADES)',
                style: TextStyle(
                  fontFamily: 'Inter',
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  color: state.items.isEmpty
                      ? Colors.white54
                      : (state.mode == ScannerMode.sale ? InternoColors.error : InternoColors.success),
                  letterSpacing: 1
                ),
              ),
            ],
          ),
          _CircleIconButton(icon: Icons.keyboard, onPressed: _showManualInput),
        ],
      ),
    );
  }

  Widget _buildPartnerChip(ScannerState state) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: InkWell(
        onTap: () => _showPartnerSearch(),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: state.selectedPartner != null
                  ? (state.mode == ScannerMode.sale ? InternoColors.error : InternoColors.success).withValues(alpha: 0.1)
                  : Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: state.selectedPartner != null
                  ? (state.mode == ScannerMode.sale ? InternoColors.error : InternoColors.success).withValues(alpha: 0.3)
                  : Colors.white10,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.person_outline,
                size: 16,
                color: state.selectedPartner != null
                    ? (state.mode == ScannerMode.sale ? InternoColors.error : InternoColors.success)
                    : Colors.white54,
              ),
              const SizedBox(width: 8),
              Text(
                state.selectedPartner?.name ?? (state.mode == ScannerMode.entry ? 'SELECCIONAR PROVEEDOR' : 'SELECCIONAR CLIENTE'),
                style: TextStyle(
                  color: state.selectedPartner != null ? Colors.white : Colors.white54,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
              if (state.selectedPartner != null) ...[
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () => context.read<ScannerBloc>().add(SelectPartner(null)),
                  child: const Icon(Icons.close, size: 14, color: Colors.white38),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.qr_code_scanner_rounded, size: 48, color: Colors.white10),
          const SizedBox(height: 16),
          const Text('ESCANEÉ UN CÓDIGO PARA COMENZAR', style: TextStyle(color: Colors.white24, fontSize: 12, fontWeight: FontWeight.w800, letterSpacing: 1)),
        ],
      ),
    );
  }

  Widget _buildCheckoutAction(ScannerState state) {
    if (state.items.isEmpty) return const SizedBox(height: 20);
    
    final formatter = NumberFormat.currency(symbol: r'$', decimalDigits: 2);
    final totalText = state.mode == ScannerMode.entry 
        ? 'DESLIZAR PARA ENTRADA' 
        : '>> DESLIZAR PARA COBRAR (${formatter.format(state.grandTotal)})';

    return Padding(
      padding: const EdgeInsets.all(20),
      child: _SlideToConfirm(
        text: totalText,
        completeColor: state.mode == ScannerMode.sale ? InternoColors.error : InternoColors.success,
        onConfirm: () {
          Future.delayed(const Duration(milliseconds: 300), () {
            Navigator.push(context, MaterialPageRoute(builder: (_) => const CheckoutScreen()));
          });
        },
      ),
    );
  }

  void _showManualInput() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        title: const Text('Entrada Manual', style: TextStyle(color: Colors.white)),
        content: TextField(
          controller: _manualController,
          style: const TextStyle(color: Colors.white),
          decoration: const InputDecoration(
            hintText: 'Código SKU / Barcode',
            hintStyle: TextStyle(color: Colors.white38),
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              _keyboardFocusNode.requestFocus();
            },
            child: const Text('CANCELAR'),
          ),
          TextButton(
            onPressed: () {
              if (_manualController.text.isNotEmpty) {
                context.read<ScannerBloc>().add(BarcodeScanned(_manualController.text));
                _manualController.clear();
                Navigator.pop(context);
                _keyboardFocusNode.requestFocus();
              }
            },
            child: const Text('BUSCAR'),
          ),
        ],
      ),
    );
  }

  void _showPartnerSearch() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const PartnerSearchModal(),
    ).then((_) {
      _keyboardFocusNode.requestFocus();
    });
  }

  void _showProductConfirmation(BuildContext context, CartItem item, ScannerMode mode) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isDismissible: false,
      builder: (_) => _ProductConfirmationSheet(
        item: item,
        accentColor: mode == ScannerMode.sale ? InternoColors.error : InternoColors.success,
      ),
    ).then((_) {
      _keyboardFocusNode.requestFocus();
    });
  }
}

class _UberCircleIcon extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _UberCircleIcon({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 48, height: 48,
        decoration: BoxDecoration(
          color: Colors.black.withOpacity(0.8),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white12),
        ),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  final String label;
  final bool isActive;
  final Color activeColor;
  final VoidCallback onTap;

  const _ModeButton({
    required this.label,
    required this.isActive,
    required this.activeColor,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? activeColor : Colors.transparent,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isActive ? Colors.black : Colors.white38,
            fontSize: 10,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
          ),
        ),
      ),
    );
  }
}

class _CircleIconButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;

  const _CircleIconButton({required this.icon, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.white.withOpacity(0.05),
        ),
        child: Icon(icon, color: Colors.white, size: 20),
      ),
      onPressed: onPressed,
    );
  }
}

class _ProductConfirmationSheet extends StatelessWidget {
  final CartItem item;
  final Color accentColor;

  const _ProductConfirmationSheet({required this.item, required this.accentColor});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Color(0xFF1A1A1A),
        borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white12, borderRadius: BorderRadius.circular(2))),
          const SizedBox(height: 24),
          const Icon(Icons.check_circle_outline, color: InternoColors.success, size: 48),
          const SizedBox(height: 16),
          Text(item.product.name, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          Text(item.product.sku, style: const TextStyle(color: Colors.white38, fontSize: 14)),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(
                child: TextButton(
                  onPressed: () {
                    context.read<ScannerBloc>().add(CancelDetection());
                    Navigator.pop(context);
                  },
                  child: const Text('DESCARTAR', style: TextStyle(color: Colors.white54)),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    context.read<ScannerBloc>().add(AddProductToCart(item));
                    Navigator.pop(context);
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: accentColor,
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text('AGREGAR', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _SlideToConfirm extends StatefulWidget {
  final String text;
  final VoidCallback onConfirm;
  final Color completeColor;

  const _SlideToConfirm({
    required this.text,
    required this.onConfirm,
    this.completeColor = InternoColors.success,
  });

  @override
  State<_SlideToConfirm> createState() => _SlideToConfirmState();
}

class _SlideToConfirmState extends State<_SlideToConfirm> {
  double _position = 0.0;
  bool _isCompleted = false;
  final double _height = 56.0;

  @override
  void didUpdateWidget(covariant _SlideToConfirm oldWidget) {
    super.didUpdateWidget(oldWidget);
    // If the text changes (e.g. total changes or cart is cleared), reset drag state.
    if (oldWidget.text != widget.text) {
      setState(() {
        _position = 0.0;
        _isCompleted = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final maxDrag = constraints.maxWidth - _height;
        return Container(
          height: _height,
          decoration: BoxDecoration(
            color: _isCompleted ? widget.completeColor : Colors.black,
            borderRadius: BorderRadius.circular(_height / 2),
            border: Border.all(color: _isCompleted ? widget.completeColor : Colors.white24),
          ),
          child: Stack(
            alignment: Alignment.centerLeft,
            children: [
              // 1. Fondo verde dinámico que sigue el arrastre
              Positioned(
                left: 0,
                top: 0,
                bottom: 0,
                width: _height + _position,
                child: Container(
                  decoration: BoxDecoration(
                    color: widget.completeColor,
                    borderRadius: BorderRadius.circular(_height / 2),
                  ),
                ),
              ),

              // 2. Texto de confirmación
              Center(
                child: Text(
                  widget.text,
                  style: TextStyle(
                    color: _isCompleted ? Colors.black : Colors.white,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 1,
                  ),
                ),
              ),

              // 3. Botón de arrastre (Handle)
              Positioned(
                left: _position,
                child: GestureDetector(
                  onPanUpdate: (details) {
                    if (_isCompleted) return;
                    setState(() {
                      _position += details.delta.dx;
                      if (_position < 0) _position = 0;
                      if (_position > maxDrag) _position = maxDrag;
                    });
                  },
                  onPanEnd: (details) {
                    if (_isCompleted) return;
                    if (_position > maxDrag * 0.85) {
                      setState(() {
                        _position = maxDrag;
                        _isCompleted = true;
                      });
                      widget.onConfirm();
                    } else {
                      setState(() {
                        _position = 0;
                      });
                    }
                  },
                  child: Container(
                    width: _height,
                    height: _height,
                    decoration: const BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.arrow_forward_ios,
                      color: _isCompleted ? widget.completeColor : Colors.black,
                      size: 20,
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

