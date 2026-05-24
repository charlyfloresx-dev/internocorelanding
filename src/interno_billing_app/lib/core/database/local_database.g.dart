// GENERATED CODE - DO NOT MODIFY BY HAND
// Generated manually due to build_runner AOT hook incompatibility with Dart 3.10+

part of 'local_database.dart';

// ══════════════════════════════════════════════════════════════════════════════
// DATA CLASSES
// ══════════════════════════════════════════════════════════════════════════════

class LocalProduct extends DataClass implements Insertable<LocalProduct> {
  final String id;
  final String name;
  final String sku;
  final String? code;
  final String? brandName;
  final String? uomName;
  final double currentStock;
  final String lastSynced;

  const LocalProduct({
    required this.id,
    required this.name,
    required this.sku,
    this.code,
    this.brandName,
    this.uomName,
    required this.currentStock,
    required this.lastSynced,
  });

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    map['sku'] = Variable<String>(sku);
    if (!nullToAbsent || code != null) map['code'] = Variable<String>(code);
    if (!nullToAbsent || brandName != null) map['brand_name'] = Variable<String>(brandName);
    if (!nullToAbsent || uomName != null) map['uom_name'] = Variable<String>(uomName);
    map['current_stock'] = Variable<double>(currentStock);
    map['last_synced'] = Variable<String>(lastSynced);
    return map;
  }

  factory LocalProduct.fromData(Map<String, dynamic> data, {String? prefix}) {
    final p = prefix ?? '';
    return LocalProduct(
      id: data['${p}id'] as String,
      name: data['${p}name'] as String,
      sku: data['${p}sku'] as String,
      code: data['${p}code'] as String?,
      brandName: data['${p}brand_name'] as String?,
      uomName: data['${p}uom_name'] as String?,
      currentStock: data['${p}current_stock'] as double,
      lastSynced: data['${p}last_synced'] as String,
    );
  }

  LocalProduct copyWith({
    String? id, String? name, String? sku, Value<String?> code = const Value.absent(),
    Value<String?> brandName = const Value.absent(), Value<String?> uomName = const Value.absent(),
    double? currentStock, String? lastSynced,
  }) {
    return LocalProduct(
      id: id ?? this.id, name: name ?? this.name, sku: sku ?? this.sku,
      code: code.present ? code.value : this.code,
      brandName: brandName.present ? brandName.value : this.brandName,
      uomName: uomName.present ? uomName.value : this.uomName,
      currentStock: currentStock ?? this.currentStock,
      lastSynced: lastSynced ?? this.lastSynced,
    );
  }

  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return {
      'id': serializer.toJson<String>(id), 'name': serializer.toJson<String>(name),
      'sku': serializer.toJson<String>(sku), 'code': serializer.toJson<String?>(code),
      'brandName': serializer.toJson<String?>(brandName), 'uomName': serializer.toJson<String?>(uomName),
      'currentStock': serializer.toJson<double>(currentStock), 'lastSynced': serializer.toJson<String>(lastSynced),
    };
  }

  @override
  String toString() => 'LocalProduct(id: $id, name: $name, sku: $sku)';
  @override
  int get hashCode => Object.hash(id, name, sku, code, brandName, uomName, currentStock, lastSynced);
  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is LocalProduct && other.id == id && other.name == name &&
          other.sku == sku && other.code == code && other.brandName == brandName &&
          other.uomName == uomName && other.currentStock == currentStock && other.lastSynced == lastSynced);
}

class LocalProductsCompanion extends UpdateCompanion<LocalProduct> {
  final Value<String> id;
  final Value<String> name;
  final Value<String> sku;
  final Value<String?> code;
  final Value<String?> brandName;
  final Value<String?> uomName;
  final Value<double> currentStock;
  final Value<String> lastSynced;

  const LocalProductsCompanion({
    this.id = const Value.absent(), this.name = const Value.absent(),
    this.sku = const Value.absent(), this.code = const Value.absent(),
    this.brandName = const Value.absent(), this.uomName = const Value.absent(),
    this.currentStock = const Value.absent(), this.lastSynced = const Value.absent(),
  });

  LocalProductsCompanion.insert({
    required String id, required String name, required String sku,
    this.code = const Value.absent(), this.brandName = const Value.absent(),
    this.uomName = const Value.absent(), this.currentStock = const Value.absent(),
    required String lastSynced,
  })  : id = Value(id), name = Value(name), sku = Value(sku), lastSynced = Value(lastSynced);

