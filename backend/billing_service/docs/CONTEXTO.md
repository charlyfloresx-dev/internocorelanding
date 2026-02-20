# 💳 BILLING SERVICE — CONTEXTO TÉCNICO

> **Servicio:** `billing_service`
> **Puerto:** `8001`
> **Versión:** `1.0.0`
> **Creado:** 2026-02-19
> **Estado:** Scaffolding completo — listo para integración

---

## 1. Propósito y Responsabilidades

El `billing_service` es el microservicio central de **facturación** dentro del ecosistema InternoCore. Gestiona el ciclo de vida completo de un documento de cobro: desde su creación como borrador hasta su cobro total, incluyendo notas de crédito y registro de pagos parciales.

### Dominio cubierto
| Entidad | Responsabilidad |
|---|---|
| `Invoice` | Documento principal de factura con folio automático |
| `InvoiceItem` | Líneas de detalle con cálculo atómico de impuestos |
| `CreditNote` | Nota de crédito aplicada contra una factura (devolución, descuento, error) |
| `PaymentTerm` | Catálogo de términos de pago (30 días, 2/10 neto 30, etc.) |
| `Payment` | Registro de pago parcial o total; actualiza el estado de la factura automáticamente |

---

## 2. Arquitectura del Servicio

### Stack
- **Framework:** FastAPI (async)
- **ORM:** SQLAlchemy 2.x (async) + `asyncpg`
- **Migraciones:** Alembic (modo asíncrono)
- **Base de datos:** PostgreSQL (multitenant)

### Estructura de capas (Clean Architecture)
```
app/
├── api/v1/endpoints/   → Controladores HTTP (FastAPI routers)
├── services/           → Lógica de negocio (orquestación)
├── models/             → Entidades SQLAlchemy (heredan MultiTenantBase)
├── schemas/            → Contratos de entrada/salida (Pydantic)
├── core/               → Enums y constantes de dominio
├── infrastructure/     → Motor de DB y sesión async
└── dependencies.py     → Inyección de dependencias (Auth + Services)
```

---

## 3. Modelo de Dominio Detallado

### 3.1 `Invoice` — Factura

Implementa el **Triple Identity Pattern** (estándar InternoCore):

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID | Identidad interna (PK) |
| `folio` | String | Folio visible al cliente (auto-generado) |
| `series` | String | Serie del folio (ej. "FAC", "EXP") |
| `sequence_number` | Integer | Contador incremental por empresa+serie |
| `company_id` | UUID | Aislamiento multitenant (obligatorio) |
| `customer_id` | UUID | Referencia al cliente (snapshot) |
| `customer_name` | String | Snapshot del nombre en el momento de emisión |
| `customer_tax_id` | String | RFC / NIT del cliente |
| `status` | Enum | `DRAFT → ISSUED → SENT → PAID / PARTIALLY_PAID / OVERDUE / CANCELLED / VOIDED` |
| `subtotal` | Numeric(18,4) | Suma de líneas sin impuesto |
| `tax_amount` | Numeric(18,4) | IVA total |
| `discount_amount` | Numeric(18,4) | Descuentos a nivel cabecera |
| `total` | Numeric(18,4) | `subtotal + tax - discount` |
| `currency` | String(3) | ISO 4217 (default: `MXN`) |
| `exchange_rate` | Numeric(10,6) | Tipo de cambio para multi-divisa |
| `wms_document_id` | UUID | Referencia cruzada a salida de almacén (WMS) |

**Constraint de unicidad:**
- `(folio, company_id)` → `_company_folio_uc`
- `(series, sequence_number, company_id)` → `_company_series_seq_uc`

### 3.2 `InvoiceItem` — Línea de Factura

Cada ítem compute sus montos de forma atómica:

```
subtotal = quantity × unit_price × (1 - discount_percent/100)
tax_amount = subtotal × (tax_rate/100)
total = subtotal + tax_amount
```

