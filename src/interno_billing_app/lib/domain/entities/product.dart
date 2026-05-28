import 'package:equatable/equatable.dart';
import '../../../features/scanner/data/models/scan_pattern.dart';

class Product extends Equatable {
  final String id;
  final String name;
  final String sku;
  final String? code;
  final String? brandName;
  final String? uomName;
  final Price? price;
  final double? currentStock;
  final List<ScanPattern> scanPatterns;

  const Product({
    required this.id,
    required this.name,
    required this.sku,
    this.code,
    this.brandName,
    this.uomName,
    this.price,
    this.currentStock,
    this.scanPatterns = const [],
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    final rawPatterns = json['scan_patterns'];
    final patterns = (rawPatterns is List)
        ? rawPatterns
            .whereType<Map<String, dynamic>>()
            .map(ScanPattern.fromJson)
            .where((p) => p.isActive)
            .toList()
        : <ScanPattern>[];

    return Product(
      id: json['id'],
      name: json['name'],
      sku: json['sku'],
      code: json['code'],
      brandName: json['brand_name'],
      uomName: json['uom_name'],
      currentStock: (json['current_stock'] as num?)?.toDouble(),
      scanPatterns: patterns,
      price: json['price'] != null
          ? Price.fromJson(json['price'])
          : (json['last_price'] != null
              ? Price(amount: double.tryParse(json['last_price'].toString()) ?? 0.0, currency: json['currency'] ?? 'MXN')
              : null),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'sku': sku,
        'code': code,
        'brand_name': brandName,
        'uom_name': uomName,
        'current_stock': currentStock,
        'price': price?.toJson(),
      };

  @override
  List<Object?> get props => [id, name, sku, code, brandName, uomName, price, currentStock, scanPatterns];
}

class Price extends Equatable {
  final double amount;
  final String currency;

  const Price({required this.amount, required this.currency});

  factory Price.fromJson(Map<String, dynamic> json) {
    final rawAmount = json['amount'];
    double parsedAmount = 0.0;
    if (rawAmount is num) {
      parsedAmount = rawAmount.toDouble();
    } else if (rawAmount is String) {
      parsedAmount = double.tryParse(rawAmount) ?? 0.0;
    }
    return Price(
      amount: parsedAmount,
      currency: json['currency'] ?? 'MXN',
    );
  }

  Map<String, dynamic> toJson() => {
        'amount': amount,
        'currency': currency,
      };

  @override
  List<Object?> get props => [amount, currency];
}
