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

  const InventoryDocumentRequest({
    required this.correlationId,
    required this.type,
    required this.conceptId,
    required this.warehouseId,
    this.targetWarehouseId,
    this.externalEntity,
    this.notes,
    required this.items,
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
      };

  @override
  List<Object?> get props => [correlationId, type, conceptId, warehouseId, items];
}

class InventoryDocumentItemRequest extends Equatable {
  final String sku;
  final String productId;
  final double quantity;
  final double unitPrice;
  final String currency;
  final String location;

  const InventoryDocumentItemRequest({
    required this.sku,
    required this.productId,
    required this.quantity,
    required this.unitPrice,
    required this.currency,
    required this.location,
  });

  Map<String, dynamic> toJson() => {
        'sku': sku,
        'product_id': productId,
        'quantity': quantity,
        'unit_price': unitPrice,
        'currency': currency,
        'location': location,
      };

  @override
  List<Object?> get props => [sku, productId, quantity, unitPrice, location];
}