  static Insertable<LocalProduct> custom({
    Expression<String>? id, Expression<String>? name, Expression<String>? sku,
    Expression<String>? code, Expression<String>? brandName, Expression<String>? uomName,
    Expression<double>? currentStock, Expression<String>? lastSynced,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id, if (name != null) 'name': name, if (sku != null) 'sku': sku,
      if (code != null) 'code': code, if (brandName != null) 'brand_name': brandName,
      if (uomName != null) 'uom_name': uomName, if (currentStock != null) 'current_stock': currentStock,
      if (lastSynced != null) 'last_synced': lastSynced,
    });
  }

  LocalProductsCompanion copyWith({
    Value<String>? id, Value<String>? name, Value<String>? sku,
    Value<String?>? code, Value<String?>? brandName, Value<String?>? uomName,
    Value<double>? currentStock, Value<String>? lastSynced,
  }) {
    return LocalProductsCompanion(
      id: id ?? this.id, name: name ?? this.name, sku: sku ?? this.sku,
      code: code ?? this.code, brandName: brandName ?? this.brandName,
      uomName: uomName ?? this.uomName, currentStock: currentStock ?? this.currentStock,
      lastSynced: lastSynced ?? this.lastSynced,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) map['id'] = Variable<String>(id.value);
    if (name.present) map['name'] = Variable<String>(name.value);
    if (sku.present) map['sku'] = Variable<String>(sku.value);
    if (code.present) map['code'] = Variable<String>(code.value);
    if (brandName.present) map['brand_name'] = Variable<String>(brandName.value);
    if (uomName.present) map['uom_name'] = Variable<String>(uomName.value);
    if (currentStock.present) map['current_stock'] = Variable<double>(currentStock.value);
    if (lastSynced.present) map['last_synced'] = Variable<String>(lastSynced.value);
    return map;
  }

  @override
  String toString() => 'LocalProductsCompanion(id: $id, name: $name, sku: $sku)';
}

class LocalPrice extends DataClass implements Insertable<LocalPrice> {
  final int? rowId;
  final String productId;
  final double amount;
  final String currency;
  final String? partnerId;
  final String? validUntil;

  const LocalPrice({
    this.rowId, required this.productId, required this.amount,
    required this.currency, this.partnerId, this.validUntil,
  });

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (rowId != null) map['row_id'] = Variable<int>(rowId!);
    map['product_id'] = Variable<String>(productId);
    map['amount'] = Variable<double>(amount);
    map['currency'] = Variable<String>(currency);
    if (!nullToAbsent || partnerId != null) map['partner_id'] = Variable<String>(partnerId);
    if (!nullToAbsent || validUntil != null) map['valid_until'] = Variable<String>(validUntil);
    return map;
  }

  factory LocalPrice.fromData(Map<String, dynamic> data, {String? prefix}) {
    final p = prefix ?? '';
    return LocalPrice(
      rowId: data['${p}row_id'] as int?,
      productId: data['${p}product_id'] as String,
      amount: data['${p}amount'] as double,
      currency: data['${p}currency'] as String,
      partnerId: data['${p}partner_id'] as String?,
      validUntil: data['${p}valid_until'] as String?,
    );
  }

  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return {
      'rowId': serializer.toJson<int?>(rowId), 'productId': serializer.toJson<String>(productId),
      'amount': serializer.toJson<double>(amount), 'currency': serializer.toJson<String>(currency),
      'partnerId': serializer.toJson<String?>(partnerId), 'validUntil': serializer.toJson<String?>(validUntil),
    };
  }

  @override
  String toString() => 'LocalPrice(rowId: $rowId, productId: $productId, amount: $amount)';
  @override
  int get hashCode => Object.hash(rowId, productId, amount, currency, partnerId, validUntil);
  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is LocalPrice && other.rowId == rowId &&
          other.productId == productId && other.amount == amount && other.currency == currency &&
          other.partnerId == partnerId && other.validUntil == validUntil);
}

class LocalPricesCompanion extends UpdateCompanion<LocalPrice> {
  final Value<int> rowId;
  final Value<String> productId;
  final Value<double> amount;
  final Value<String> currency;
  final Value<String?> partnerId;
  final Value<String?> validUntil;

  const LocalPricesCompanion({
    this.rowId = const Value.absent(), this.productId = const Value.absent(),
    this.amount = const Value.absent(), this.currency = const Value.absent(),
    this.partnerId = const Value.absent(), this.validUntil = const Value.absent(),
  });

