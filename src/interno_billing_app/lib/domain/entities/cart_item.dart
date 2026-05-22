import 'package:equatable/equatable.dart';
import 'product.dart';

class CartItem extends Equatable {
  final Product product;
  int quantity;
  final double taxRate;

  CartItem({
    required this.product,
    this.quantity = 1,
    this.taxRate = 0.16,
  });

  double get lineTotal => (product.price?.amount ?? 0) * quantity;
  double get taxAmount => lineTotal * taxRate;
  double get totalWithTax => lineTotal + taxAmount;
  String get currency => product.price?.currency ?? 'MXN';

  void increment() => quantity++;
  void decrement() {
    if (quantity > 1) quantity--;
  }

  CartItem copyWith({int? quantity}) {
    return CartItem(
      product: product,
      quantity: quantity ?? this.quantity,
      taxRate: taxRate,
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
