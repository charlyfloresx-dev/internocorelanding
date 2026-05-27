import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/services/product_sync_service.dart';
import 'package:interno_billing_app/core/database/local_database.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/scanner/presentation/checkout_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/payment_confirmation_screen.dart';
import 'package:interno_billing_app/features/scanner/presentation/widgets/cart_item_tile.dart';
import 'package:interno_billing_app/features/scanner/presentation/widgets/partner_search_modal.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/domain/entities/product.dart';

class ScannerScreen extends StatefulWidget {
  final bool isTabMode;
  final ValueNotifier<bool>? isActiveNotifier;
  const ScannerScreen({super.key, this.isTabMode = false, this.isActiveNotifier});

  @override
  State<ScannerScreen> createState() => _ScannerScreenState();
}

class _ScannerScreenState extends State<ScannerScreen> {
  final MobileScannerController controller = MobileScannerController(autoStart: false);
  final TextEditingController _manualController = TextEditingController();
  final FocusNode _keyboardFocusNode = FocusNode();
  final StringBuffer _keyboardBuffer = StringBuffer();

  // Sale-mode state
  final DraggableScrollableController _sheetController = DraggableScrollableController();
  double _slideProgress = 0.0;
  bool _isSyncing = false;
  String _syncStatusText = 'Sin sincronizar';
  int _cachedProductCount = 0;
  List<Map<String, dynamic>> _productCatalog = [];
  bool _isProductModalShown = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _keyboardFocusNode.requestFocus();
      // Start camera only if active (or non-tab mode always starts)
      if (widget.isActiveNotifier == null || widget.isActiveNotifier!.value) {
        controller.start();
      }
    });
    widget.isActiveNotifier?.addListener(_onActiveChanged);
    _loadSyncStatus();
    _loadProductsFromDb();
    _autoSyncIfNeeded();
  }

  void _onActiveChanged() {
    if (!mounted) return;
    if (widget.isActiveNotifier!.value) {
      controller.start();
    } else {
      controller.stop();
    }
  }

  @override
  void dispose() {
    widget.isActiveNotifier?.removeListener(_onActiveChanged);
    _keyboardFocusNode.dispose();
    controller.dispose();
    _manualController.dispose();
    _sheetController.dispose();
    super.dispose();
  }

  // ── Hardware keyboard (entry mode) ──────────────────────────────────────
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

  // ── Sync (sale mode) ─────────────────────────────────────────────────────
  Future<void> _loadProductsFromDb() async {
    try {
      final localDb = sl<AppLocalDatabase>();
      final products = await localDb.getAllProducts();
      if (mounted) {
        setState(() {
          _productCatalog = products.map((p) => <String, dynamic>{
            'id': p.id,
            'name': p.name,
            'code': p.code ?? p.sku,
            'sku': p.sku,
            'price': p.price?.amount ?? 0.0,
            'currency': p.price?.currency ?? 'MXN',
          }).toList();
        });
      }
    } catch (e) {
      debugPrint('Error cargando catálogo: $e');
    }
  }

  Future<void> _loadSyncStatus() async {
    try {
      final syncService = sl<ProductSyncService>();
      final status = await syncService.getSyncStatus();
      if (mounted) {
        setState(() {
          _syncStatusText = status.displayText;
          _cachedProductCount = status.cachedProductCount;
        });
      }
    } catch (e) {
      debugPrint('Error loading sync status: $e');
    }
  }

  Future<void> _autoSyncIfNeeded() async {
    try {
      final syncService = sl<ProductSyncService>();
      final status = await syncService.getSyncStatus();
      if (status.isStale) await _triggerSync();
    } catch (e) {
      debugPrint('Auto-sync check error: $e');
    }
  }

  Future<void> _triggerSync() async {
    if (_isSyncing) return;
    setState(() => _isSyncing = true);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final syncService = sl<ProductSyncService>();
      final result = await syncService.fullSync(
        onProgress: (current, total) {
          if (mounted) setState(() => _syncStatusText = 'Descargando $current/$total...');
        },
      );
      await _loadSyncStatus();
      await _loadProductsFromDb();
      if (result >= 0) {
        messenger.showSnackBar(SnackBar(
          content: Text('✅ Catálogo sincronizado: $_cachedProductCount productos'),
          backgroundColor: const Color(0xFF1E3A27),
          duration: const Duration(seconds: 2),
        ));
      }
    } catch (e) {
      messenger.showSnackBar(SnackBar(
        content: Text('❌ Error de sincronización: $e'),
        backgroundColor: Colors.redAccent.shade700,
      ));
    } finally {
      if (mounted) setState(() => _isSyncing = false);
    }
  }

  void _toggleCartSheet() {
    if (_sheetController.isAttached) {
      final double currentSize = _sheetController.size;
      final double targetSize = currentSize < 0.2 ? 0.85 : 0.11;
      _sheetController.animateTo(
        targetSize,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutCubic,
      );
    }
  }

  void _animateSliderReset() {
    double start = _slideProgress;
    const steps = 15;
    int currentStep = 0;
    Timer.periodic(const Duration(milliseconds: 10), (timer) {
      currentStep++;
      if (currentStep >= steps) {
        if (mounted) setState(() => _slideProgress = 0.0);
        timer.cancel();
      } else {
        if (mounted) setState(() => _slideProgress = start * (1.0 - currentStep / steps));
      }
    });
  }

  void _navigateToPayment(BuildContext context) {
    final prefs = sl<SharedPreferences>();
    final warehouseId = prefs.getString('warehouse_id') ?? '';
    final bloc = context.read<ScannerBloc>();
    Navigator.of(context).push(MaterialPageRoute(
      builder: (_) => BlocProvider.value(
        value: bloc,
        child: PaymentConfirmationScreen(warehouseId: warehouseId),
      ),
    ));
  }

  void _showProductDetectedSheet(BuildContext context, CartItem item) {
    if (_isProductModalShown) return;
    _isProductModalShown = true;
    final bloc = context.read<ScannerBloc>();
    final price = item.product.price?.amount ?? 0.0;
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF12141A),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(child: Container(width: 40, height: 5, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2.5)))),
            const SizedBox(height: 16),
            Text(item.product.name, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold), maxLines: 2, overflow: TextOverflow.ellipsis),
            const SizedBox(height: 4),
            Text(item.product.code ?? item.product.sku, style: const TextStyle(color: Colors.white38, fontSize: 12, letterSpacing: 0.5)),
            const SizedBox(height: 16),
            Text('\$${price.toStringAsFixed(2)}', style: const TextStyle(color: InternoColors.cyan, fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 24),
            Row(children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () { bloc.add(CancelDetection()); Navigator.pop(ctx); },
                  style: OutlinedButton.styleFrom(
                    side: const BorderSide(color: Colors.white24),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text('Cancelar', style: TextStyle(color: Colors.white54)),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                flex: 2,
                child: ElevatedButton(
                  onPressed: () { bloc.add(AddProductToCart(item)); Navigator.pop(ctx); },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF00E676),
                    foregroundColor: Colors.black,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Text('Agregar al Carrito', style: TextStyle(fontWeight: FontWeight.bold)),
                ),
              ),
            ]),
          ],
        ),
      ),
    ).whenComplete(() => _isProductModalShown = false);
  }


  void _showQuickCatalogDialog(BuildContext context, ScannerBloc bloc) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF12141A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text('Búsqueda Rápida', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            IconButton(
              icon: _isSyncing
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Color(0xFF00E676)))
                  : Icon(Icons.sync_rounded, color: _cachedProductCount > 0 ? const Color(0xFF00E676) : Colors.amber),
              onPressed: () { Navigator.pop(dialogContext); _triggerSync(); },
            ),
          ],
        ),
        content: SizedBox(
          width: double.maxFinite,
          child: _productCatalog.isEmpty
              ? Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_download_outlined, color: Colors.white24, size: 48),
                    const SizedBox(height: 16),
                    const Text('No hay productos en caché local.', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    const Text('Pulsa sincronización para descargar el catálogo.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white24, fontSize: 12)),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () { Navigator.pop(dialogContext); _triggerSync(); },
                      icon: const Icon(Icons.sync),
                      label: const Text('Sincronizar Ahora'),
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00E676)),
                    ),
                  ],
                )
              : ListView.builder(
                  shrinkWrap: true,
                  itemCount: _productCatalog.length,
                  itemBuilder: (_, index) {
                    final p = _productCatalog[index];
                    return ListTile(
                      contentPadding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                      title: Text(p['name'] as String, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                      subtitle: Text('${p['code']}  ·  \$${(p['price'] as double).toStringAsFixed(2)}', style: const TextStyle(color: Colors.white38)),
                      trailing: const Icon(Icons.add_circle, color: Color(0xFF00E676)),
                      onTap: () {
                        final product = Product(
                          id: p['id'] as String,
                          name: p['name'] as String,
                          sku: p['sku'] as String,
                          code: p['code'] as String,
                          price: Price(amount: p['price'] as double, currency: p['currency'] as String),
                        );
                        bloc.add(AddProductToCart(CartItem(product: product, taxRate: 0.16)));
                        Navigator.pop(dialogContext);
                      },
                    );
                  },
                ),
        ),
      ),
    );
  }

  // ── ROOT BUILD ───────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () { if (!_keyboardFocusNode.hasFocus) _keyboardFocusNode.requestFocus(); },
      child: Focus(
        focusNode: _keyboardFocusNode,
        autofocus: true,
        onKeyEvent: _handleKeyEvent,
        child: BlocConsumer<ScannerBloc, ScannerState>(
          listenWhen: (previous, current) =>
              previous.detectedProduct != current.detectedProduct ||
              previous.error != current.error ||
              previous.successMessage != current.successMessage,
          listener: (context, state) {
            if (state.successMessage != null) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(state.successMessage!),
                backgroundColor: InternoColors.success,
                behavior: SnackBarBehavior.floating,
              ));
            }
            if (state.error != null) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(state.error!),
                backgroundColor: Colors.red,
                behavior: SnackBarBehavior.floating,
              ));
            }
            if (state.detectedProduct != null) {
              if (state.mode == ScannerMode.sale) {
                _showProductDetectedSheet(context, state.detectedProduct!);
              } else {
                _showProductConfirmation(context, state.detectedProduct!, state.mode);
              }
            }
          },
          builder: (context, state) {
            return state.mode == ScannerMode.sale
                ? _buildSaleMode(context, state)
                : _buildEntryMode(context, state);
          },
        ),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // SALE MODE — Uber POS Design (frozen per uber_pos_layout.md)
  // ══════════════════════════════════════════════════════════════════════════
  Widget _buildSaleMode(BuildContext context, ScannerState state) {
    final double screenHeight = MediaQuery.of(context).size.height;
    final double screenWidth = MediaQuery.of(context).size.width;
    final double cutoutWidth = screenWidth * 0.75;
    const double cutoutHeight = 220.0;
    final double scannerTop = (screenHeight - cutoutHeight) / 2 - 100;
    final double laserTop = scannerTop + (cutoutHeight / 2);
    final Rect scanWindow = Rect.fromLTWH(
      (screenWidth - cutoutWidth) / 2,
      scannerTop,
      cutoutWidth,
      cutoutHeight,
    );

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // 1. Fullscreen camera
          Positioned.fill(
            child: MobileScanner(
              controller: controller,
              scanWindow: scanWindow,
              onDetect: (capture) {
                for (final barcode in capture.barcodes) {
                  if (barcode.rawValue != null) {
                    context.read<ScannerBloc>().add(BarcodeScanned(barcode.rawValue!));
                  }
                }
              },
            ),
          ),

          // 2. Dark overlay with cutout
          Positioned.fill(
            child: CustomPaint(
              painter: _ScannerOverlayPainter(
                cutoutWidth: cutoutWidth,
                cutoutHeight: cutoutHeight,
                topOffset: scannerTop,
              ),
            ),
          ),

          // 3. Red laser line
          Positioned(
            top: laserTop,
            left: screenWidth * 0.15,
            right: screenWidth * 0.15,
            child: Container(
              height: 3,
              decoration: BoxDecoration(
                color: Colors.redAccent,
                boxShadow: [BoxShadow(color: Colors.redAccent.withValues(alpha: 0.8), blurRadius: 10, spreadRadius: 2)],
              ),
            ),
          ),

          // 4. Top bar
          Positioned(
            top: 50, left: 20, right: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildCircularButton(
                  icon: Icons.close_rounded,
                  onTap: () {
                    if (widget.isTabMode) return;
                    Navigator.of(context).maybePop();
                  },
                ),
                GestureDetector(
                  onTap: () {},
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.85),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                      boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 10, offset: Offset(0, 4))],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Text('MX\$', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                        const SizedBox(width: 4),
                        Text(
                          state.grandTotal.toStringAsFixed(2),
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 22, letterSpacing: -0.5),
                        ),
                      ],
                    ),
                  ),
                ),
                _buildCircularButton(
                  icon: Icons.search_rounded,
                  onTap: () => _showQuickCatalogDialog(context, context.read<ScannerBloc>()),
                ),
              ],
            ),
          ),

          // 5. Draggable bottom sheet
          DraggableScrollableSheet(
            controller: _sheetController,
            initialChildSize: 0.11,
            minChildSize: 0.11,
            maxChildSize: 0.85,
            builder: (BuildContext ctx, ScrollController scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
                  boxShadow: [BoxShadow(color: Colors.black87, blurRadius: 20, spreadRadius: 5)],
                ),
                child: ListView(
                  controller: scrollController,
                  padding: EdgeInsets.zero,
                  children: [
                    const SizedBox(height: 10),
                    Center(child: Container(width: 40, height: 5, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2.5)))),
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.tune_rounded, color: Colors.white, size: 24),
                            onPressed: () => _showPartnerSearch(),
                            style: IconButton.styleFrom(backgroundColor: Colors.white.withValues(alpha: 0.04), padding: const EdgeInsets.all(12)),
                          ),
                          Column(
                            children: [
                              Text(
                                state.items.isEmpty ? 'Escaneando...' : '${state.totalItems} ${state.totalItems == 1 ? 'artículo' : 'artículos'}',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: -0.5),
                              ),
                              const SizedBox(height: 4),
                              Text('Cliente: ${state.selectedPartner?.name ?? 'Público General'}', style: const TextStyle(color: Colors.white54, fontSize: 12)),
                              GestureDetector(
                                onTap: _triggerSync,
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    if (_isSyncing)
                                      const SizedBox(width: 10, height: 10, child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF00E676)))
                                    else
                                      Icon(Icons.sync_rounded, size: 10, color: _cachedProductCount > 0 ? const Color(0xFF00E676) : Colors.amber),
                                    const SizedBox(width: 4),
                                    Text(
                                      '$_cachedProductCount SKUs · $_syncStatusText',
                                      style: TextStyle(color: _cachedProductCount > 0 ? Colors.white30 : Colors.amber.shade300, fontSize: 9),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                          IconButton(
                            icon: const Icon(Icons.list_rounded, color: Colors.white, size: 24),
                            onPressed: _toggleCartSheet,
                            style: IconButton.styleFrom(backgroundColor: Colors.white.withValues(alpha: 0.04), padding: const EdgeInsets.all(12)),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Divider(color: Colors.white10, height: 1),
                    if (state.items.isEmpty) ...[
                      const SizedBox(height: 40),
                      Center(
                        child: Column(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.02), shape: BoxShape.circle),
                              child: const Icon(Icons.receipt_long_outlined, color: Colors.white24, size: 48),
                            ),
                            const SizedBox(height: 16),
                            const Text('No hay productos agregados', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 6),
                            const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 40),
                              child: Text(
                                'Apunta la cámara a un código de barras o utiliza la lupa arriba para agregarlos.',
                                textAlign: TextAlign.center,
                                style: TextStyle(color: Colors.white10, fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ] else ...[
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        itemCount: state.items.length,
                        itemBuilder: (_, index) {
                          final item = state.items[index];
                          return Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(14),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.03),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: Colors.white.withValues(alpha: 0.04)),
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    item.product.code ?? item.product.sku,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15, letterSpacing: 0.5),
                                  ),
                                ),
                                SizedBox(
                                  width: 90,
                                  child: Text('\$${item.lineTotal.toStringAsFixed(2)}', textAlign: TextAlign.right, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
                                ),
                                const SizedBox(width: 16),
                                Row(
                                  children: [
                                    IconButton(
                                      icon: const Icon(Icons.remove_circle, color: Colors.white54, size: 30),
                                      onPressed: () {
                                        final newQty = item.quantity - 1;
                                        if (newQty <= 0) {
                                          context.read<ScannerBloc>().add(RemoveItem(item.product.id));
                                        } else {
                                          context.read<ScannerBloc>().add(UpdateQuantity(item.product.id, newQty));
                                        }
                                      },
                                      padding: EdgeInsets.zero,
                                      constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
                                    ),
                                    Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 10),
                                      child: Text('${item.quantity}', style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 18)),
                                    ),
                                    IconButton(
                                      icon: const Icon(Icons.add_circle, color: Colors.white, size: 30),
                                      onPressed: () => context.read<ScannerBloc>().add(UpdateQuantity(item.product.id, item.quantity + 1)),
                                      padding: EdgeInsets.zero,
                                      constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          );
                        },
                      ),
                      // Slide to confirm
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
                        child: LayoutBuilder(
                          builder: (_, constraints) {
                            final double sliderWidth = constraints.maxWidth;
                            const double handleSize = 56.0;
                            final double maxDragDistance = sliderWidth - handleSize;
                            return Container(
                              width: sliderWidth,
                              height: 56,
                              decoration: BoxDecoration(
                                color: Colors.white.withValues(alpha: 0.05),
                                borderRadius: BorderRadius.circular(28),
                                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                              ),
                              child: Stack(
                                children: [
                                  Positioned(
                                    left: 0, top: 0, bottom: 0,
                                    width: handleSize + (_slideProgress * maxDragDistance),
                                    child: Container(
                                      decoration: BoxDecoration(color: const Color(0xFF00E676), borderRadius: BorderRadius.circular(28)),
                                    ),
                                  ),
                                  Center(
                                    child: AnimatedOpacity(
                                      duration: const Duration(milliseconds: 100),
                                      opacity: (1.0 - _slideProgress).clamp(0.0, 1.0),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.center,
                                        children: [
                                          const Icon(Icons.keyboard_double_arrow_right_rounded, color: Colors.white, size: 20),
                                          const SizedBox(width: 8),
                                          Text(
                                            'DESLIZAR PARA COBRAR (\$${state.grandTotal.toStringAsFixed(2)})',
                                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 13, letterSpacing: 0.5),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                  Positioned(
                                    left: _slideProgress * maxDragDistance,
                                    top: 0, bottom: 0,
                                    child: GestureDetector(
                                      onHorizontalDragUpdate: (details) {
                                        setState(() {
                                          _slideProgress += details.primaryDelta! / maxDragDistance;
                                          _slideProgress = _slideProgress.clamp(0.0, 1.0);
                                        });
                                      },
                                      onHorizontalDragEnd: (details) {
                                        if (_slideProgress > 0.85) {
                                          setState(() => _slideProgress = 1.0);
                                          _navigateToPayment(context);
                                          Future.delayed(const Duration(milliseconds: 600), () {
                                            if (mounted) setState(() => _slideProgress = 0.0);
                                          });
                                        } else {
                                          _animateSliderReset();
                                        }
                                      },
                                      child: Container(
                                        width: handleSize,
                                        height: handleSize,
                                        decoration: const BoxDecoration(
                                          color: Colors.white,
                                          shape: BoxShape.circle,
                                          boxShadow: [BoxShadow(color: Colors.black26, blurRadius: 4, offset: Offset(2, 0))],
                                        ),
                                        child: Center(
                                          child: Icon(
                                            Icons.arrow_forward_rounded,
                                            color: _slideProgress > 0.85 ? const Color(0xFF00E676) : Colors.black,
                                            size: 24,
                                          ),
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildCircularButton({required IconData icon, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(30),
      child: Container(
        width: 54, height: 54,
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.85),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 8, offset: Offset(0, 3))],
        ),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
    );
  }

  // ══════════════════════════════════════════════════════════════════════════
  // ENTRY MODE — same DraggableScrollableSheet architecture as sale mode
  // Only differences: accent color (green), partner label, slider text
  // ══════════════════════════════════════════════════════════════════════════
  Widget _buildEntryMode(BuildContext context, ScannerState state) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // 1. Fullscreen camera
          Positioned.fill(
            child: MobileScanner(
              controller: controller,
              onDetect: (capture) {
                for (final barcode in capture.barcodes) {
                  if (barcode.rawValue != null) {
                    context.read<ScannerBloc>().add(BarcodeScanned(barcode.rawValue!));
                  }
                }
              },
            ),
          ),

          // 2. Dark overlay
          Positioned.fill(
            child: Container(color: Colors.black.withValues(alpha: 0.55)),
          ),

          // 3. Top bar — mode switcher + flash
          Positioned(
            top: 50, left: 20, right: 20,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                widget.isTabMode
                    ? const SizedBox(width: 54, height: 54)
                    : _buildCircularButton(
                        icon: Icons.close_rounded,
                        onTap: () => Navigator.of(context).maybePop(),
                      ),
                // VENTA / ENTRADA toggle pill
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.black.withValues(alpha: 0.85),
                    borderRadius: BorderRadius.circular(30),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                    boxShadow: const [BoxShadow(color: Colors.black54, blurRadius: 10, offset: Offset(0, 4))],
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      _ModeButton(
                        label: 'VENTA',
                        isActive: false,
                        activeColor: InternoColors.error,
                        onTap: () => context.read<ScannerBloc>().add(ModeSelected(ScannerMode.sale)),
                      ),
                      _ModeButton(
                        label: 'ENTRADA',
                        isActive: true,
                        activeColor: InternoColors.success,
                        onTap: () {},
                      ),
                    ],
                  ),
                ),
                _buildCircularButton(
                  icon: controller.torchEnabled ? Icons.flash_on : Icons.flash_off,
                  onTap: () => controller.toggleTorch(),
                ),
              ],
            ),
          ),

          // 4. Draggable bottom sheet — identical structure to sale mode
          DraggableScrollableSheet(
            controller: _sheetController,
            initialChildSize: 0.11,
            minChildSize: 0.11,
            maxChildSize: 0.85,
            builder: (BuildContext ctx, ScrollController scrollController) {
              return Container(
                decoration: const BoxDecoration(
                  color: Colors.black,
                  borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
                  boxShadow: [BoxShadow(color: Colors.black87, blurRadius: 20, spreadRadius: 5)],
                ),
                child: ListView(
                  controller: scrollController,
                  padding: EdgeInsets.zero,
                  children: [
                    const SizedBox(height: 10),
                    Center(child: Container(width: 40, height: 5, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(2.5)))),
                    const SizedBox(height: 16),
                    // Sheet header
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          // Partner selector (tune icon)
                          IconButton(
                            icon: const Icon(Icons.tune_rounded, color: Colors.white, size: 24),
                            onPressed: _showPartnerSearch,
                            style: IconButton.styleFrom(
                              backgroundColor: Colors.white.withValues(alpha: 0.04),
                              padding: const EdgeInsets.all(12),
                            ),
                          ),
                          // Center status
                          Column(
                            children: [
                              Text(
                                state.items.isEmpty
                                    ? 'Escaneando...'
                                    : '${state.totalItems} ${state.totalItems == 1 ? 'unidad' : 'unidades'}',
                                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 18, letterSpacing: -0.5),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Proveedor: ${state.selectedPartner?.name ?? 'Sin proveedor'}',
                                style: const TextStyle(color: Colors.white54, fontSize: 12),
                              ),
                            ],
                          ),
                          // List toggle
                          IconButton(
                            icon: const Icon(Icons.list_rounded, color: Colors.white, size: 24),
                            onPressed: _toggleCartSheet,
                            style: IconButton.styleFrom(
                              backgroundColor: Colors.white.withValues(alpha: 0.04),
                              padding: const EdgeInsets.all(12),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Divider(color: Colors.white10, height: 1),
                    // Items
                    if (state.items.isEmpty) ...[
                      const SizedBox(height: 40),
                      Center(
                        child: Column(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.02), shape: BoxShape.circle),
                              child: const Icon(Icons.qr_code_scanner_rounded, color: Colors.white24, size: 48),
                            ),
                            const SizedBox(height: 16),
                            const Text('No hay productos agregados', style: TextStyle(color: Colors.white38, fontWeight: FontWeight.bold)),
                            const SizedBox(height: 6),
                            TextButton.icon(
                              onPressed: _showManualInput,
                              icon: const Icon(Icons.keyboard_rounded, color: Colors.white24, size: 16),
                              label: const Text(
                                'Ingresar código manual',
                                style: TextStyle(color: Colors.white24, fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ] else ...[
                      ListView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                        itemCount: state.items.length,
                        itemBuilder: (_, index) => CartItemTile(item: state.items[index]),
                      ),
                      // Slide to confirm — green accent for entry
                      Padding(
                        padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
                        child: _SlideToConfirm(
                          text: 'DESLIZAR PARA ENTRADA',
                          completeColor: InternoColors.success,
                          onConfirm: () {
                            final nav = Navigator.of(context);
                            Future.delayed(const Duration(milliseconds: 300), () {
                              nav.push(MaterialPageRoute(builder: (_) => const CheckoutScreen()));
                            });
                          },
                        ),
                      ),
                    ],
                  ],
                ),
              );
            },
          ),

          // 5. Loading indicator
          if (state.isLoading)
            const Center(child: CircularProgressIndicator(color: InternoColors.success)),
        ],
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
          decoration: const InputDecoration(hintText: 'Código SKU / Barcode', hintStyle: TextStyle(color: Colors.white38)),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () { Navigator.pop(context); _keyboardFocusNode.requestFocus(); },
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
    final bloc = context.read<ScannerBloc>();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => BlocProvider.value(
        value: bloc,
        child: const PartnerSearchModal(),
      ),
    ).then((_) => _keyboardFocusNode.requestFocus());
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
    ).then((_) => _keyboardFocusNode.requestFocus());
  }
}

