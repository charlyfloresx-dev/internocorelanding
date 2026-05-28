import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:interno_billing_app/core/di/injection.dart';
import 'package:interno_billing_app/core/theme/app_theme.dart';

class InventoryStockScreen extends StatefulWidget {
  const InventoryStockScreen({super.key});

  @override
  State<InventoryStockScreen> createState() => _InventoryStockScreenState();
}

class _InventoryStockScreenState extends State<InventoryStockScreen> {
  List<Map<String, dynamic>> _stockItems = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchStock();
  }

  Future<void> _fetchStock() async {
    try {
      final dio = sl<Dio>();
      final prefs = sl<SharedPreferences>();
      final companyId = prefs.getString('company_id') ?? '';

      final response = await dio.get(
        'inventory/stock',
        queryParameters: {'company_id': companyId},
      );

      if (response.data['status'] == 'success') {
        setState(() {
          _stockItems = List<Map<String, dynamic>>.from(response.data['data']);
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final scaffoldBg = Theme.of(context).scaffoldBackgroundColor;
    final cardBg = Theme.of(context).cardColor;

    return Scaffold(
      backgroundColor: scaffoldBg,
      appBar: AppBar(
        backgroundColor: scaffoldBg,
        title: Text(
          'inventory.title'.tr(),
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w900, letterSpacing: 2),
        ),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator(color: InternoColors.cyan))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _stockItems.length,
              itemBuilder: (context, index) {
                return _buildStockCard(_stockItems[index], cs, cardBg);
              },
            ),
    );
  }

  Widget _buildStockCard(Map<String, dynamic> item, ColorScheme cs, Color cardBg) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: cs.onSurface.withValues(alpha: 0.08)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: InternoColors.cyan.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  item['sku'] ?? 'N/A',
                  style: const TextStyle(color: InternoColors.cyan, fontWeight: FontWeight.bold, fontSize: 12),
                ),
              ),
              Text(
                '${item['total_available_qty']} ${'inventory.available'.tr()}',
                style: TextStyle(color: cs.onSurface, fontWeight: FontWeight.w900, fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            item['product_name'] ?? '',
            style: TextStyle(color: cs.onSurface.withValues(alpha: 0.7), fontSize: 14, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          Divider(color: cs.onSurface.withValues(alpha: 0.08)),
          const SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.description_outlined, color: cs.onSurface.withValues(alpha: 0.38), size: 14),
              const SizedBox(width: 8),
              Text(
                '${'inventory.pedimento'.tr()}: ${item['pedimento_number']}',
                style: TextStyle(color: cs.onSurface.withValues(alpha: 0.38), fontSize: 11),
              ),
            ],
          ),
          if (item['expiry_date'] != null) ...[
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.event_note, color: cs.onSurface.withValues(alpha: 0.38), size: 14),
                const SizedBox(width: 8),
                Text(
                  '${'inventory.expires'.tr()}: ${item['expiry_date'].toString().split('T')[0]} (${item['days_to_expiry']} días)',
                  style: TextStyle(
                    color: item['is_at_risk'] == true ? Colors.red : cs.onSurface.withValues(alpha: 0.38),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
