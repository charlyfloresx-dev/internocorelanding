# Historial Maestro de Implementación: 2026-05-24

Jornada de estabilización POS mobile. Phase 131 (payment_method + scanner unificado) y Phase 132 (restauración diseño Uber POS).

---

## 1. Phase 131 — ScannerScreen Unificado + payment_method

### Problema raíz
Dos problemas independientes resueltos en la misma fase:

1. **Dual-camera hardware conflict (BLASTBufferQueue)**: `IndexedStack` con Ventas (`SalesScreen`) y Recibos (`ScannerScreen`) creaba dos instancias de `MobileScannerController` activas simultáneamente en el Moto g04s, causando crashes.

2. **payment_method como workaround en `notes`**: El método de pago se codificaba dentro del campo `notes` como texto libre (`"Mobile POS Sale | Pago: CASH"`), sin columna dedicada en `inventory_documents`.

### Solución — Cámara única
```
IndexedStack _physicalSlots = [0, 0, 1, 2, 3]
Tab 0 (Ventas) ──┐
                  ├─► slot físico 0 → ScannerScreen(isTabMode: true)
Tab 1 (Recibos) ─┘       ↑
                    MobileScannerController (único)

_onTabTapped(index):
  if index == 0 → ScannerBloc.add(ModeSelected(sale))
  if index == 1 → ScannerBloc.add(ModeSelected(entry))
```

### Solución — payment_method como columna
```sql
-- Migración 003
ALTER TABLE inventory_documents ADD COLUMN payment_method VARCHAR(20);
```
```dart
// Antes (workaround):
'notes': 'Mobile POS Sale | Pago: CASH'

// Después (campo propio):
if (paymentMethod != null) 'payment_method': paymentMethod,
```

### Arquitectura de enums dinámica
`PAYMENT_METHOD` vive en tabla `enumerations` con `company_id=NULL` (global). Empresas pueden extender con métodos propios. El endpoint `GET /api/v1/enumerations?type=PAYMENT_METHOD` retorna globales + empresa combinados.

---

## 2. Phase 132 — Restauración Diseño Uber POS

### Problema detectado en prueba física (Moto g04s)
Phase 131 resolvió el conflicto de hardware unificando ambas pestañas en `ScannerScreen`, pero al hacerlo, la pestaña Ventas perdió el diseño Uber POS frozen definido en `docs/design_system/uber_pos_layout.md`.

El usuario observó el cambio visual y solicitó restaurar el diseño original.

### Decisión arquitectónica: Dual-mode en un solo widget

**Opción descartada**: Restaurar `SalesScreen` como slot separado en `IndexedStack`.
- Pros: diseño limpio, separación de responsabilidades.
- Cons: Dos `MobileScanner` activos simultáneamente → conflicto de hardware en Moto g04s (el problema que Phase 131 resolvió).

**Opción elegida**: `ScannerScreen` con dos builders según `state.mode`.
```dart
builder: (context, state) {
  return state.mode == ScannerMode.sale
      ? _buildSaleMode(context, state)   // Uber POS design
      : _buildEntryMode(context, state); // Entry design
},
```
Un solo `MobileScannerController` compartido. Al cambiar de modo, Flutter reconstruye el `Scaffold` pero el controller ya está inicializado y la cámara permanece activa (no se reinicia).

### Diseño Uber POS (sale mode) — componentes integrados

```
Stack (Scaffold.body)
├── Positioned.fill → MobileScanner(controller: controller)
├── Positioned.fill → CustomPaint(_ScannerOverlayPainter)
│     ├── Fondo negro 65% opacidad con cutout 75%w × 220px
│     └── Esquinas verdes 4px + laser rojo con glow
├── Positioned(top:50) → Top bar
│     ├── _buildCircularButton(home)
│     ├── Pill "MX$[total]"
│     └── _buildCircularButton(search → quick catalog dialog)
└── DraggableScrollableSheet(0.11 → 0.85)
      ├── Handle pill
      ├── Row: tune icon | [items count + cliente + sync indicator] | list icon
      ├── Divider
      ├── Empty state OR ListView items con [-] qty [+]
      └── Slide-to-confirm → _navigateToPayment() → PaymentConfirmationScreen
```

### Estado integrado en `_ScannerScreenState`

| Variable | Origen | Propósito |
|---|---|---|
| `_sheetController` | `SalesScreen` | Controla expand/collapse del DraggableScrollableSheet |
| `_slideProgress` | `SalesScreen` | Progreso del slider de pago (0.0 → 1.0) |
| `_isSyncing` | `SalesScreen` | Guard contra sincronizaciones simultáneas |
| `_productCatalog` | `SalesScreen` | Lista local de productos para quick search |
| `_syncStatusText` | `SalesScreen` | Texto de estado de la última sincronización |
| `_isProductModalShown` | `SalesScreen` | Guard contra múltiples modals simultáneos |
| `controller` | `ScannerScreen` | `MobileScannerController` — único para ambos modos |
| `_keyboardFocusNode` | `ScannerScreen` | Captura entrada de scanner externo (barcode reader) |

### Flujo de checkout por modo

| Mode | Detección producto | Confirmar carrito |
|---|---|---|
| `sale` | `_showProductDetectedSheet()` (bottom sheet con precio en cyan) | Slide handle → `_navigateToPayment()` → `PaymentConfirmationScreen` |
| `entry` | `_showProductConfirmation()` (sheet oscuro con AGREGAR/DESCARTAR) | `_SlideToConfirm` → `CheckoutScreen` |

---

## 3. Verificaciones del Día

| Check | Resultado |
|---|---|
| Code Graph Auditor | ✅ 0 CRITICALs — 14 servicios |
| Ecosystem validate | ✅ 8/8 OK |
| HMAC subscription | ✅ 403 |
| HMAC tickets | ⚠️ 400 (body validation antes de HMAC — no brecha) |
| Prueba física Moto g04s | ✅ Diseño Uber POS visible, items escaneados correctamente |

---

## 4. Archivos Clave

| Archivo | Cambio |
|---|---|
| `src/interno_billing_app/lib/features/scanner/presentation/scanner_screen.dart` | Refactorizado completo — dual-mode, 685 líneas añadidas |
| `backend/inventory_service/alembic/versions/003_add_payment_method_to_documents.py` | Nueva migración |
| `backend/inventory_service/inventory_app/models/document.py` | `payment_method` column |
| `backend/inventory_service/inventory_app/schemas/inventory.py` | `payment_method` field |
| `src/interno_billing_app/lib/features/scanner/data/models/inventory_document_request.dart` | `toJson()` con campo propio |
| `backend/scripts/unified_industrial_seed.py` | PAYMENT_METHOD + sync master_data_db |
