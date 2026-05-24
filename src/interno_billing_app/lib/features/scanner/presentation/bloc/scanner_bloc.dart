import 'dart:async';
import 'dart:convert';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import '../../data/repositories/product_repository.dart';
import '../../data/repositories/sale_repository.dart';
import '../../data/repositories/local_draft_repository.dart';
import '../../data/models/draft_sale.dart';
import '../../data/models/inventory_document_request.dart';
import 'package:interno_billing_app/core/enums/app_reference.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/domain/entities/partner.dart';
import 'package:uuid/uuid.dart';
import 'package:dio/dio.dart';

enum ScannerMode { sale, entry }

// ── Events ──────────────────────────────────────────────────────────────────
abstract class ScannerEvent extends Equatable {
  @override
  List<Object?> get props => [];
}

class ModeSelected extends ScannerEvent {
  final ScannerMode mode;
  ModeSelected(this.mode);

  @override
  List<Object?> get props => [mode];
}

class BarcodeScanned extends ScannerEvent {
  final String code;
  BarcodeScanned(this.code);

  @override
  List<Object?> get props => [code];
}

class RemoveItem extends ScannerEvent {
  final String productId;
  RemoveItem(this.productId);

  @override
  List<Object?> get props => [productId];
}

class UpdateQuantity extends ScannerEvent {
  final String productId;
  final int quantity;
  UpdateQuantity(this.productId, this.quantity);

  @override
  List<Object?> get props => [productId, quantity];
}

class SelectPartner extends ScannerEvent {
  final Partner? partner;
  SelectPartner(this.partner);

  @override
  List<Object?> get props => [partner];
}

class ClearCart extends ScannerEvent {}

class AddProductToCart extends ScannerEvent {
  final CartItem item;
  AddProductToCart(this.item);

  @override
  List<Object?> get props => [item];
}

class CancelDetection extends ScannerEvent {}

class CheckoutRequested extends ScannerEvent {
  final String warehouseId;
  final String? comments;
  final String? paymentMethod;
  final String? appReference;
  CheckoutRequested({required this.warehouseId, this.comments, this.paymentMethod, this.appReference});

  @override
  List<Object?> get props => [warehouseId, comments, paymentMethod, appReference];
}

// ── State ───────────────────────────────────────────────────────────────────
class ScannerState extends Equatable {
  final List<CartItem> items;
  final bool isLoading;
  final String? lastScannedCode;
  final String? error;
  final String? successMessage;
  final double taxRate;
  final Partner? selectedPartner;
  final ScannerMode mode;

  const ScannerState({
    this.items = const [],
    this.isLoading = false,
    this.lastScannedCode,
    this.error,
    this.successMessage,
    this.taxRate = 0.16,
    this.selectedPartner,
    this.detectedProduct,
    this.mode = ScannerMode.sale,
  });

  final CartItem? detectedProduct;

  /// Net subtotal (before tax)
  double get subtotal => items.fold(0.0, (sum, item) => sum + item.lineTotal);

  /// Total tax
  double get totalTax => items.fold(0.0, (sum, item) => sum + item.taxAmount);

  /// Grand total (including tax)
  double get grandTotal => subtotal + totalTax;

  /// Total items count
  int get totalItems => items.fold(0, (sum, item) => sum + item.quantity);

  /// Currency (from first item or default)
  String get currency =>
      items.isNotEmpty ? items.first.currency : 'MXN';

  ScannerState copyWith({
    List<CartItem>? items,
    bool? isLoading,
    String? lastScannedCode,
    String? error,
    String? successMessage,
    double? taxRate,
    Partner? selectedPartner,
    bool clearPartner = false,
    CartItem? detectedProduct,
    bool clearDetected = false,
    ScannerMode? mode,
  }) {
    return ScannerState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      lastScannedCode: lastScannedCode ?? this.lastScannedCode,
      error: error,
      successMessage: successMessage,
      taxRate: taxRate ?? this.taxRate,
      selectedPartner: clearPartner ? null : (selectedPartner ?? this.selectedPartner),
      detectedProduct: clearDetected ? null : (detectedProduct ?? this.detectedProduct),
      mode: mode ?? this.mode,
    );
  }

  @override
  List<Object?> get props =>
      [items, isLoading, lastScannedCode, error, successMessage, selectedPartner, mode];
}

// ── Bloc ────────────────────────────────────────────────────────────────────
class ScannerBloc extends Bloc<ScannerEvent, ScannerState> {
  final ProductRepository _repository;
  final SaleRepository? _saleRepository;
  final LocalDraftRepository? _localDraftRepository;
  final double taxRate;
  String? _lastProcessedCode;
  DateTime? _lastScanTime;

