# 📊 AUDIT_REPORT_SPEC — Inventory Service Analytics Engine

> **Version:** 1.0 | **Date:** 2026-03-13 | **Phase:** 28 — Forensic Report Engine

---

## 1. Overview

This document specifies the three analytics endpoints added to the `inventory-service` dashboard router in Phase 28. All endpoints operate exclusively over the **immutable `inventory_movements` ledger**, guaranteeing that no in-memory mutations occur and that historical data is fully reproducible.

All responses include:
- `X-Trace-ID` response header — echoes the frontend `x-correlation-id` or generates a new UUIDv4 for forensic linkage.
- `meta.trace_id` field inside the `ApiResponse` envelope.

---

## 2. Endpoint A — Kardex (Running Balance)

### Route
```
GET /api/v1/dashboard/reports/kardex
```

### Query Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `product_id` | UUID | ✅ | Target SKU (product variant UUID) |
| `warehouse_id` | UUID | ✅ | Target warehouse UUID |
| `limit` | int | ❌ | Max rows returned (default: 200) |

### SQL Window Function Used

```sql
SELECT
    id AS movement_id,
    created_at,
    document_id,
    movement_type,
    CASE WHEN movement_type = 'OUT' THEN -quantity ELSE quantity END AS quantity_delta,
    uom_id, weight, unit_price,
    SUM(CASE WHEN movement_type = 'OUT' THEN -quantity ELSE quantity END)
        OVER (ORDER BY created_at ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        AS running_balance,
    company_id
FROM inventory_movements
WHERE product_id = :product_id
  AND warehouse_id = :warehouse_id
  AND company_id = :company_id
ORDER BY created_at ASC
LIMIT :limit;
```

**Key Properties:**
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` guarantees O(n) computation — no subquery per row.
- Negative `quantity_delta` is assigned to `OUT` movements; all other types (IN, TRANSFER, ADJUSTMENT) are positive.
- Result is **deterministic and reproducible** from the immutable ledger.

### Response Schema
```json
{
  "status": "success",
  "data": [
    {
      "movement_id": "UUID",
      "date": "ISO-8601",
      "document_folio": "UUID",
      "movement_type": "IN | OUT | TRANSFER",
      "quantity_delta": "Decimal (signed)",
      "uom_id": "UUID",
      "weight": "Decimal",
      "unit_price": "Decimal",
      "running_balance": "Decimal"
    }
  ],
  "meta": { "count": 15, "product_id": "UUID", "trace_id": "UUID" }
}
```

---

## 3. Endpoint B — WAC Valuation (Costo Promedio Ponderado)

### Route
```
GET /api/v1/dashboard/reports/valuation
```

### Query Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `product_id` | UUID | ✅ | Target product |
| `warehouse_id` | UUID | ✅ | Target warehouse |
| `as_of_date` | ISO-8601 | ❌ | Historical cutoff (omit for current) |

### WAC Formula

$$WAC = \frac{\sum_{i \in IN, price_i > 0} qty_i \times price_i}{\sum_{i \in IN, price_i > 0} qty_i}$$

**Filtering Criterion:**
- Only `movement_type = 'IN'` with `unit_price > 0` contribute to the cost basis.
- `OUT`, `TRANSFER`, and `ADJUSTMENT` movements affect `total_units` but **not** the WAC numerator.
- `as_of_date` is a hard cutoff: `WHERE created_at <= :as_of_date`.

### Response Schema
```json
{
  "status": "success",
  "data": {
    "product_id": "UUID",
    "warehouse_id": "UUID",
    "as_of_date": "2026-03-13 | NOW",
    "total_units": "Decimal",
    "weighted_average_cost": "Decimal (4 decimals)",
    "total_inventory_value": "Decimal (2 decimals)",
    "currency_code": "USD"
  },
  "meta": { "trace_id": "UUID" }
}
```

---

## 4. Endpoint C — ABC Rotation Classification

### Route
```
GET /api/v1/dashboard/reports/abc
```

### Query Parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `warehouse_id` | UUID | ❌ | Filter by warehouse; omit for all |

### Classification Algorithm

```python
rotation_index_30d = exits_30d / (current_stock + 0.0001)

if rotation_index >= 0.7:   abc_class = "A"  # Fast-mover
elif rotation_index >= 0.3: abc_class = "B"  # Normal
else:                        abc_class = "C"  # Slow / Dead stock
```

- `exits_30d`: `SUM(quantity)` of `OUT` movements in the last 30 days per `(product_id, warehouse_id)`.
- `exits_90d`: Same for 90-day window (reported but not used for classification).
- `current_stock`: Live value from `stock` table (not computed from ledger, for performance).
- Result is **sorted descending by `rotation_index_30d`** (A-class first).

### Response Schema
```json
{
  "status": "success",
  "data": [
    {
      "product_id": "UUID",
      "warehouse_id": "UUID",
      "current_stock": "Decimal",
      "exits_30d": "Decimal",
      "exits_90d": "Decimal",
      "rotation_index_30d": "Decimal (4 decimals)",
      "abc_class": "A | B | C"
    }
  ],
  "meta": { "count": 42, "warehouse_filter": "ALL | UUID", "trace_id": "UUID" }
}
```

---

## 5. Forensic Traceability Protocol

### X-Trace-ID Header Chain

```
Frontend (auth.interceptor.ts)
  → sets: x-correlation-id: <UUIDv4>
  → request reaches inventory-service

inventory-service (dashboard.py)
  → reads: request.headers["x-correlation-id"]
  → echoes: response.headers["X-Trace-ID"] = same UUID
  → includes: meta.trace_id in ApiResponse body

Frontend (UI)
  → reads X-Trace-ID from response headers
  → displays trace_id in forensic tooltip for operator audit
```

### Multi-tenant Security
Every report query includes `WHERE company_id = :x_company_id` enforced at the repository level. Cross-tenant data leakage is architecturally impossible.

---

## 6. Files Changed (Phase 28)

| File | Change |
|---|---|
| `app/domain/entities/inventory_item.py` | Added `KardexRowEntity`, `WACValuationEntity`, `RotationABCEntity` |
| `app/domain/repositories/inventory_repository.py` | Added 3 abstract methods |
| `app/infrastructure/repositories/sqlalchemy_inventory_repository.py` | Implemented `get_kardex`, `get_wac_valuation`, `get_abc_rotation` |
| `app/schemas/dashboard.py` | Added `KardexRow`, `WACValuationRow`, `ABCRotationRow`; extended `MovementDocumentRow` |
| `app/api/v1/endpoints/dashboard.py` | Added 3 endpoints with `X-Trace-ID` header injection |