  LocalPricesCompanion.insert({
    this.rowId = const Value.absent(), required String productId, required double amount,
    this.currency = const Value.absent(), this.partnerId = const Value.absent(),
    this.validUntil = const Value.absent(),
  })  : productId = Value(productId), amount = Value(amount);

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (rowId.present) map['row_id'] = Variable<int>(rowId.value);
    if (productId.present) map['product_id'] = Variable<String>(productId.value);
    if (amount.present) map['amount'] = Variable<double>(amount.value);
    if (currency.present) map['currency'] = Variable<String>(currency.value);
    if (partnerId.present) map['partner_id'] = Variable<String>(partnerId.value);
    if (validUntil.present) map['valid_until'] = Variable<String>(validUntil.value);
    return map;
  }

  @override
  String toString() => 'LocalPricesCompanion(productId: $productId, amount: $amount)';
}

class SyncCheckpoint extends DataClass implements Insertable<SyncCheckpoint> {
  final String key;
  final String value;
  const SyncCheckpoint({required this.key, required this.value});

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    return {'key': Variable<String>(key), 'value': Variable<String>(value)};
  }

  factory SyncCheckpoint.fromData(Map<String, dynamic> data, {String? prefix}) {
    final p = prefix ?? '';
    return SyncCheckpoint(key: data['${p}key'] as String, value: data['${p}value'] as String);
  }

  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return {'key': serializer.toJson<String>(key), 'value': serializer.toJson<String>(value)};
  }

  @override
  String toString() => 'SyncCheckpoint(key: $key, value: $value)';
  @override
  int get hashCode => Object.hash(key, value);
  @override
  bool operator ==(Object other) =>
      identical(this, other) || (other is SyncCheckpoint && other.key == key && other.value == value);
}

class SyncCheckpointsCompanion extends UpdateCompanion<SyncCheckpoint> {
  final Value<String> key;
  final Value<String> value;
  const SyncCheckpointsCompanion({this.key = const Value.absent(), this.value = const Value.absent()});

  SyncCheckpointsCompanion.insert({required String key, required String value})
      : key = Value(key), value = Value(value);

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (key.present) map['key'] = Variable<String>(key.value);
    if (value.present) map['value'] = Variable<String>(value.value);
    return map;
  }
}

// ══════════════════════════════════════════════════════════════════════════════
// TABLE IMPLEMENTATIONS
// ══════════════════════════════════════════════════════════════════════════════

class $LocalProductsTable extends LocalProducts with TableInfo<$LocalProductsTable, LocalProduct> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalProductsTable(this.attachedDatabase, [this._alias]);

  final VerificationMeta _idMeta = const VerificationMeta('id');
  late final GeneratedColumn<String> id = GeneratedColumn<String>('id', aliasedName, false, type: DriftSqlType.string);
  final VerificationMeta _nameMeta = const VerificationMeta('name');
  late final GeneratedColumn<String> name = GeneratedColumn<String>('name', aliasedName, false, type: DriftSqlType.string);
  final VerificationMeta _skuMeta = const VerificationMeta('sku');
  late final GeneratedColumn<String> sku = GeneratedColumn<String>('sku', aliasedName, false, type: DriftSqlType.string);
  final VerificationMeta _codeMeta = const VerificationMeta('code');
  late final GeneratedColumn<String> code = GeneratedColumn<String>('code', aliasedName, true, type: DriftSqlType.string);
  final VerificationMeta _brandNameMeta = const VerificationMeta('brandName');
  late final GeneratedColumn<String> brandName = GeneratedColumn<String>('brand_name', aliasedName, true, type: DriftSqlType.string);
  final VerificationMeta _uomNameMeta = const VerificationMeta('uomName');
  late final GeneratedColumn<String> uomName = GeneratedColumn<String>('uom_name', aliasedName, true, type: DriftSqlType.string);
  final VerificationMeta _currentStockMeta = const VerificationMeta('currentStock');
  late final GeneratedColumn<double> currentStock = GeneratedColumn<double>('current_stock', aliasedName, false, type: DriftSqlType.double, defaultValue: const Constant(0.0));
  final VerificationMeta _lastSyncedMeta = const VerificationMeta('lastSynced');
  late final GeneratedColumn<String> lastSynced = GeneratedColumn<String>('last_synced', aliasedName, false, type: DriftSqlType.string);

  @override
  List<GeneratedColumn> get $columns => [id, name, sku, code, brandName, uomName, currentStock, lastSynced];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => 'local_products';
  @override
  VerificationContext validateIntegrity(Insertable<LocalProduct> instance, {bool isInserting = false}) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    if (data.containsKey('name')) context.handle(_nameMeta, name.isAcceptableOrUnknown(data['name']!, _nameMeta));
    if (data.containsKey('sku')) context.handle(_skuMeta, sku.isAcceptableOrUnknown(data['sku']!, _skuMeta));
    if (data.containsKey('code')) context.handle(_codeMeta, code.isAcceptableOrUnknown(data['code']!, _codeMeta));
    if (data.containsKey('brand_name')) context.handle(_brandNameMeta, brandName.isAcceptableOrUnknown(data['brand_name']!, _brandNameMeta));
    if (data.containsKey('uom_name')) context.handle(_uomNameMeta, uomName.isAcceptableOrUnknown(data['uom_name']!, _uomNameMeta));
    if (data.containsKey('current_stock')) context.handle(_currentStockMeta, currentStock.isAcceptableOrUnknown(data['current_stock']!, _currentStockMeta));
    if (data.containsKey('last_synced')) context.handle(_lastSyncedMeta, lastSynced.isAcceptableOrUnknown(data['last_synced']!, _lastSyncedMeta));
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  LocalProduct map(Map<String, dynamic> data, {String? tablePrefix}) => LocalProduct.fromData(data, prefix: tablePrefix != null ? '$tablePrefix.' : null);
  @override
  $LocalProductsTable createAlias(String alias) => $LocalProductsTable(attachedDatabase, alias);
}