  ScannerBloc({
    required ProductRepository repository,
    SaleRepository? saleRepository,
    LocalDraftRepository? localDraftRepository,
    this.taxRate = 0.16,
  })  : _repository = repository,
        _saleRepository = saleRepository,
        _localDraftRepository = localDraftRepository,
        super(_buildInitialState(localDraftRepository, 0.16)) {
    on<ModeSelected>(_onModeSelected);
    on<BarcodeScanned>(_onBarcodeScanned);
    on<RemoveItem>(_onRemoveItem);
    on<UpdateQuantity>(_onUpdateQuantity);
    on<SelectPartner>(_onSelectPartner);
    on<ClearCart>(_onClearCart);
    on<AddProductToCart>(_onAddProductToCart);
    on<CancelDetection>(_onCancelDetection);
    on<CheckoutRequested>(_onCheckout);
  }

  /// Builds the initial state by restoring any persisted draft.
  /// Called from super() — no emit needed.
  static ScannerState _buildInitialState(
    LocalDraftRepository? repo,
    double taxRate,
  ) {
    if (repo == null) return ScannerState(taxRate: taxRate);
    try {
      final draft = repo.loadDraft();
      if (draft != null && draft.items.isNotEmpty) {
        return ScannerState(
          taxRate: taxRate,
          items: draft.items,
          selectedPartner: draft.selectedPartner,
          mode: draft.mode == 'entry' ? ScannerMode.entry : ScannerMode.sale,
        );
      }
    } catch (_) {}
    return ScannerState(taxRate: taxRate);
  }

  void _onModeSelected(ModeSelected event, Emitter<ScannerState> emit) {
    if (event.mode == state.mode) return;
    emit(ScannerState(
      mode: event.mode,
      taxRate: taxRate,
      selectedPartner: state.selectedPartner,
    ));
    _saveDraftToLocal();
  }

  Future<void> _onSelectPartner(SelectPartner event, Emitter<ScannerState> emit) async {
    final currentItems = state.items;

    emit(state.copyWith(
      selectedPartner: event.partner,
      clearPartner: event.partner == null,
      isLoading: currentItems.isNotEmpty,
    ));

    if (currentItems.isEmpty) {
      _saveDraftToLocal();
      return;
    }

    // Re-fetch prices for all cart items using the new partner's PriceAgreement
    final newPartnerId = event.partner?.id;
    final updatedItems = <CartItem>[];

    for (final item in currentItems) {
      try {
        final repriced = await _repository.lookupByCode(
          item.product.sku,
          partnerId: newPartnerId,
        );
        updatedItems.add(repriced != null
            ? CartItem(product: repriced, quantity: item.quantity, taxRate: item.taxRate)
            : item);
      } catch (_) {
        updatedItems.add(item);
      }
    }

    emit(state.copyWith(items: updatedItems, isLoading: false));
    _saveDraftToLocal();
  }

  Future<void> _onBarcodeScanned(
    BarcodeScanned event,
    Emitter<ScannerState> emit,
  ) async {
    final now = DateTime.now();
    
    // Parse code to handle URL-based QR codes (e.g., qrto.org/ECM-600)
    String parsedCode = event.code;
    if (parsedCode.contains('/')) {
      parsedCode = parsedCode.split('/').last;
    }

    if (_lastProcessedCode == parsedCode &&
        _lastScanTime != null &&
        now.difference(_lastScanTime!).inMilliseconds < 1500) {
      return;
    }
    _lastProcessedCode = parsedCode;
    _lastScanTime = now;

    final existingIndex = state.items.indexWhere(
      (item) => item.product.sku == parsedCode || item.product.code == parsedCode,
    );

    if (existingIndex >= 0) {
      final existingItem = state.items[existingIndex];
      HapticFeedback.mediumImpact();
      emit(state.copyWith(
        isLoading: false,
        detectedProduct: existingItem,
      ));
      return;
    }

    emit(state.copyWith(isLoading: true, lastScannedCode: parsedCode));

    try {
      final product = await _repository.lookupByCode(
        parsedCode, 
        partnerId: state.selectedPartner?.id
      );
      if (product == null) {
        HapticFeedback.heavyImpact();
        emit(state.copyWith(
          isLoading: false,
          error: 'Producto no encontrado: $parsedCode',
        ));
        return;
      }

      HapticFeedback.mediumImpact();
      emit(state.copyWith(
        isLoading: false,
        detectedProduct: CartItem(product: product, taxRate: taxRate),
      ));
    } catch (e) {
      _handleError(e, emit);
    }
  }

  void _onAddProductToCart(AddProductToCart event, Emitter<ScannerState> emit) {
    final existingIndex = state.items.indexWhere(
      (item) => item.product.id == event.item.product.id,
    );

    if (existingIndex >= 0) {
      final updatedItems = List<CartItem>.from(state.items);
      updatedItems[existingIndex] = updatedItems[existingIndex].copyWith(
        quantity: updatedItems[existingIndex].quantity + 1,
      );
      emit(state.copyWith(
        items: updatedItems,
        clearDetected: true,
        successMessage: '+1 ${updatedItems[existingIndex].product.name}',
      ));
    } else {
      emit(state.copyWith(
        items: [...state.items, event.item],
        clearDetected: true,
        successMessage: '✓ ${event.item.product.name}',
      ));
    }
    HapticFeedback.selectionClick();
    _saveDraftToLocal();
  }

