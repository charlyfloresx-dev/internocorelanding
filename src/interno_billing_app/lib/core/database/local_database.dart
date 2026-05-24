import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:interno_billing_app/domain/entities/product.dart';

part 'local_database.g.dart';

// ══════════════════════════════════════════════════════════════════════════════
// TABLE DEFINITIONS — Offline Product Catalog & Onion Pricing
// ══════════════════════════════════════════════════════════════════════════════

/// Local cache of products synced from master-data-service.
class LocalProducts extends Table {
  TextColumn get id => text()();             // UUID from backend
  TextColumn get name => text()();
  TextColumn get sku => text()();            // Industrial SKU code
  TextColumn get code => text().nullable()(); // Barcode (EAN/UPC)
  TextColumn get brandName => text().nullable()();
  TextColumn get uomName => text().nullable()();
  RealColumn get currentStock => real().withDefault(const Constant(0.0))();
  TextColumn get lastSynced => text()();     // ISO8601 timestamp

  @override
  Set<Column> get primaryKey => {id};
}

/// Local cache of resolved prices (supports Onion Pricing per partner).
class LocalPrices extends Table {
  IntColumn get rowId => integer().nullable().autoIncrement()();
  TextColumn get productId => text()();
  RealColumn get amount => real()();
  TextColumn get currency => text().withDefault(const Constant('MXN'))();
  TextColumn get partnerId => text().nullable()(); // Specific customer price
  TextColumn get validUntil => text().nullable()();
}

/// Sync checkpoint metadata for delta sync protocol.
class SyncCheckpoints extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

// ══════════════════════════════════════════════════════════════════════════════
// DATABASE CLASS
// ══════════════════════════════════════════════════════════════════════════════

@DriftDatabase(tables: [LocalProducts, LocalPrices, SyncCheckpoints])
class AppLocalDatabase extends _$AppLocalDatabase {
  AppLocalDatabase() : super(_openConnection());

