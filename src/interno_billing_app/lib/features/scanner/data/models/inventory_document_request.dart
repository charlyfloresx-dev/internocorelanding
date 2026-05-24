import 'package:equatable/equatable.dart';

class InventoryDocumentRequest extends Equatable {
  final String correlationId;
  final String type; // 'IN' or 'OUT'
  final String conceptId;
  final String warehouseId;
  final String? targetWarehouseId;
  final String? externalEntity;
  final String? notes;
  final List<InventoryDocumentItemRequest> items;
  final String? appReference;
  final String? paymentMethod;

  const InventoryDocumentRequest({
    required this.correlationId,
    required this.type,
    required this.conceptId,
    required this.warehouseId,
    this.targetWarehouseId,
    this.externalEntity,
    this.notes,
    required this.items,
    this.appReference,
    this.paymentMethod,
  });

  Map<String, dynamic> toJson() => {
        'correlation_id': correlationId,
        'type': type,
        'concept_id': conceptId,
        'warehouse_id': warehouseId,
        'target_warehouse_id': targetWarehouseId,
        'external_entity': externalEntity,
        'notes': notes,
        'items': items.map((e) => e.toJson()).toList(),
        'app_reference': appReference,
        if (paymentMethod != null) 'payment_method': paymentMethod,
      };

  @override
  List<Object?> get props => [correlationId, type, conceptId, warehouseId, items, appReference, paymentMethod];
}

class InventoryDocumentItemRequest extends Equatable {
  final String sku;
  final String productId;
  final double quantity;
  final double unitPrice;
  final String currency;
  final String? location;

  const InventoryDocumentItemRequest({
    required this.sku,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
    required this.currency,
    this.location,
  });

  Map<String, dynamic> toJson() => {
        'sku': sku,
        'product_id': productId,
        'quantity': quantity,
        'unit_price': unitPrice,
        'currency': currency,
        if (location != null) 'location': location,
      };

  @override
  List<Object?> get props => [sku, productId, quantity, unitPrice, location];
}
