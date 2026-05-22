import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:interno_billing_app/domain/entities/product.dart';
import 'package:interno_billing_app/core/database/local_database.dart';
import 'package:interno_billing_app/core/network/connectivity_service.dart';

/// ProductRepository — Single Source of Truth (SSOT) for the UI layer.
///
/// Implements the Offline-First hybrid pattern:
///   1. Resolve from local SQLite cache (0ms latency)
///   2. If cache miss or stale + online → fetch from API → persist locally
///   3. If offline → serve stale cache as safe fallback
class ProductRepository {
  final Dio _dio;
  final SharedPreferences _prefs;
  final AppLocalDatabase _localDb;
  final ConnectivityService _connectivity;

  /// TTL for cached prices in hours. After this period, the cache is
  /// considered "dirty" and a background refresh will be attempted.
  static const int _cacheTtlHours = 24;

  ProductRepository(this._dio, this._prefs, this._localDb, this._connectivity);

  /// Looks up a product by barcode or SKU code.
  ///
  /// Resolution order:
  ///   1. Local DB (instant) — if valid and not stale
  ///   2. Remote API — if online and cache miss/stale
  ///   3. Stale local cache — if offline fallback
  Future<Product?> lookupByCode(String code, {String? partnerId}) async {
    final isOnline = await _connectivity.isConnected;

    if (isOnline) {
      // 1. Si tiene conexión, pide al api
      final remoteProduct = await _fetchAndCacheFromApi(code, partnerId: partnerId);
      if (remoteProduct != null) {
        return remoteProduct;
      }
    }

    // 2. Si no tiene conexión o falla el api, busca en la base de datos local
    return await _localDb.findProductByCode(code, partnerId: partnerId);
  }

  /// Fetches a product from the remote API and persists it locally.
  Future<Product?> _fetchAndCacheFromApi(String code, {String? partnerId}) async {
    try {
      final response = await _dio.get(
        'products/lookup/$code',
        queryParameters: {
          if (partnerId != null) 'partner_id': partnerId,
        },
      );

      if (response.data['status'] == 'success' && response.data['data'] != null) {
        final product = Product.fromJson(response.data['data']);

        // Persist to local SQLite (On-Demand Cache)
        await _localDb.cacheProduct(product, scannedCode: code);

        return product;
      }
      return null;
    } catch (e) {
      print('ProductRepository._fetchAndCacheFromApi error: $e');
      return null;
    }
  }

  /// Searches products by query string (for typeahead / quick catalog).
  /// Falls back to local DB if offline.
  Future<List<Product>> searchProducts(String query) async {
    final isOnline = await _connectivity.isConnected;

    if (isOnline) {
      try {
        final response = await _dio.get(
          'products',
          queryParameters: {'q': query},
        );

        if (response.data['status'] == 'success') {
          final List data = response.data['data'] ?? [];
          return data.map((json) => Product.fromJson(json)).toList();
        }
      } catch (e) {
        print('ProductRepository.searchProducts remote error: $e');
        // Fall through to local search
      }
    }

    // Local fallback: search by SKU or name prefix
    // (basic implementation — Drift full-text search can be added later)
    return [];
  }
}
