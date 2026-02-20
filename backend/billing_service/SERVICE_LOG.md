# 📋 BILLING SERVICE — SERVICE LOG

> **Agente:** Antigravity (InternoCore AI)
> **Fecha:** 2026-02-19
> **Sesión:** Scaffolding inicial completo

---

## [2026-02-19] — Creación del Scaffolding Inicial

### Contexto
El usuario solicitó la creación de la estructura de archivos para `backend/billing_service/` basándose estrictamente en el estándar definido en `MANIFEST.md` (sección "Estándar de Creación de Microservicios").

---

### Archivos Creados

#### 📁 Raíz del servicio

| Archivo | Acción | Nota |
|---|---|---|
| `README.md` | CREADO | Descripción general, estructura y variables de entorno |
| `Dockerfile` | CREADO | Multi-stage, build context `/backend`, expone puerto `8001` |
| `requirements.txt` | CREADO | FastAPI, SQLAlchemy async, Alembic, JWT, httpx |
| `alembic.ini` | CREADO | Configuración Alembic, URL sobrescrita desde `DATABASE_URL` |

#### 📁 alembic/

| Archivo | Acción | Nota |
|---|---|---|
| `alembic/README` | CREADO | Descripción del directorio |
| `alembic/env.py` | CREADO | Async engine + fix Windows `SelectorEventLoopPolicy` |
| `alembic/script.py.mako` | CREADO | Template estándar para nuevas revisiones |
| `alembic/versions/b001_billing_init.py` | CREADO | Migración inicial — crea 5 tablas + 3 Enum types |

**Tablas creadas por `b001_billing_init.py`:**
- `payment_terms` — Catálogo híbrido global/empresa
- `invoices` — Cabecera con constraints de unicidad Triple Identity
- `invoice_items` — Líneas con CASCADE DELETE
- `credit_notes` — Notas de crédito
- `payments` — Registro de pagos

**Enum Types de PostgreSQL creados:**
- `invoicestatus` (DRAFT, ISSUED, SENT, PAID, PARTIALLY_PAID, OVERDUE, CANCELLED, VOIDED)
- `creditnotetype` (RETURN, DISCOUNT, ERROR_CORRECTION)
- `paymentmethod` (CASH, BANK_TRANSFER, CHECK, CREDIT_CARD, OTHER)

#### 📁 app/core/

| Archivo | Acción | Nota |
|---|---|---|
| `app/core/__init__.py` | CREADO | Package marker |
| `app/core/enums.py` | CREADO | `InvoiceStatus`, `CreditNoteType`, `PaymentMethod` — todos implementan `@property translation_key` (estándar MANIFEST §3.i18n) |

#### 📁 app/infrastructure/

| Archivo | Acción | Nota |
|---|---|---|
| `app/infrastructure/__init__.py` | CREADO | Package marker |
| `app/infrastructure/database.py` | CREADO | `create_async_engine`, `AsyncSessionLocal`, `get_db()` contextmanager + auto-commit/rollback |

#### 📁 app/models/

| Archivo | Acción | Nota |
|---|---|---|
| `app/models/__init__.py` | CREADO | Package marker |
| `app/models/invoice.py` | CREADO | `Invoice` + `InvoiceItem`: Triple Identity, relaciones bidireccionales, métodos `recalculate_totals()` y `compute()` |
| `app/models/credit_note.py` | CREADO | `CreditNote`: folio único por empresa, FK a invoice |
| `app/models/payment_term.py` | CREADO | `PaymentTerm`: Hybrid Catalog (`company_id` nullable), campo `translation_key` |
| `app/models/payment.py` | CREADO | `Payment`: múltiples pagos por factura, FK a invoice |

**Decisión de diseño — Triple Identity en `Invoice`:**
Se aplicó el patrón estándar del proyecto para documentos comerciales:
- `id` → identidad interna del sistema (UUID)
- `folio` → identidad visible al cliente
- `series + sequence_number` → identidad fiscal/contable

