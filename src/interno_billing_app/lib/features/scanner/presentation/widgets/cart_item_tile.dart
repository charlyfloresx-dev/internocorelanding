import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';
import 'package:interno_billing_app/domain/entities/cart_item.dart';
import 'package:interno_billing_app/features/scanner/presentation/bloc/scanner_bloc.dart';

class CartItemTile extends StatelessWidget {
  final CartItem item;

  const CartItemTile({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        children: [
          _buildQuantityBadge(context),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.product.name,
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                Text(
                  item.product.sku,
                  style: const TextStyle(color: Colors.white38, fontSize: 11),
                ),
              ],
            ),
          ),
          SizedBox(
            width: 90,
            child: Text(
              '\$${item.lineTotal.toStringAsFixed(2)}',
              textAlign: TextAlign.right,
              style: const TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.w900),
            ),
          ),
          const SizedBox(width: 8),
          IconButton(
            icon: const Icon(Icons.remove_circle_outline, color: Colors.white24, size: 20),
            onPressed: () => context.read<ScannerBloc>().add(RemoveItem(item.product.id)),
          ),
        ],
      ),
    );
  }

  Widget _buildQuantityBadge(BuildContext context) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: InternoColors.cyan.withOpacity(0.1),
        shape: BoxShape.circle,
      ),
      child: Center(
        child: Text(
          '${item.quantity}',
          style: const TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.w900),
        ),
      ),
    );
  }
}
