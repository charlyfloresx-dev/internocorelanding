# Plan de Sincronización y Caché de Productos — Interno Billing App
**Última actualización:** 2026-05-19 (revisión post-análisis de código)

---

## Estado de Implementación

| Componente | Estado | Notas |
|---|---|---|
| Drift schema (3 tablas) | ✅ Completo | `local_database.dart` |
| Phase A — Full Sync Bootstrap (paginado 500) | ✅ Completo | `product_sync_service.dart` |
| Phase B — Delta Sync | ⚠️ Parcial | Ve sección §3B — endpoint backend ausente, estrategia revisada |
| Phase C — On-Demand Cache en scan miss | ✅ Completo | `product_repository.dart` |
| Onion Pricing (partner-specific price priority) | ✅ Completo | `local_database.findProductByCode(partnerId)` |
| TTL 24h stale check | ✅ Completo | `local_database.isCacheStale()` |
| Sync status indicator UI | ✅ Completo | `sales_screen.dart` (pill con SKUs + timestamp) |
| Auto-sync al abrir pantalla si stale | ✅ Completo | `sales_screen._autoSyncIfNeeded()` |
| Loading screen sync inicial | ❌ Faltante | Ve §4.5 |
| Workmanager background sync | ⏳ Deferred | Pendiente junto con notificaciones push |
| Flujo Ventas (ScannerMode.sale) | ✅ Completo | → `PaymentConfirmationScreen` → `POST /pos/checkout` |
| Flujo Entradas (ScannerMode.entry) | ✅ Completo | → `POST /inventory/documents` tipo IN / TRANSFER |
| Carrito unificado en BLoC | ❌ Faltante | `sales_screen.dart` tiene doble estado (Ve Bug B1) |
| Búsqueda offline local | ❌ Faltante | `searchProducts()` retorna `[]` offline |
| Stock actual desde inventory_service | ❌ Faltante | Ve §3D |

---

## 1. Arquitectura Tecnológica

```
Motor DB Local : Drift (SQLite reactivo) — relaciones + índices para Onion Pricing
Conectividad   : ConnectivityPlus (ya integrado via ConnectivityService)
Background Sync: [DEFERRED] Workmanager — pendiente junto con módulo notificaciones
Estrategia     : Online-First (API → cache en miss/stale) — decisión confirmada 2026-05-19
```

```
Scanner/Búsqueda UI
        │
        ▼
ProductRepository.lookupByCode(code, partnerId?)
        │
        ├─ Online? ──► API /products/lookup/{code} ──► cache local ──► return
        │
        └─ Offline? ─► SQLite local (Drift) ──────────────────────────► return
                            │
                            └─ Si no existe ──► SnackBar "Sin conexión, producto no en caché"
```

---

## 2. Dos Flujos POS

### Flujo A — Ventas (ScannerMode.sale)
```
Escaneo → lookupByCode → detectedProduct modal → AddProductToCart
→ DraggableSheet carrito → "Deslizar para cobrar"
→ PaymentConfirmationScreen (método de pago: CASH/CARD/TRANSFER)
→ CheckoutRequested → SaleRepository.checkout() → POST /api/v1/pos/checkout
→ InventoryDocument OUT + ledger tx (lado backend)
```

### Flujo B — Entradas (ScannerMode.entry)
```
Escaneo → lookupByCode → detectedProduct modal → AddProductToCart
→ Desde documento de transferencia existente O escaneos manuales individuales
→ CheckoutRequested → SaleRepository.createDocument()
→ POST /api/v1/inventory/documents { type: IN | TRANSFER, items: [...] }
→ InventoryDocument IN/TRANSFER + ledger tx (lado backend)
```

**Concepto para entradas:** UUID determinístico `d1d198e1-24a8-589c-94c1-ec8dafd67ab0` (ENT-PUR).
Para entradas desde documento de transferencia se puede pasar `externalDocumentId` al request.

---

## 3. Estrategia de Sincronización (Revisada)

### 3A — Full Sync Bootstrap (sin cambios)
Descarga el catálogo completo en bloques de 500 registros. Se ejecuta:
- En primera instalación / sin caché
- Vía botón manual "Sincronizar Ahora"