class $LocalPricesTable extends LocalPrices with TableInfo<$LocalPricesTable, LocalPrice> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalPricesTable(this.attachedDatabase, [this._alias]);

  late final GeneratedColumn<int> rowId = GeneratedColumn<int>('row_id', aliasedName, true, type: DriftSqlType.int, hasAutoIncrement: true);
  late final GeneratedColumn<String> productId = GeneratedColumn<String>('product_id', aliasedName, false, type: DriftSqlType.string);
  late final GeneratedColumn<double> amount = GeneratedColumn<double>('amount', aliasedName, false, type: DriftSqlType.double);
  late final GeneratedColumn<String> currency = GeneratedColumn<String>('currency', aliasedName, false, type: DriftSqlType.string, defaultValue: const Constant('MXN'));
  late final GeneratedColumn<String> partnerId = GeneratedColumn<String>('partner_id', aliasedName, true, type: DriftSqlType.string);
  late final GeneratedColumn<String> validUntil = GeneratedColumn<String>('valid_until', aliasedName, true, type: DriftSqlType.string);

  @override
  List<GeneratedColumn> get $columns => [rowId, productId, amount, currency, partnerId, validUntil];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => 'local_prices';
  @override
  VerificationContext validateIntegrity(Insertable<LocalPrice> instance, {bool isInserting = false}) => VerificationContext();
  @override
  Set<GeneratedColumn> get $primaryKey => {rowId};
  @override
  LocalPrice map(Map<String, dynamic> data, {String? tablePrefix}) => LocalPrice.fromData(data, prefix: tablePrefix != null ? '$tablePrefix.' : null);
  @override
  $LocalPricesTable createAlias(String alias) => $LocalPricesTable(attachedDatabase, alias);
}

class $SyncCheckpointsTable extends SyncCheckpoints with TableInfo<$SyncCheckpointsTable, SyncCheckpoint> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncCheckpointsTable(this.attachedDatabase, [this._alias]);

  late final GeneratedColumn<String> key = GeneratedColumn<String>('key', aliasedName, false, type: DriftSqlType.string);
  late final GeneratedColumn<String> value = GeneratedColumn<String>('value', aliasedName, false, type: DriftSqlType.string);

  @override
  List<GeneratedColumn> get $columns => [key, value];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => 'sync_checkpoints';
  @override
  VerificationContext validateIntegrity(Insertable<SyncCheckpoint> instance, {bool isInserting = false}) => VerificationContext();
  @override
  Set<GeneratedColumn> get $primaryKey => {key};
  @override
  SyncCheckpoint map(Map<String, dynamic> data, {String? tablePrefix}) => SyncCheckpoint.fromData(data, prefix: tablePrefix != null ? '$tablePrefix.' : null);
  @override
  $SyncCheckpointsTable createAlias(String alias) => $SyncCheckpointsTable(attachedDatabase, alias);
}

// ══════════════════════════════════════════════════════════════════════════════
// DATABASE MIXIN
// ══════════════════════════════════════════════════════════════════════════════

abstract class _$AppLocalDatabase extends GeneratedDatabase {
  _$AppLocalDatabase(QueryExecutor e) : super(e);

  late final $LocalProductsTable localProducts = $LocalProductsTable(this);
  late final $LocalPricesTable localPrices = $LocalPricesTable(this);
  late final $SyncCheckpointsTable syncCheckpoints = $SyncCheckpointsTable(this);

  @override
  Iterable<TableInfo<Table, dynamic>> get allTables => allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [localProducts, localPrices, syncCheckpoints];
}
