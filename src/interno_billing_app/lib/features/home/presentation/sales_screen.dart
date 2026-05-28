import 'dart:async';
import 'package:flutter/material.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:interno_billing_app/features/scanner/data/repositories/partner_repository.dart';
import 'package:interno_billing_app/core/services/product_sync_service.dart';
import 'package:interno_billing_app/core/database/local_database.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:interno_billing_app/domain/entities/product.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/domain/entities/partner.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';
import 'package:interno_billing_app/features/scanner/presentation/payment_confirmation_screen.dart';

class SalesScreen extends StatefulWidget {
  const SalesScreen({super.key});

  @override
  State<SalesScreen> createState() => _SalesScreenState();
}

class _SalesScreenState extends State<SalesScreen> {
  final DraggableScrollableController _sheetController = DraggableScrollableController();

  double _slideProgress = 0.0;
  bool _isSyncing = false;
  String _syncStatusText = 'Sin sincronizar';
  int _cachedProductCount = 0;

  // Cached product list for quick catalog search dialog
  List<Map<String, dynamic>> _productCatalog = [];

  // Guard against showing multiple product-detected modals simultaneously
  bool _isProductModalShown = false;

  @override
  void initState() {
    super.initState();
    _loadSyncStatus();
    _loadProductsFromDb();
    _autoSyncIfNeeded();
  }