```dart
GET /api/v1/products?limit=500&page=N
// Respuesta esperada: { data: [...], meta: { total: N } }
```

Requiere pantalla de loading bloqueante (Ve §4.5).

### 3B — Delta Sync (estrategia revisada)
El endpoint `GET /products/sync?since=` **no existe** en `master_data_service`. Decisión: no crearlo.

**Estrategia alternativa:**
- Delta sync = full sync paginado, pero comparando `lastSynced` local vs. `updated_at` del servidor
- Para catálogos ≤5,000 SKUs: full sync cada 24h tiene latencia aceptable (~2-3s en Wi-Fi)
- **Opción futura (si el catálogo crece):** Agregar parámetro `updated_since` al endpoint `/products` en master_data_service (1 línea de SQLAlchemy: `WHERE updated_at > :since`)

**Implementación inmediata:** Cambiar `deltaSync()` para hacer full sync paginado directamente (eliminar la llamada a `products/sync` que siempre falla):

```dart
// ANTES (roto — endpoint no existe):
final response = await _dio.get('products/sync', queryParameters: {'since': lastSync});

// DESPUÉS (usa endpoints existentes):
return await fullSync(); // Reutilizar fullSync con estrategia de timestamp
```

### 3C — On-Demand Cache (sin cambios)
Scan miss → `GET /products/lookup/{code}` → `_localDb.cacheProduct()`.
Siguiente scan del mismo código → 0ms latencia local.

### 3D — Stock Actual (nuevo — pendiente)
El campo `currentStock` en `LocalProducts` no se actualiza desde inventory_service.
Para mostrarlo en el carrito/scanner se necesita una sync separada:

```
GET /api/v1/inventory/levels?warehouse_id={warehouseId}
// Respuesta: [{ product_id, quantity, available_quantity, warehouse_id }]
```

**Plan:** Agregar `StockSyncService` que actualiza solo el campo `currentStock` en `local_products`
sin tocar precios. Frecuencia: en cada apertura de pantalla (es liviano).

---

## 4. Plan de Implementación — Pendientes

### 4.1 Bug crítico: `_calculateTotal()` no definida (BLOCKER)
**Archivo:** [sales_screen.dart:1005](../../src/interno_billing_app/lib/features/home/presentation/sales_screen.dart)
**Problema:** Método llamado en `.then()` del Navigator pero no está definido → crash en checkout.
**Fix:** Eliminar la llamada — `setState(() { _cartItems.clear(); })` es suficiente. El total se recalcula al limpiar el carrito vía getter.

### 4.2 Bug crítico: Doble estado de carrito (B1)
**Archivo:** `sales_screen.dart`
**Problema:** `_cartItems` (local) y `ScannerBloc.state.items` (BLoC) son dos fuentes de verdad paralelas. El hack en `_checkoutSale()` los sincroniza manualmente — frágil.
**Fix:** Migrar `sales_screen.dart` para leer el carrito directamente del `ScannerBloc`:
```dart
// En build():
BlocBuilder<ScannerBloc, ScannerState>(
  builder: (context, state) {
    final items = state.items; // ← fuente única de verdad
    // ... render carrito desde state.items
  }
)
// Scan en cámara → bloc.add(BarcodeScanned(code)) en vez de _addProductToCart()
```

