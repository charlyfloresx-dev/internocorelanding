class SaleRequest {
  final List<SaleItemRequest> items;
  final String warehouseId;
  final String? partnerId;
  final double totalAmount;
  final String? comments;
  final String? paymentMethod;
  final String? appReference;

  SaleRequest({
    required this.items,
    required this.warehouseId,
    this.partnerId,
    required this.totalAmount,
    this.comments,
    this.paymentMethod,
    this.appReference,
  });

  Map<String, dynamic> toJson() => {
        'items': items.map((e) => e.toJson()).toList(),
        'warehouse_id': warehouseId,
        'partner_id': partnerId,
        'total_amount': totalAmount,
        'comments': comments,
        'payment_method': paymentMethod,
        'app_reference': appReference,
      };
}

class SaleItemRequest {
  final String productId;
  final String sku;
  final double quantity;
  final double unitPrice;

  SaleItemRequest({
    required this.productId,
    required this.sku,
    required this.quantity,
    required this.unitPrice,
  });

  Map<String, dynamic> toJson() => {
        'product_id': productId,
        'sku': sku,
        'quantity': quantity,
        'unit_price': unitPrice,
      };
}
