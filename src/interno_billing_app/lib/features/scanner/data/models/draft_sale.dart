import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/domain/entities/partner.dart';

class DraftSale {
  final List<CartItem> items;
  final Partner? selectedPartner;
  final String mode;

  DraftSale({
    required this.items,
    this.selectedPartner,
    required this.mode,
  });

  Map<String, dynamic> toJson() => {
        'items': items.map((e) => e.toJson()).toList(),
        'selectedPartner': selectedPartner?.toJson(),
        'mode': mode,
      };

  factory DraftSale.fromJson(Map<String, dynamic> json) {
    return DraftSale(
      items: (json['items'] as List?)
              ?.map((e) => CartItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      selectedPartner: json['selectedPartner'] != null
          ? Partner.fromJson(json['selectedPartner'] as Map<String, dynamic>)
          : null,
      mode: json['mode'] ?? 'sale',
    );
  }
}
