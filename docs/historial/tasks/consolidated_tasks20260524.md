# Consolidado de Tareas: 2026-05-24

Jornada de estabilización del flujo POS mobile: unificación de scanner + campo `payment_method` + restauración del diseño Uber POS. Phases 131–132.

---

## Phase 131 — ScannerScreen Unificado + payment_method Backend ✅ COMPLETADO

### Mobile (Flutter)
- `[x]` Pestañas Ventas (tab 0) y Recibos (tab 1) unificadas en slot físico 0 con `IndexedStack`
- `[x]` `_physicalSlots = [0, 0, 1, 2, 3]` — un solo `MobileScannerController` sin conflicto BLASTBufferQueue
- `[x]` `_onTabTapped` despacha `ModeSelected(sale/entry)` al `ScannerBloc`
- `[x]` Guard `if (event.mode == state.mode) return` en `_onModeSelected` — carrito no se limpia al re-tapear
- `[x]` `ScannerScreen(isTabMode: bool)` — botón X oculto cuando embebida como tab
- `[x]` Bug fix `PartnerSearchModal`: `context.read<PartnerRepository>()` → `sl<PartnerRepository>()`
- `[x]` `_buildNotes()` workaround eliminado — `payment_method` enviado como campo JSON propio

### Backend (inventory_service)
- `[x]` Migración `003_add_payment_method_to_documents.py` — `payment_method VARCHAR(20) NULL`
- `[x]` `InventoryDocument.payment_method: Mapped[Optional[str]]`
- `[x]` `InventoryDocumentCreate.payment_method: Optional[str] = None`
- `[x]` `doc_entity` y repositorio mapean el campo

### Seed / Enumeraciones
- `[x]` `PAYMENT_METHOD` en `unified_industrial_seed.py`: CASH, CARD, TRANSFER, STRIPE, CREDIT
- `[x]` Section 3 sincroniza enums a `master_data_db` (`seed_enumerations(session)`)
- `[x]` `master_data_service/scripts/seed_enums.py` actualizado

---

## Phase 132 — ScannerScreen Dual-Mode: Uber POS Restaurado ✅ COMPLETADO

### Diagnóstico
- `[x]` Identificado: Phase 131 reemplazó el diseño Uber POS (`SalesScreen`) con el diseño de entrada simple en la pestaña Ventas
- `[x]` `docs/design_system/uber_pos_layout.md` confirma diseño frozen — NO se puede modificar visualmente

### Implementación
- `[x]` `_buildSaleMode()` integrado en `_ScannerScreenState` — diseño completo de `SalesScreen`:
  - `Positioned.fill` MobileScanner con controller compartido
  - `_ScannerOverlayPainter`: cutout 75% × 220px + esquinas verdes + laser rojo
  - Top bar: botón home · pill `MX$total` · botón búsqueda
  - `DraggableScrollableSheet` (0.11 → 0.85) + slide-to-confirm → `PaymentConfirmationScreen`
- `[x]` `_buildEntryMode()` preservado — toggle VENTA/ENTRADA + panel fijo 45% → `CheckoutScreen`
- `[x]` Estado de sync integrado: `_sheetController`, `_slideProgress`, `_isSyncing`, `_productCatalog`, `_syncStatusText`
- `[x]` `_showProductDetectedSheet()` (sale) y `_showProductConfirmation()` (entry) separados en `BlocConsumer` listener
- `[x]` 4 `withOpacity` deprecados → `withValues(alpha:)` corregidos
- `[x]` BuildContext async gap corregido en `_buildCheckoutAction`

### Sync-docs
- `[x]` Code Graph: 0 CRITICALs — 14 servicios 100% compliance
- `[x]` Ecosystem: 8/8 servicios OK
- `[x]` HMAC subscription: 403 ✓
- `[x]` REPO_LOG.md Phase 132 actualizado
- `[x]` `src/interno_billing_app/SERVICE_LOG.md` Phase 132 actualizado
- `[x]` Commit: `2c67758 feat(mobile): Phase 132 — ScannerScreen dual-mode UI, Uber POS sale design restored`

---

## Pendientes Acumulados (cross-phase)

- `[ ]` Rebuild contenedor `interno-inventory-dev` para aplicar migración 003 (`payment_method`)
- `[ ]` Re-run `unified_industrial_seed.py` para poblar `PAYMENT_METHOD` en ambas DBs
- `[ ]` Fix `GET /products/{id}/variants` 403 para rol `collaborator` — agregar `inventory:read` en `select_company_command.py`
- `[ ]` `default_tax_rate` Planta US = 0.0 (actualmente 0.16)
- `[ ]` `POST /api/v1/pos/checkout` validación end-to-end con flows antigravity
- `[ ]` Activar `mes_service` y `wms_service` en nginx (ADR-04)
- `[ ]` HMAC tickets `/internal` retorna 400 en vez de 403 — verificar que guard precede a body validation
- `[ ]` Agregar `+526641667684` al seed `unified_industrial_seed.py`
