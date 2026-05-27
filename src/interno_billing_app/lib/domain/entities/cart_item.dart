import 'package:equatable/equatable.dart';
import 'product.dart';

class CartItem extends Equatable {
  final Product product;
  final int quantity;
  final double taxRate;

  const CartItem({
    required this.product,
    this.quantity = 1,
    this.taxRate = 0.16,
  });

  double get lineTotal => (product.price?.amount ?? 0) * quantity;
  double get taxAmount => lineTotal * taxRate;
  double get totalWithTax => lineTotal + taxAmount;
  String get currency => product.price?.currency ?? 'MXN';

  CartItem copyWith({int? quantity, double? taxRate}) {
    return CartItem(
      product: product,
      quantity: quantity ?? this.quantity,
      taxRate: taxRate ?? this.taxRate,
    );
  }

  Map<String, dynamic> toJson() => {
        'product': product.toJson(),
        'quantity': quantity,
        'tax_rate': taxRate,
      };

  factory CartItem.fromJson(Map<String, dynamic> json) {
    return CartItem(
      product: Product.fromJson(json['product'] as Map<String, dynamic>),
      quantity: (json['quantity'] as num?)?.toInt() ?? 1,
      taxRate: (json['tax_rate'] as num?)?.toDouble() ?? 0.16,
    );
  }

  @override
  List<Object?> get props => [product, quantity, taxRate];
}