  void _onCancelDetection(CancelDetection event, Emitter<ScannerState> emit) {
    emit(state.copyWith(clearDetected: true));
  }

  void _onRemoveItem(RemoveItem event, Emitter<ScannerState> emit) {
    final updatedItems = state.items
        .where((item) => item.product.id != event.productId)
        .toList();
    emit(state.copyWith(items: updatedItems));
    _saveDraftToLocal();
  }

  void _onUpdateQuantity(UpdateQuantity event, Emitter<ScannerState> emit) {
    final updatedItems = state.items.map((item) {
      if (item.product.id == event.productId) {
        return item.copyWith(quantity: event.quantity);
      }
      return item;
    }).toList();
    emit(state.copyWith(items: updatedItems));
    _saveDraftToLocal();
  }

  void _onClearCart(ClearCart event, Emitter<ScannerState> emit) {
    emit(ScannerState(taxRate: taxRate, selectedPartner: state.selectedPartner));
    _clearDraftFromLocal();
  }

  Future<void> _onCheckout(
    CheckoutRequested event,
    Emitter<ScannerState> emit,
  ) async {
    if (state.items.isEmpty || _saleRepository == null) return;

    emit(state.copyWith(isLoading: true));

    try {
      final isEntry = state.mode == ScannerMode.entry;

      final request = InventoryDocumentRequest(
        correlationId: const Uuid().v4(),
        type: isEntry ? 'IN' : 'OUT',
        conceptId: isEntry ? 'ENT-PUR' : 'SAL-VEN',
        warehouseId: event.warehouseId,
        externalEntity: state.selectedPartner?.id,
        notes: event.comments ?? (isEntry ? 'Mobile Industrial Entry' : 'Mobile POS Sale'),
        paymentMethod: isEntry ? null : event.paymentMethod,
        items: state.items
            .map((item) => InventoryDocumentItemRequest(
                  sku: item.product.sku,
                  productId: item.product.id,
                  quantity: item.quantity.toDouble(),
                  unitPrice: item.product.price?.amount ?? 0.0,
                  currency: item.currency,
                  location: isEntry ? 'SYS_RECEIVING' : null,
                ))
            .toList(),
        appReference: event.appReference ?? AppReference.mobileScanner.value,
      );

      await _saleRepository.createDocument(request);

      HapticFeedback.heavyImpact();
      _clearDraftFromLocal();
      emit(ScannerState(
        successMessage: isEntry
            ? '✓ Entrada Registrada Exitosamente'
            : '✓ Venta Procesada Exitosamente',
        taxRate: taxRate,
        selectedPartner: state.selectedPartner,
        mode: state.mode,
      ));
    } catch (e) {
      _handleError(e, emit);
    }
  }

  void _saveDraftToLocal() {
    if (_localDraftRepository == null) return;
    try {
      _localDraftRepository.saveDraft(DraftSale(
        items: state.items,
        selectedPartner: state.selectedPartner,
        mode: state.mode == ScannerMode.entry ? 'entry' : 'sale',
      ));
    } catch (_) {}
  }

  void _clearDraftFromLocal() {
    if (_localDraftRepository == null) return;
    try {
      _localDraftRepository.clearDraft();
    } catch (_) {}
  }

  void _handleError(dynamic e, Emitter<ScannerState> emit) {
    String message = 'Error desconocido';
    
    if (e is DioException) {
      final response = e.response;
      if (response != null && response.data is Map) {
        final data = response.data as Map;
        final errorMsg = data['message'] ?? data['detail'] ?? '';
        
        if (errorMsg.toString().contains('ERR_LOCATION_OVERFLOW_UNITS')) {
          message = '⚠️ CAPACIDAD EXCEDIDA: La ubicación no tiene espacio suficiente para estas unidades.';
        } else if (errorMsg.toString().contains('ERR_WAREHOUSE_LOCK')) {
          message = '🔒 ALMACÉN BLOQUEADO: No se permiten movimientos en este momento.';
        } else if (errorMsg.toString().contains('ERR_INSUFFICIENT_STOCK')) {
          message = '❌ STOCK INSUFICIENTE: No hay existencias disponibles para completar la operación.';
        } else {
          message = errorMsg.toString();
        }
      } else {
        message = 'Error de red: ${e.type}';
      }
    } else {
      message = e.toString();
    }

    emit(state.copyWith(
      isLoading: false,
      error: message,
    ));
  }
}
