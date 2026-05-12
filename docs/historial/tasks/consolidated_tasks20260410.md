# Consolidated Tasks — 2026-04-10 (Updated End-of-Day)

## ✅ COMPLETADO HOY — Backend (master_data_service)

### RBAC & Governance (Fase 33.4)
- [x] POST/PATCH/DELETE guards (`admin/owner/superadmin`) en `categories.py`
- [x] POST/PATCH/DELETE guards en `brands.py`
- [x] POST/PATCH/DELETE guards en `uom_router.py`
- [x] `ProductCreate` schema extendido con campos fiscales: `sat_product_code`, `hts_code`, `is_taxable`, `allow_price_override`, `brand_id`, `requires_batch`, `requires_expiration`

### Precios & Fiscal (Fase 33.5)
- [x] Modelo `ProductPrice` con `valid_until` (soft-close) + `is_manual` (audit flag)
- [x] Migración Alembic `cc4ea7bf91a2` aplicada en master_data_db
- [x] Chain de migraciones sin bifurcaciones: `bb3da9fcddfd → e5703c10603a → cc4ea7bf91a2`
- [x] Removed DB-level FK `product_prices.warehouse_id → warehouses` (cross-service boundary)

---

## ✅ COMPLETADO HOY — Frontend

### Modales de Catálogo (Gobernanza Administrativa)
- [x] `partner-modal.component.ts` — AuthService + disable form + delete button (admin-only)
- [x] `concept-modal.component.ts` — RBAC + soft-delete
- [x] `category-brand-modal.component.ts` — RBAC + soft-delete
- [x] `uom-modal.component.ts` — RBAC + save guard + delete button
- [x] `Partner` interface → `email?: string` añadido (fix TS2339)

### Servicios
- [x] `MasterDataService` — `createProduct`, `updateProduct`, `deleteProduct`, `getPrices`, `upsertPrice`, `deleteUom`
- [x] `ProductPrice` interface: `valid_until`, `is_manual`, `warehouse_id`, `price_list_index 1-10`
- [x] `Product` interface: `sat_product_code`, `hts_code`, `is_taxable`, `allow_price_override`

### Alta Rápida de Productos (Fase 33.6)
- [x] `product-wizard.component.ts` — Grid estilo Excel, N filas simultáneas, Tab/Enter/Esc
- [x] Guardado por fila + guardado masivo "Guardar Todo"
- [x] Precio opcional — producto se guarda sin tabulador asignado
- [x] Recuperación de errores por fila con "Reintentar"
- [x] Moneda bloqueada por contexto de empresa (MXN/USD)

### Dashboard de Fichas Incompletas
- [x] Panel colapsable amber en `product-catalog.component.ts`
- [x] `computed` signal `incompleteProducts()` — detecta sin Precio, SAT, Categoría
- [x] Chips de campo faltante por producto
- [x] Toggle "Filtrar" para mostrar solo incompletos en la tabla
- [x] Botón "Precios" inline por producto incompleto

---

## 🔄 EN PROGRESO

### Express Open (Apertura Express de Inventario)
- [ ] Conectar toggle de Apertura Express al `InventoryService` (movimiento de entrada inicial)
- [ ] Concepto a usar: `APERTURA` o `ENTRADA_INICIAL`
- [ ] Requiere: selección de almacén + cantidad inicial en el wizard

---

## ⬜ PENDIENTE — Siguiente Sesión

### Backend
- [ ] Endpoint `PATCH /products/{id}` (edición de producto existente)
- [ ] Endpoint `DELETE /products/{id}` (soft-delete)
- [ ] Validación de SKU único a nivel DB/servicio
- [ ] Snapshot de pruebas de integración cross-service (`test_cross_service_price_fetch.py`)
- [ ] `test_mirror_transfer.py` — Validar espejo ICT con tenant destino

### Frontend
- [ ] Edit Product flow (modal/panel desde la tabla) para productos privados
- [ ] Product detail view con historial de precios (timeline de versiones)
- [ ] Conectar "Apertura Express" al InventoryService
- [ ] Implementar búsqueda/filtro por SKU en la tabla del catálogo
- [ ] Agregar columna "% Completitud" en tabla de productos

### Infraestructura / AWS
- [ ] Crear repositorios en Amazon ECR para auth-service y master-data-service
- [ ] Primer push de imágenes Docker estables
- [ ] Configurar bucket S3 + distribución CloudFront para el frontend
- [ ] Ejecutar pruebas de integración completas en ambiente de staging

---

## 🧪 Validación Pendiente
- [ ] Verificar que `master-data-service` acepta el payload completo del wizard (SKU + UOM mínimo)
- [ ] Verificar que `product-catalog` muestra el panel amber con productos del seed que no tienen precio
- [ ] Test manual: crear 5 productos via Alta Rápida, verificar que aparecen en panel de incompletos