// ── SHARED WIDGETS ────────────────────────────────────────────────────────────


class _ModeButton extends StatelessWidget {
  final String label;
  final bool isActive;
  final Color activeColor;
  final VoidCallback onTap;
  const _ModeButton({required this.label, required this.isActive, required this.activeColor, required this.onTap});

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
        child: Text(label, style: TextStyle(color: isActive ? Colors.black : Colors.white38, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
      ),
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
      decoration: const BoxDecoration(color: Color(0xFF1A1A1A), borderRadius: BorderRadius.vertical(top: Radius.circular(32))),
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
                  onPressed: () { context.read<ScannerBloc>().add(CancelDetection()); Navigator.pop(context); },
                  child: const Text('DESCARTAR', style: TextStyle(color: Colors.white54)),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton(
                  onPressed: () { context.read<ScannerBloc>().add(AddProductToCart(item)); Navigator.pop(context); },
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
  const _SlideToConfirm({required this.text, required this.onConfirm, this.completeColor = InternoColors.success});

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
    if (oldWidget.text != widget.text) {
      setState(() { _position = 0.0; _isCompleted = false; });
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
              Positioned(
                left: 0, top: 0, bottom: 0,
                width: _height + _position,
                child: Container(decoration: BoxDecoration(color: widget.completeColor, borderRadius: BorderRadius.circular(_height / 2))),
              ),
              Center(
                child: Text(widget.text, style: TextStyle(color: _isCompleted ? Colors.black : Colors.white, fontWeight: FontWeight.w900, letterSpacing: 1)),
              ),
              Positioned(
                left: _position,
                child: GestureDetector(
                  onPanUpdate: (details) {
                    if (_isCompleted) return;
                    setState(() {
                      _position = (_position + details.delta.dx).clamp(0.0, maxDrag);
                    });
                  },
                  onPanEnd: (details) {
                    if (_isCompleted) return;
                    if (_position > maxDrag * 0.85) {
                      setState(() { _position = maxDrag; _isCompleted = true; });
                      widget.onConfirm();
                    } else {
                      setState(() { _position = 0; });
                    }
                  },
                  child: Container(
                    width: _height, height: _height,
                    decoration: const BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                    child: Icon(Icons.arrow_forward_ios, color: _isCompleted ? widget.completeColor : Colors.black, size: 20),
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

// ── SALE MODE OVERLAY PAINTER ─────────────────────────────────────────────────
class _ScannerOverlayPainter extends CustomPainter {
  final double cutoutWidth;
  final double cutoutHeight;
  final double topOffset;

  _ScannerOverlayPainter({required this.cutoutWidth, required this.cutoutHeight, required this.topOffset});

  @override
  void paint(Canvas canvas, Size size) {
    final backgroundPaint = Paint()..color = Colors.black.withValues(alpha: 0.65);
    final double left = (size.width - cutoutWidth) / 2;
    final Rect cutoutRect = Rect.fromLTWH(left, topOffset, cutoutWidth, cutoutHeight);
    final Path path = Path()
      ..addRect(Rect.fromLTWH(0, 0, size.width, size.height))
      ..addRRect(RRect.fromRectAndRadius(cutoutRect, const Radius.circular(20)))
      ..fillType = PathFillType.evenOdd;
    canvas.drawPath(path, backgroundPaint);

    final borderPaint = Paint()
      ..color = const Color(0xFF00E676)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 4.0;
    const double cornerSize = 24.0;
    final RRect rrect = RRect.fromRectAndRadius(cutoutRect, const Radius.circular(20));

    canvas.drawPath(Path()..moveTo(rrect.left, rrect.top + cornerSize)..lineTo(rrect.left, rrect.top)..lineTo(rrect.left + cornerSize, rrect.top), borderPaint);
    canvas.drawPath(Path()..moveTo(rrect.right - cornerSize, rrect.top)..lineTo(rrect.right, rrect.top)..lineTo(rrect.right, rrect.top + cornerSize), borderPaint);
    canvas.drawPath(Path()..moveTo(rrect.left, rrect.bottom - cornerSize)..lineTo(rrect.left, rrect.bottom)..lineTo(rrect.left + cornerSize, rrect.bottom), borderPaint);
    canvas.drawPath(Path()..moveTo(rrect.right - cornerSize, rrect.bottom)..lineTo(rrect.right, rrect.bottom)..lineTo(rrect.right, rrect.bottom - cornerSize), borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