  @override
  void dispose() {
    _sheetController.dispose();
    super.dispose();
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
        if (mounted) setState(() => _slideProgress = start * (1.0 - (currentStep / steps)));
      }
    });
  }

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
      debugPrint('Error cargando catálogo desde DB: $e');
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

    // Capture messenger before any async gap
    final messenger = ScaffoldMessenger.of(context);

    try {
      final syncService = sl<ProductSyncService>();
      int result = await syncService.fullSync(
        onProgress: (current, total) {
          if (mounted) setState(() => _syncStatusText = 'Descargando $current/$total...');
        },
      );

      await _loadSyncStatus();
      await _loadProductsFromDb();

      if (result >= 0) {
        messenger.showSnackBar(
          SnackBar(
            content: Text('✅ Catálogo sincronizado: $_cachedProductCount productos'),
            backgroundColor: const Color(0xFF1E3A27),
            duration: const Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      messenger.showSnackBar(
        SnackBar(
          content: Text('❌ Error de sincronización: $e'),
          backgroundColor: Colors.redAccent.shade700,
        ),
      );
    } finally {
      if (mounted) setState(() => _isSyncing = false);
    }
  }

  void _navigateToPayment(BuildContext context) {
    final prefs = sl<SharedPreferences>();
    final warehouseId = prefs.getString('warehouse_id') ?? '';
    final bloc = context.read<ScannerBloc>();

    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => BlocProvider.value(
          value: bloc,
          child: PaymentConfirmationScreen(warehouseId: warehouseId),
        ),
      ),
    );
  }

  void _showProductDetectedSheet(BuildContext context, CartItem item) {
    if (_isProductModalShown) return;
    _isProductModalShown = true;

    final bloc = context.read<ScannerBloc>();
    final price = item.product.price?.amount ?? 0.0;

    showModalBottomSheet(
      context: context,
      backgroundColor: Theme.of(context).cardColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        final cs = Theme.of(ctx).colorScheme;
        return Padding(
        padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 5,
                decoration: BoxDecoration(
                  color: cs.onSurface.withValues(alpha: 0.24),
                  borderRadius: BorderRadius.circular(2.5),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              item.product.name,
              style: TextStyle(color: cs.onSurface, fontSize: 18, fontWeight: FontWeight.bold),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 4),
            Text(
              item.product.code ?? item.product.sku,
              style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 12, letterSpacing: 0.5),
            ),
            const SizedBox(height: 16),
            Text(
              '\$${price.toStringAsFixed(2)}',
              style: const TextStyle(color: InternoColors.cyan, fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {
                      bloc.add(CancelDetection());
                      Navigator.pop(ctx);
                    },
                    style: OutlinedButton.styleFrom(
                      side: BorderSide(color: cs.onSurface.withValues(alpha: 0.24)),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text('Cancelar', style: TextStyle(color: cs.onSurface.withValues(alpha: 0.54))),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: ElevatedButton(
                    onPressed: () {
                      bloc.add(AddProductToCart(item));
                      Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00E676),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: const Text(
                      'Agregar al Carrito',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      );
      },
    ).whenComplete(() => _isProductModalShown = false);
  }

  Future<void> _showPartnerSelectionDialog(ScannerBloc bloc) async {
    List<Partner> partners = [];
    try {
      final partnerRepo = sl<PartnerRepository>();
      partners = await partnerRepo.getPartners(type: 'CUSTOMER');
    } catch (e) {
      debugPrint('Error cargando partners: $e');
    }

    if (!mounted) return;

    showDialog(
      context: context,
      builder: (dialogContext) {
        final cs = Theme.of(dialogContext).colorScheme;
        final cardBg = Theme.of(dialogContext).cardColor;
        final currentPartner = bloc.state.selectedPartner;
        return AlertDialog(
          backgroundColor: cardBg,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Text(
            'Seleccionar Cliente',
            style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold),
          ),
          content: SizedBox(
            width: double.maxFinite,
            child: ListView(
              shrinkWrap: true,
              children: [
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                  title: Text(
                    'Público General',
                    style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text('CUST-0000', style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38))),
                  trailing: currentPartner == null
                      ? const Icon(Icons.check_circle, color: InternoColors.success)
                      : null,
                  onTap: () {
                    bloc.add(SelectPartner(null));
                    Navigator.pop(dialogContext);
                  },
                ),
                ...partners.map((p) => ListTile(
                  contentPadding: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
                  title: Text(
                    p.name,
                    style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold),
                  ),
                  subtitle: Text(p.code, style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38))),
                  trailing: currentPartner?.id == p.id
                      ? const Icon(Icons.check_circle, color: InternoColors.success)
                      : null,
                  onTap: () {
                    bloc.add(SelectPartner(p));
                    Navigator.pop(dialogContext);
                  },
                )),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final double screenHeight = MediaQuery.of(context).size.height;
    final double screenWidth = MediaQuery.of(context).size.width;

    final double cutoutWidth = screenWidth * 0.75;
    const double cutoutHeight = 220.0;
    final double scannerTop = (screenHeight - cutoutHeight) / 2 - 100;
    final double laserTop = scannerTop + (cutoutHeight / 2);

    return Scaffold(
      backgroundColor: Colors.black,
      body: BlocConsumer<ScannerBloc, ScannerState>(
        listenWhen: (previous, current) =>
            previous.detectedProduct != current.detectedProduct ||
            previous.error != current.error ||
            previous.successMessage != current.successMessage,
        listener: (context, state) {
          if (state.detectedProduct != null) {
            _showProductDetectedSheet(context, state.detectedProduct!);
          }
          if (state.error != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(state.error!),
                backgroundColor: Colors.redAccent.shade700,
                behavior: SnackBarBehavior.floating,
              ),
            );
          }
        },
        builder: (context, state) {
          final bloc = context.read<ScannerBloc>();

          return Stack(
            children: [
              // ── 1. FULLSCREEN SCANNER CAMERA ───────────────────────────────
              Positioned.fill(
                child: MobileScanner(
                  onDetect: (capture) {
                    for (final barcode in capture.barcodes) {
                      if (barcode.rawValue != null) {
                        bloc.add(BarcodeScanned(barcode.rawValue!));
                      }
                    }
                  },
                ),
              ),

              // ── 2. SCANNING OVERLAY ────────────────────────────────────────
              Positioned.fill(
                child: CustomPaint(
                  painter: _ScannerOverlayPainter(
                    cutoutWidth: cutoutWidth,
                    cutoutHeight: cutoutHeight,
                    topOffset: scannerTop,
                  ),
                ),
              ),

              Positioned(
                top: laserTop,
                left: screenWidth * 0.15,
                right: screenWidth * 0.15,
                child: Container(
                  height: 3,
                  decoration: BoxDecoration(
                    color: Colors.redAccent,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.redAccent.withValues(alpha: 0.8),
                        blurRadius: 10,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                ),
              ),

              // ── 3. TOP BAR ─────────────────────────────────────────────────
              Positioned(
                top: 50,
                left: 20,
                right: 20,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildCircularButton(
                      icon: Icons.close_rounded,
                      onTap: () => Navigator.of(context).maybePop(),
                    ),

                    // Total pill
                    GestureDetector(
                      onTap: () {},
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                        decoration: BoxDecoration(
                          color: Colors.black.withValues(alpha: 0.85),
                          borderRadius: BorderRadius.circular(30),
                          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
                          boxShadow: const [
                            BoxShadow(color: Colors.black54, blurRadius: 10, offset: Offset(0, 4)),
                          ],
                        ),
                        child: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Text(
                              'MX\$',
                              style: TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 16,
                              ),
                            ),
                            const SizedBox(width: 4),
                            Text(
                              state.grandTotal.toStringAsFixed(2),
                              style: const TextStyle(
                                color: Colors.white,
                                fontWeight: FontWeight.w900,
                                fontSize: 22,
                                letterSpacing: -0.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    _buildCircularButton(
                      icon: Icons.search_rounded,
                      onTap: () => _showQuickCatalogDialog(context, bloc),
                    ),
                  ],
                ),
              ),

              // ── 4. BOTTOM SHEET ────────────────────────────────────────────
              DraggableScrollableSheet(
                controller: _sheetController,
                initialChildSize: 0.11,
                minChildSize: 0.11,
                maxChildSize: 0.85,
                builder: (BuildContext ctx, ScrollController scrollController) {
                  final cs = Theme.of(ctx).colorScheme;
                  final sheetBg = Theme.of(ctx).scaffoldBackgroundColor;
                  return Container(
                    decoration: BoxDecoration(
                      color: sheetBg,
                      borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
                      boxShadow: const [
                        BoxShadow(color: Colors.black87, blurRadius: 20, spreadRadius: 5),
                      ],
                    ),
                    child: ListView(
                      controller: scrollController,
                      padding: EdgeInsets.zero,
                      children: [
                        const SizedBox(height: 10),
                        Center(
                          child: Container(
                            width: 40,
                            height: 5,
                            decoration: BoxDecoration(
                              color: cs.onSurface.withValues(alpha: 0.24),
                              borderRadius: BorderRadius.circular(2.5),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Sheet header row
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              // Partner selector
                              IconButton(
                                icon: Icon(Icons.tune_rounded, color: cs.onSurface, size: 24),
                                onPressed: () => _showPartnerSelectionDialog(bloc),
                                style: IconButton.styleFrom(
                                  backgroundColor: cs.onSurface.withValues(alpha: 0.04),
                                  padding: const EdgeInsets.all(12),
                                ),
                              ),

                              // Cart status
                              Column(
                                children: [
                                  Text(
                                    state.items.isEmpty
                                        ? 'Escaneando...'
                                        : '${state.totalItems} ${state.totalItems == 1 ? 'artículo' : 'artículos'}',
                                    style: TextStyle(
                                      color: cs.onSurface,
                                      fontWeight: FontWeight.w900,
                                      fontSize: 18,
                                      letterSpacing: -0.5,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Cliente: ${state.selectedPartner?.name ?? 'Público General'}',
                                    style: TextStyle(color: cs.onSurface.withValues(alpha: 0.54), fontSize: 12),
                                  ),
                                  // Sync indicator
                                  GestureDetector(
                                    onTap: _triggerSync,
                                    child: Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        if (_isSyncing)
                                          const SizedBox(
                                            width: 10,
                                            height: 10,
                                            child: CircularProgressIndicator(
                                              strokeWidth: 1.5,
                                              color: Color(0xFF00E676),
                                            ),
                                          )
                                        else
                                          Icon(
                                            Icons.sync_rounded,
                                            size: 10,
                                            color: _cachedProductCount > 0
                                                ? const Color(0xFF00E676)
                                                : Colors.amber,
                                          ),
                                        const SizedBox(width: 4),
                                        Text(
                                          '$_cachedProductCount SKUs · $_syncStatusText',
                                          style: TextStyle(
                                            color: _cachedProductCount > 0
                                                ? cs.onSurface.withValues(alpha: 0.3)
                                                : Colors.amber.shade300,
                                            fontSize: 9,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),

                              IconButton(
                                icon: Icon(Icons.list_rounded, color: cs.onSurface, size: 24),
                                onPressed: _toggleCartSheet,
                                style: IconButton.styleFrom(
                                  backgroundColor: cs.onSurface.withValues(alpha: 0.04),
                                  padding: const EdgeInsets.all(12),
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),
                        Divider(color: cs.onSurface.withValues(alpha: 0.1), height: 1),

                        // Cart content
                        if (state.items.isEmpty) ...[
                          const SizedBox(height: 40),
                          Center(
                            child: Column(
                              children: [
                                Container(
                                  padding: const EdgeInsets.all(20),
                                  decoration: BoxDecoration(
                                    color: cs.onSurface.withValues(alpha: 0.02),
                                    shape: BoxShape.circle,
                                  ),
                                  child: Icon(
                                    Icons.receipt_long_outlined,
                                    color: cs.onSurface.withValues(alpha: 0.24),
                                    size: 48,
                                  ),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  'No hay productos agregados',
                                  style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontWeight: FontWeight.bold),
                                ),
                                const SizedBox(height: 6),
                                Padding(
                                  padding: const EdgeInsets.symmetric(horizontal: 40),
                                  child: Text(
                                    'Apunta la cámara a un código de barras o utiliza la lupa arriba para agregarlos.',
                                    textAlign: TextAlign.center,
                                    style: TextStyle(color: cs.onSurface.withValues(alpha: 0.1), fontSize: 12),
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
                                  color: cs.onSurface.withValues(alpha: 0.03),
                                  borderRadius: BorderRadius.circular(16),
                                  border: Border.all(
                                    color: cs.onSurface.withValues(alpha: 0.04),
                                  ),
                                ),
                                child: Row(
                                  children: [
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            item.product.name,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyle(
                                              color: cs.onSurface,
                                              fontWeight: FontWeight.bold,
                                              fontSize: 15,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Text(
                                            item.product.code ?? item.product.sku,
                                            maxLines: 1,
                                            overflow: TextOverflow.ellipsis,
                                            style: TextStyle(
                                              color: cs.onSurface.withValues(alpha: 0.38),
                                              fontSize: 11,
                                              letterSpacing: 0.5,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                    SizedBox(
                                      width: 90,
                                      child: Text(
                                        '\$${item.lineTotal.toStringAsFixed(2)}',
                                        textAlign: TextAlign.right,
                                        style: TextStyle(
                                          color: cs.onSurface,
                                          fontWeight: FontWeight.bold,
                                          fontSize: 15,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 16),
                                    Row(
                                      children: [
                                        IconButton(
                                          icon: Icon(
                                            Icons.remove_circle,
                                            color: cs.onSurface.withValues(alpha: 0.54),
                                            size: 30,
                                          ),
                                          onPressed: () {
                                            final newQty = item.quantity - 1;
                                            if (newQty <= 0) {
                                              bloc.add(RemoveItem(item.product.id));
                                            } else {
                                              bloc.add(UpdateQuantity(item.product.id, newQty));
                                            }
                                          },
                                          padding: EdgeInsets.zero,
                                          constraints: const BoxConstraints(
                                            minWidth: 44,
                                            minHeight: 44,
                                          ),
                                        ),
                                        Padding(
                                          padding: const EdgeInsets.symmetric(horizontal: 10),
                                          child: Text(
                                            '${item.quantity}',
                                            style: TextStyle(
                                              color: cs.onSurface,
                                              fontWeight: FontWeight.bold,
                                              fontSize: 18,
                                            ),
                                          ),
                                        ),
                                        IconButton(
                                          icon: Icon(
                                            Icons.add_circle,
                                            color: cs.onSurface,
                                            size: 30,
                                          ),
                                          onPressed: () => bloc.add(
                                            UpdateQuantity(item.product.id, item.quantity + 1),
                                          ),
                                          padding: EdgeInsets.zero,
                                          constraints: const BoxConstraints(
                                            minWidth: 44,
                                            minHeight: 44,
                                          ),
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
                                    color: cs.onSurface.withValues(alpha: 0.05),
                                    borderRadius: BorderRadius.circular(28),
                                    border: Border.all(
                                      color: cs.onSurface.withValues(alpha: 0.1),
                                    ),
                                  ),
                                  child: Stack(
                                    children: [
                                      // Dynamic green fill
                                      Positioned(
                                        left: 0,
                                        top: 0,
                                        bottom: 0,
                                        width: handleSize + (_slideProgress * maxDragDistance),
                                        child: Container(
                                          decoration: BoxDecoration(
                                            color: const Color(0xFF00E676),
                                            borderRadius: BorderRadius.circular(28),
                                          ),
                                        ),
                                      ),

                                      // Guide text
                                      Center(
                                        child: AnimatedOpacity(
                                          duration: const Duration(milliseconds: 100),
                                          opacity: (1.0 - _slideProgress).clamp(0.0, 1.0),
                                          child: Row(
                                            mainAxisAlignment: MainAxisAlignment.center,
                                            children: [
                                              Icon(
                                                Icons.keyboard_double_arrow_right_rounded,
                                                color: cs.onSurface,
                                                size: 20,
                                              ),
                                              const SizedBox(width: 8),
                                              Text(
                                                'DESLIZAR PARA COBRAR (\$${state.grandTotal.toStringAsFixed(2)})',
                                                style: TextStyle(
                                                  color: cs.onSurface,
                                                  fontWeight: FontWeight.w900,
                                                  fontSize: 13,
                                                  letterSpacing: 0.5,
                                                ),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ),

                                      // Drag handle
                                      Positioned(
                                        left: _slideProgress * maxDragDistance,
                                        top: 0,
                                        bottom: 0,
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
                                              boxShadow: [
                                                BoxShadow(
                                                  color: Colors.black26,
                                                  blurRadius: 4,
                                                  offset: Offset(2, 0),
                                                ),
                                              ],
                                            ),
                                            child: Center(
                                              child: Icon(
                                                Icons.arrow_forward_rounded,
                                                color: _slideProgress > 0.85
                                                    ? const Color(0xFF00E676)
                                                    : Colors.black,
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
          );
        },
      ),
    );
  }

  Widget _buildCircularButton({required IconData icon, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(30),
      child: Container(
        width: 54,
        height: 54,
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.85),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          boxShadow: const [
            BoxShadow(color: Colors.black54, blurRadius: 8, offset: Offset(0, 3)),
          ],
        ),
        child: Icon(icon, color: Colors.white, size: 24),
      ),
    );
  }

  void _showQuickCatalogDialog(BuildContext context, ScannerBloc bloc) {
    showDialog(
      context: context,
      builder: (dialogContext) {
        final cs = Theme.of(dialogContext).colorScheme;
        final cardBg = Theme.of(dialogContext).cardColor;
        return AlertDialog(
          backgroundColor: cardBg,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Búsqueda Rápida',
                style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: _isSyncing
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Color(0xFF00E676),
                        ),
                      )
                    : Icon(
                        Icons.sync_rounded,
                        color: _cachedProductCount > 0 ? const Color(0xFF00E676) : Colors.amber,
                      ),
                onPressed: () {
                  Navigator.pop(dialogContext);
                  _triggerSync();
                },
                tooltip: 'Sincronizar catálogo',
              ),
            ],
          ),
          content: SizedBox(
            width: double.maxFinite,
            child: _productCatalog.isEmpty
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.cloud_download_outlined, color: cs.onSurface.withValues(alpha: 0.24), size: 48),
                      const SizedBox(height: 16),
                      Text(
                        'No hay productos en caché local.',
                        style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Pulsa el botón de sincronización para descargar el catálogo del servidor.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: cs.onSurface.withValues(alpha: 0.24), fontSize: 12),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: () {
                          Navigator.pop(dialogContext);
                          _triggerSync();
                        },
                        icon: const Icon(Icons.sync),
                        label: const Text('Sincronizar Ahora'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00E676),
                        ),
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
                        title: Text(
                          p['name'] as String,
                          style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          'Código: ${p['code']}  ·  \$${(p['price'] as double).toStringAsFixed(2)}',
                          style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38)),
                        ),
                        trailing: const Icon(Icons.add_circle, color: Color(0xFF00E676)),
                        onTap: () {
                          final product = Product(
                            id: p['id'] as String,
                            name: p['name'] as String,
                            sku: p['sku'] as String,
                            code: p['code'] as String,
                            price: Price(
                              amount: p['price'] as double,
                              currency: p['currency'] as String,
                            ),
                          );
                          bloc.add(AddProductToCart(CartItem(product: product, taxRate: 0.16)));
                          Navigator.pop(dialogContext);
                        },
                      );
                    },
                  ),
          ),
        );
      },
    );
  }
}

// ── CUSTOM PAINTER: SCANNER OVERLAY ───────────────────────────────────────────
class _ScannerOverlayPainter extends CustomPainter {
  final double cutoutWidth;
  final double cutoutHeight;
  final double topOffset;

  _ScannerOverlayPainter({
    required this.cutoutWidth,
    required this.cutoutHeight,
    required this.topOffset,
  });

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

    canvas.drawPath(
      Path()
        ..moveTo(rrect.left, rrect.top + cornerSize)
        ..lineTo(rrect.left, rrect.top)
        ..lineTo(rrect.left + cornerSize, rrect.top),
      borderPaint,
    );
    canvas.drawPath(
      Path()
        ..moveTo(rrect.right - cornerSize, rrect.top)
        ..lineTo(rrect.right, rrect.top)
        ..lineTo(rrect.right, rrect.top + cornerSize),
      borderPaint,
    );
    canvas.drawPath(
      Path()
        ..moveTo(rrect.left, rrect.bottom - cornerSize)
        ..lineTo(rrect.left, rrect.bottom)
        ..lineTo(rrect.left + cornerSize, rrect.bottom),
      borderPaint,
    );
    canvas.drawPath(
      Path()
        ..moveTo(rrect.right - cornerSize, rrect.bottom)
        ..lineTo(rrect.right, rrect.bottom)
        ..lineTo(rrect.right, rrect.bottom - cornerSize),
      borderPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}