### 4.3 Delta Sync — Reemplazar llamada rota
**Archivo:** [product_sync_service.dart:129](../../src/interno_billing_app/lib/core/services/product_sync_service.dart#L129)
**Fix:** Reemplazar `_dio.get('products/sync', ...)` con `fullSync()` directamente, guardando el checkpoint igual.

### 4.4 Búsqueda offline local
**Archivo:** [product_repository.dart:94](../../src/interno_billing_app/lib/features/scanner/data/repositories/product_repository.dart#L94)
**Problema:** `return []` cuando offline.
**Fix:** Agregar query a Drift con filtro por nombre/SKU:
```dart
// En local_database.dart:
Future<List<Product>> searchLocal(String query) async {
  final q = '%${query.toLowerCase()}%';
  return (select(localProducts)
    ..where((t) => t.name.lower().like(q) | t.sku.lower().like(q))
    ..limit(50))
    .get()
    .then((rows) => rows.map(_toProduct).toList());
}
```

### 4.5 Pantalla de loading para sync inicial (NECESARIA)
Para catálogos grandes (>1k SKUs), el `fullSync()` puede tardar 3-8s.
Mostrar pantalla bloqueante con barra de progreso en primera instalación:

```dart
// En company_selection_screen.dart o warehouse_selection_screen.dart (post-login):
if (cachedCount == 0) {
  await Navigator.push(context, MaterialPageRoute(
    builder: (_) => InitialSyncScreen(), // Pantalla nueva
  ));
}

// InitialSyncScreen muestra:
// ┌─────────────────────────────────────┐
// │  ⬇ Descargando catálogo...         │
// │  ████████░░░░░░░░  450 / 1,200 SKU │
// │  "Esta operación solo ocurre        │
// │   una vez. Asegúrate de tener       │
// │   conexión Wi-Fi."                  │
// └─────────────────────────────────────┘
```

### 4.6 Schema migrations en lugar de drop-recreate
**Archivo:** [local_database.dart:63](../../src/interno_billing_app/lib/core/database/local_database.dart#L63)
**Problema actual:** `onUpgrade` borra todas las tablas — en campo con Wi-Fi limitado, perder el caché es crítico.
**Fix:**
```dart
onUpgrade: (m, from, to) async {
  // Migración incremental en vez de drop-all
  if (from < 3) {
    await m.addColumn(localProducts, localProducts.mpn); // ejemplo futuro
  }
}
```

### 4.7 StockSyncService (nuevo)
Crear servicio ligero para actualizar `currentStock` desde inventory_service:
```dart
class StockSyncService {
  Future<void> syncWarehouseStock(String warehouseId) async {
    final response = await _dio.get('inventory/levels',
      queryParameters: {'warehouse_id': warehouseId});
    // Actualizar solo campo currentStock en local_products via Drift
    await _localDb.updateStockLevels(levels);
  }
}
```

---

## 5. Deferred (Próxima Fase)

| Item | Descripción |
|---|---|
| `Workmanager` background sync | Sync automático cada 15min cuando dispositivo carga y hay Wi-Fi. Pendiente junto con módulo de notificaciones push |
| `GET /products?updated_since=` | Endpoint delta eficiente en `master_data_service` — solo si catálogo crece >5k SKUs |
| Offline buffer SQLite para checkout | Cola de ventas pendientes cuando sin red → sync al recuperar conexión |

---

## 6. Orden de Ejecución Recomendado

```
1. Fix _calculateTotal() → 5 min — eliminar crash blocker
2. Fix delta sync (reemplazar products/sync) → 10 min — hacer que sync funcione correctamente
3. Migrar sales_screen.dart carrito a BLoC → 60-90 min — resolver estado duplicado
4. InitialSyncScreen (loading bloqueante) → 45 min — UX para primera instalación
5. Búsqueda offline en searchProducts() → 20 min — funcionalidad offline completa
6. StockSyncService → 30 min — currentStock fresco en carrito
7. Schema migrations → 15 min — proteger caché en actualizaciones
```

---

## 7. Arquitectura de Archivos (Estado Actual)

```
lib/
├── core/
│   ├── database/local_database.dart          ← Drift schema + queries (COMPLETO)
│   ├── di/injection.dart                     ← GetIt wiring (COMPLETO)
│   └── services/product_sync_service.dart    ← Phase A/B/C (B ROTO — fix §4.3)
└── features/
    ├── home/presentation/sales_screen.dart   ← Flujo Ventas UI (BUG doble carrito §4.2)
    └── scanner/
        ├── data/repositories/
        │   ├── product_repository.dart       ← Online-first lookup (COMPLETO)
        │   ├── sale_repository.dart          ← checkout + document (COMPLETO)
        │   └── partner_repository.dart       ← B2B partner search (COMPLETO)
        └── presentation/
            ├── bloc/scanner_bloc.dart        ← State machine POS (COMPLETO)
            ├── scanner_screen.dart           ← Flujo Entradas + Ventas BLoC (COMPLETO)
            ├── inventory_stock_screen.dart   ← Entrada manual individual (COMPLETO)
            └── payment_confirmation_screen.dart ← Pago + método (COMPLETO)
```
