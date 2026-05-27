import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';

/// Glove-friendly cart item row — spec: uber_pos_layout.md §3 & §3(Tactile)
/// Icons.remove_circle / add_circle size 30, touch target 44×44, qty fontSize 18.
/// Pure black/white monochrome palette — no color accents.
class CartItemTile extends StatelessWidget {
  final CartItem item;

  const CartItemTile({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
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
          // Product name + code
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.product.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  item.product.code ?? item.product.sku,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white38,
                    fontSize: 11,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
          ),
          // Line total
          SizedBox(
            width: 90,
            child: Text(
              '\$${item.lineTotal.toStringAsFixed(2)}',
              textAlign: TextAlign.right,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 15,
              ),
            ),
          ),
          const SizedBox(width: 16),
          // Quantity controls — spec: minWidth/minHeight 44, icon size 30
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.remove_circle, color: Colors.white54, size: 30),
                onPressed: () {
                  HapticFeedback.selectionClick();
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
                child: Text(
                  '${item.quantity}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.add_circle, color: Colors.white, size: 30),
                onPressed: () {
                  HapticFeedback.selectionClick();
                  context.read<ScannerBloc>().add(
                    UpdateQuantity(item.product.id, item.quantity + 1),
                  );
                },
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