### 3.3 `PaymentTerm` — Términos de Pago (Catálogo Híbrido)

Sigue el patrón **Hybrid Catalog**:
- `company_id = NULL` → término global del sistema (visible para todas las empresas)
- `company_id = <uuid>` → término personalizado de una empresa específica

### 3.4 `CreditNote` — Nota de Crédito

| Tipo | Uso |
|---|---|
| `RETURN` | Devolución de mercancía |
| `DISCOUNT` | Descuento posterior a la factura |
| `ERROR_CORRECTION` | Corrección de error en factura emitida |

### 3.5 `Payment` — Pago

Soporta múltiples pagos parciales por factura. Al registrar un pago, el servicio:
1. Persiste el registro de pago.
2. Suma todos los pagos anteriores.
3. Si `total_paid >= invoice.total` → cambia estado a `PAID`.
4. Si `0 < total_paid < invoice.total` → cambia estado a `PARTIALLY_PAID`.

---

## 4. Generación de Folios

El `InvoiceService` genera folios automáticamente sin bloqueos de tabla:

```
seq = MAX(sequence_number) + 1  WHERE company_id = X AND series = Y
folio = f"{series}-{seq:06d}"   (ej. "FAC-000001")
```

> **Nota:** Para alta concurrencia en producción, migrar a una secuencia de PostgreSQL (`CREATE SEQUENCE`) para garantizar atomicidad sin race conditions.

---

## 5. API Endpoints

### Invoices — `/api/v1/invoices`
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/` | Crea factura en DRAFT con ítems |
| `GET` | `/` | Lista facturas (filtro por status opcional) |
| `GET` | `/{invoice_id}` | Detalle de una factura |
| `PATCH` | `/{invoice_id}/status` | Cambia el estado de la factura |

### Payments — `/api/v1/payments`
| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/` | Registra un pago y actualiza estado de factura |

### System
| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Health check del servicio |

---

## 6. Seguridad y Multitenancy

Todas las rutas están protegidas por `get_current_user_payload` (OAuth2 Bearer JWT).

El token **debe contener** `company_id`; si no está presente, se retorna `HTTP 400 - Multitenancy violation`.

> **TODO:** Reemplazar el mock en `dependencies.py` por `common.security.decode_access_token(token)` cuando se integre el módulo compartido de seguridad.

---

## 7. Variables de Entorno

| Variable | Requerida | Default | Descripción |
|---|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://...` | URL de conexión async |
| `SECRET_KEY` | ✅ | — | Clave de validación JWT |
| `ALLOWED_ORIGINS` | ❌ | `*` | CORS — lista CSV de orígenes |

---

## 8. Tablas de Base de Datos

```sql
payment_terms    -- Catálogo global/empresa
invoices         -- Cabecera de factura (unique: folio+company, series+seq+company)
invoice_items    -- Líneas (cascade delete)
credit_notes     -- Notas de crédito (unique: folio+company)
payments         -- Pagos registrados
```

---

## 9. Integración con Otros Servicios

| Servicio | Relación |
|---|---|
| `auth_service` | Valida el JWT con `company_id` para multitenancy |
| `wms_service` | `wms_document_id` en `Invoice` vincula a una salida de almacén |
| `master_data_service` | `product_id` en `InvoiceItem` referencia el catálogo de productos |

---

## 10. Pendientes para Producción

- [ ] Integrar `common.security.decode_access_token` en `dependencies.py`
- [ ] Endpoint GET/POST para `PaymentTerms`
- [ ] Endpoint GET/POST para `CreditNotes`
- [ ] Endpoint de Aging Report (cuentas por cobrar vencidas)
- [ ] Lógica de `OVERDUE` automático via scheduled job
- [ ] Secuencia PostgreSQL para folios concurrentes
- [ ] Agregar `billing_service` al `docker-compose.yml`
- [ ] Configurar puerto `8001` en docker-compose y nginx/gateway