  // For testing
  AppLocalDatabase.forTesting(super.e);

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (m) async {
          await m.createAll();
        },
        onUpgrade: (m, from, to) async {
          // Recrear las tablas locales de SQLite en caso de cambios de esquema durante desarrollo
          for (final table in allTables) {
            await m.deleteTable(table.actualTableName);
          }
          await m.createAll();
        },
      );

  // ── Bulk Upsert (Full Sync & Delta Sync) ────────────────────────────────

  /// Atomically inserts or updates a batch of products and their prices.
  /// Uses Drift's batch API to avoid main-thread blocking on PDA devices.
  Future<void> saveProductsWithPrices(
    List<LocalProductsCompanion> products,
    List<LocalPricesCompanion> prices,
  ) async {
    await batch((b) {
      b.insertAllOnConflictUpdate(localProducts, products);
      for (final price in prices) {
        b.insert(localPrices, price, mode: InsertMode.insertOrReplace);
      }
    });
  }

  /// Save a single product + price from on-demand cache (scanner lookup).
  Future<void> cacheProduct(Product product, {String? scannedCode}) async {
    final now = DateTime.now().toIso8601String();
    await into(localProducts).insertOnConflictUpdate(
      LocalProductsCompanion.insert(
        id: product.id,
        name: product.name,
        sku: product.sku,
        code: Value(scannedCode ?? product.code),
        brandName: Value(product.brandName),
        uomName: Value(product.uomName),
        currentStock: Value(product.currentStock ?? 0.0),
        lastSynced: now,
      ),
    );

    if (product.price != null) {
      // Delete existing base price for this product, then insert fresh
      await (delete(localPrices)
            ..where((t) => t.productId.equals(product.id) & t.partnerId.isNull()))
          .go();
      await into(localPrices).insert(
        LocalPricesCompanion.insert(
          productId: product.id,
          amount: product.price!.amount,
          currency: Value(product.price!.currency),
        ),
      );
    }
  }

  // ── Lookup Queries ──────────────────────────────────────────────────────

  /// Finds a product by barcode or SKU, with optional partner-specific pricing.
  /// Returns null if not found. Priority: partner price > base price.
  Future<Product?> findProductByCode(String code, {String? partnerId}) async {
    final query = select(localProducts).join([
      leftOuterJoin(
        localPrices,
        localPrices.productId.equalsExp(localProducts.id),
      ),
    ]);

    query.where(localProducts.code.equals(code) | localProducts.sku.equals(code));

    final rows = await query.get();
    if (rows.isEmpty) return null;

    // Find the best matching row: partner-specific price first, then base price
    TypedResult? bestRow;
    for (final row in rows) {
      final pricePartnerId = row.readTableOrNull(localPrices)?.partnerId;
      if (partnerId != null && pricePartnerId == partnerId) {
        bestRow = row;
        break; // Exact partner match — highest priority
      }
      if (pricePartnerId == null) {
        bestRow ??= row; // Base price fallback
      }
    }

    bestRow ??= rows.first;

    final productRow = bestRow.readTable(localProducts);
    final priceRow = bestRow.readTableOrNull(localPrices);

    return Product(
      id: productRow.id,
      name: productRow.name,
      sku: productRow.sku,
      code: productRow.code,
      brandName: productRow.brandName,
      uomName: productRow.uomName,
      currentStock: productRow.currentStock,
      price: priceRow != null
          ? Price(amount: priceRow.amount, currency: priceRow.currency)
          : null,
    );
  }

  /// Retrieves all cached products with their resolved prices.
  Future<List<Product>> getAllProducts({String? partnerId}) async {
    final query = select(localProducts).join([
      leftOuterJoin(
        localPrices,
        localPrices.productId.equalsExp(localProducts.id),
      ),
    ]);

    final rows = await query.get();
    if (rows.isEmpty) return [];

    // Group rows by product to resolve prices
    final Map<String, List<TypedResult>> grouped = {};
    for (final row in rows) {
      final product = row.readTable(localProducts);
      grouped.putIfAbsent(product.id, () => []).add(row);
    }

    final List<Product> result = [];
    for (final entry in grouped.entries) {
      final productRows = entry.value;
      
      TypedResult? bestRow;
      for (final row in productRows) {
        final pricePartnerId = row.readTableOrNull(localPrices)?.partnerId;
        if (partnerId != null && pricePartnerId == partnerId) {
          bestRow = row;
          break; // Exact partner match
        }
        if (pricePartnerId == null) {
          bestRow ??= row; // Base price fallback
        }
      }
      bestRow ??= productRows.first;

      final productRow = bestRow.readTable(localProducts);
      final priceRow = bestRow.readTableOrNull(localPrices);

      result.add(Product(
        id: productRow.id,
        name: productRow.name,
        sku: productRow.sku,
        code: productRow.code,
        brandName: productRow.brandName,
        uomName: productRow.uomName,
        currentStock: productRow.currentStock,
        price: priceRow != null
            ? Price(amount: priceRow.amount, currency: priceRow.currency)
            : null,
      ));
    }

    return result;
  }


  /// Check if cache entry is stale (older than TTL hours).
  Future<bool> isCacheStale(String code, {int ttlHours = 24}) async {
    final row = await (select(localProducts)
          ..where((t) => t.code.equals(code) | t.sku.equals(code)))
        .getSingleOrNull();

    if (row == null) return true;

    final lastSynced = DateTime.tryParse(row.lastSynced);
    if (lastSynced == null) return true;

    return DateTime.now().difference(lastSynced).inHours >= ttlHours;
  }

  // ── Full Sync Bootstrap ─────────────────────────────────────────────────

  /// Replaces the entire local catalog with fresh data from the server.
  /// Used during initial login or manual "Force Sync".
  Future<void> fullSyncReplace(
    List<LocalProductsCompanion> products,
    List<LocalPricesCompanion> prices,
  ) async {
    await transaction(() async {
      await delete(localPrices).go();
      await delete(localProducts).go();
      await batch((b) {
        b.insertAllOnConflictUpdate(localProducts, products);
        b.insertAll(localPrices, prices); // table cleared above — no conflict possible
      });
      // Save sync checkpoints
      final nowStr = DateTime.now().toIso8601String();
      await into(syncCheckpoints).insertOnConflictUpdate(
        SyncCheckpointsCompanion.insert(
          key: 'last_full_sync',
          value: nowStr,
        ),
      );
      await into(syncCheckpoints).insertOnConflictUpdate(
        SyncCheckpointsCompanion.insert(
          key: 'last_delta_sync',
          value: nowStr,
        ),
      );
    });
  }

  /// Delete discontinued products (used during delta sync).
  Future<void> deleteProductsByIds(List<String> ids) async {
    if (ids.isEmpty) return;
    await (delete(localProducts)..where((t) => t.id.isIn(ids))).go();
    // Prices cascade-delete via app logic (Drift doesn't support FK cascades natively on all platforms)
    await (delete(localPrices)..where((t) => t.productId.isIn(ids))).go();
  }

  // ── Sync Checkpoint Management ──────────────────────────────────────────

  Future<String?> getSyncCheckpoint(String key) async {
    final row = await (select(syncCheckpoints)
          ..where((t) => t.key.equals(key)))
        .getSingleOrNull();
    return row?.value;
  }

  Future<void> setSyncCheckpoint(String key, String value) async {
    await into(syncCheckpoints).insertOnConflictUpdate(
      SyncCheckpointsCompanion.insert(key: key, value: value),
    );
  }

  // ── Stats / Debug ───────────────────────────────────────────────────────

  /// Returns the count of cached products (for UI sync status indicator).
  Future<int> getCachedProductCount() async {
    final count = localProducts.id.count();
    final query = selectOnly(localProducts)..addColumns([count]);
    final row = await query.getSingle();
    return row.read(count) ?? 0;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// DATABASE CONNECTION (Background Isolate for PDA performance)
// ══════════════════════════════════════════════════════════════════════════════

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'interno_billing_local_v4.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