#### 📁 app/schemas/

| Archivo | Acción | Nota |
|---|---|---|
| `app/schemas/__init__.py` | CREADO | Package marker |
| `app/schemas/billing.py` | CREADO | Schemas `*Create` y `*Read` para Invoice, InvoiceItem, CreditNote, PaymentTerm, Payment (Pydantic v2) |

#### 📁 app/services/

| Archivo | Acción | Nota |
|---|---|---|
| `app/services/__init__.py` | CREADO | Package marker |
| `app/services/invoice_service.py` | CREADO | Generación automática de folios, computación de ítems, recálculo de totales, CRUD |
| `app/services/payment_service.py` | CREADO | Registro de pagos + actualización automática de estado de factura |

**Lógica de folio automático en `InvoiceService`:**
```python
seq = MAX(sequence_number) + 1  # Por empresa+serie
folio = f"{series}-{seq:06d}"   # Ej: FAC-000001
```

**Lógica de estado automático en `PaymentService`:**
```python
total_paid = SUM(payments.amount WHERE invoice_id = X)
if total_paid >= invoice.total  → PAID
elif total_paid > 0             → PARTIALLY_PAID
```

#### 📁 app/api/v1/endpoints/

| Archivo | Acción | Nota |
|---|---|---|
| `app/api/__init__.py` | CREADO | Package marker |
| `app/api/v1/__init__.py` | CREADO | Package marker |
| `app/api/v1/endpoints/__init__.py` | CREADO | Package marker |
| `app/api/v1/endpoints/invoices.py` | CREADO | `POST /` · `GET /` · `GET /{id}` · `PATCH /{id}/status` |
| `app/api/v1/endpoints/payments.py` | CREADO | `POST /` — registra pago y actualiza factura |

#### 📁 app/ (raíz)

| Archivo | Acción | Nota |
|---|---|---|
| `app/__init__.py` | CREADO | Package marker |
| `app/dependencies.py` | CREADO | `get_current_user_payload` (OAuth2 Bearer), `get_invoice_service`, `get_payment_service` |
| `app/main.py` | CREADO | Entry point FastAPI: CORS, `DomainException` handler, registro de routers |

---

### Actualizaciones a Archivos Existentes

| Archivo | Acción | Cambio |
|---|---|---|
| `MANIFEST.md` | MODIFICADO | Agregado `billing_service` en lista de servicios backend y en el Service Documentation Map |

---

### Decisiones de Arquitectura

1. **Puerto 8001:** Se asignó para evitar conflicto con `master_data_service` (8000). Debe registrarse en docker-compose y en el API gateway.

2. **`wms_document_id` en Invoice:** Se incluyó como campo opcional para trazar la factura hasta el documento de salida de almacén del WMS, habilitando reconciliación automática in futuro.

3. **Snapshot de cliente en Invoice:** `customer_name` y `customer_tax_id` se guardan al momento de la emisión para preservar el histórico, incluso si el cliente cambia sus datos maestros posteriormente.

4. **Enums con `translation_key`:** Todos los Enums implementan `@property translation_key` alineados al estándar de internacionalización del MANIFEST (§3 — i18n).

5. **`PaymentTerm` como catálogo híbrido:** `company_id = NULL` para términos globales del sistema, siguiendo el patrón de `master_data_service`.

---

### Estado Final al Cierre de Sesión

- ✅ Estructura de directorios completa (41 archivos)
- ✅ Migración inicial lista (`b001_billing_init.py`)
- ✅ Modelos con herencia `MultiTenantBase`
- ✅ Servicios con lógica de negocio funcional
- ✅ Endpoints REST registrados
- ✅ MANIFEST.md actualizado
- ⏳ Pendiente: agregar al `docker-compose.yml`
- ⏳ Pendiente: integrar `common.security` para validación JWT real
- ⏳ Pendiente: endpoints de `CreditNotes` y `PaymentTerms`
- ⏳ Pendiente: Aging Report para cuentas por cobrar
