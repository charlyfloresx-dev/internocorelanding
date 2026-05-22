import 'package:dio/dio.dart';
import 'package:drift/drift.dart';
import 'package:interno_billing_app/core/database/local_database.dart';
import 'package:interno_billing_app/core/network/connectivity_service.dart';

/// ProductSyncService orchestrates the 3-phase sync protocol:
///   Phase A: Full Sync Bootstrap (initial login or manual trigger)
///   Phase B: Delta Sync (incremental updates every 15 min)
///   Phase C: On-Demand Cache (handled by ProductRepository on scan miss)
class ProductSyncService {
  final Dio _dio;
  final AppLocalDatabase _localDb;
  final ConnectivityService _connectivity;

  /// Maximum products per page during full sync to prevent PDA memory overflow.
  static const int _pageSize = 500;

  ProductSyncService(this._dio, this._localDb, this._connectivity);

  // ── Phase A: Full Sync Bootstrap ──────────────────────────────────────────

  /// Downloads the entire product catalog + base prices from the server.
  /// Replaces all local data atomically. Should be called on first login
  /// or via a manual "Force Sync" button.
  ///
  /// Returns the total count of synced products, or -1 on failure.
  Future<int> fullSync({void Function(int current, int total)? onProgress}) async {
    if (!await _connectivity.isConnected) return -1;

    try {
      int totalSynced = 0;
      int page = 1;
      bool hasMore = true;

      final allProducts = <LocalProductsCompanion>[];
      final allPrices = <LocalPricesCompanion>[];

      while (hasMore) {
        final response = await _dio.get(
          'products',
          queryParameters: {
            'limit': _pageSize,
            'page': page,
          },
        );

        if (response.data['status'] != 'success') break;

        final List items = response.data['data'] ?? [];
        final meta = response.data['meta'];
        final int totalItems = meta?['total'] ?? items.length;

        final now = DateTime.now().toIso8601String();

        for (final item in items) {
          allProducts.add(LocalProductsCompanion.insert(
            id: item['id'],
            name: item['name'] ?? '',
            sku: item['sku'] ?? '',
            code: Value(item['code']),
            brandName: Value(item['brand_name']),
            uomName: Value(item['uom_name']),
            currentStock: Value((item['current_stock'] as num?)?.toDouble() ?? 0.0),
            lastSynced: now,
          ));

          // Extract price from either nested object or flat fields
          final priceData = item['price'] ?? item['last_price'];
          if (priceData != null) {
            double? amount;
            String currency = item['currency'] ?? 'MXN';

            if (priceData is Map) {
              amount = (priceData['amount'] as num?)?.toDouble() ?? double.tryParse(priceData['amount']?.toString() ?? '');
              currency = priceData['currency'] ?? 'MXN';
            } else if (priceData is num) {
              amount = priceData.toDouble();
            } else {
              amount = double.tryParse(priceData.toString());
            }

            if (amount != null) {
              allPrices.add(LocalPricesCompanion.insert(
                productId: item['id'],
                amount: amount,
                currency: Value(currency),
              ));
            }
          }
        }

        totalSynced += items.length;
        onProgress?.call(totalSynced, totalItems);

        hasMore = items.length >= _pageSize;
        page++;
      }

      // Atomic replace — wipe old data and insert new
      if (allProducts.isNotEmpty) {
        await _localDb.fullSyncReplace(allProducts, allPrices);
      }

      return totalSynced;
    } catch (e) {
      print('ProductSyncService.fullSync error: $e');
      return -1;
    }
  }

  // ── Phase B: Delta Sync ───────────────────────────────────────────────────

  /// Refreshes the local catalog using the existing /products endpoint.
  ///
  /// The backend does not expose a /products/sync?since= endpoint yet.
  /// Until one is available, delta sync delegates to fullSync(), which is
  /// efficient for catalogs ≤5k SKUs (500-record pages, ~2-3s on Wi-Fi).
  ///
  /// When master_data_service adds GET /products?updated_since=, this method
  /// can be updated to do a true incremental diff without touching this call site.
  ///
  /// Returns the total count of synced products, or -1 on failure.
  Future<int> deltaSync() async {
    return await fullSync();
  }

  // ── Sync Status ───────────────────────────────────────────────────────────

  /// Returns a human-readable sync status for the UI indicator.
  Future<SyncStatus> getSyncStatus() async {
    final cachedCount = await _localDb.getCachedProductCount();
    final lastSync = await _localDb.getSyncCheckpoint('last_delta_sync')
        ?? await _localDb.getSyncCheckpoint('last_full_sync');

    DateTime? lastSyncDate;
    if (lastSync != null) {
      lastSyncDate = DateTime.tryParse(lastSync);
    }

    return SyncStatus(
      cachedProductCount: cachedCount,
      lastSyncDate: lastSyncDate,
      isStale: lastSyncDate == null ||
          DateTime.now().difference(lastSyncDate).inHours >= 24,
    );
  }
}

/// Sync status data class for UI display.
class SyncStatus {
  final int cachedProductCount;
  final DateTime? lastSyncDate;
  final bool isStale;

  const SyncStatus({
    required this.cachedProductCount,
    this.lastSyncDate,
    required this.isStale,
  });

  String get displayText {
    if (lastSyncDate == null) return 'Sin sincronizar';

    final diff = DateTime.now().difference(lastSyncDate!);
    if (diff.inMinutes < 1) return 'Hace un momento';
    if (diff.inMinutes < 60) return 'Hace ${diff.inMinutes} min';
    if (diff.inHours < 24) return 'Hace ${diff.inHours}h';
    return 'Hace ${diff.inDays} días';
  }
}
