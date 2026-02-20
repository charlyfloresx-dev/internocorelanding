# 💳 Billing Service — InternoCore

> **Puerto:** `8001` | **Estado:** Scaffolding completo | **Versión:** `1.0.0`

Microservicio de facturación del ecosistema InternoCore. Gestiona el ciclo de vida completo de documentos de cobro: creación, emisión, pagos parciales/totales y notas de crédito, con aislamiento multitenant por `company_id`.

---

## Dominio

| Entidad | Descripción |
|---|---|
| `Invoice` | Factura con folio auto-generado (Triple Identity Pattern) |
| `InvoiceItem` | Líneas con IVA y descuento calculados atómicamente |
| `PaymentTerm` | Catálogo de términos (global o por empresa) |
| `CreditNote` | Notas de crédito (devolución, descuento, corrección) |
| `Payment` | Pagos parciales/totales; actualiza estado de factura automáticamente |

**Estados de factura:** `DRAFT → ISSUED → SENT → PAID / PARTIALLY_PAID / OVERDUE / CANCELLED / VOIDED`

---

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/invoices/` | Crear factura con ítems |
| `GET` | `/api/v1/invoices/` | Listar facturas (filtro por status) |
| `GET` | `/api/v1/invoices/{id}` | Detalle de factura |
| `PATCH` | `/api/v1/invoices/{id}/status` | Cambiar estado |
| `POST` | `/api/v1/payments/` | Registrar pago |
| `GET` | `/health` | Health check |

---

## Estructura

```
billing_service/
├── Dockerfile                     # Build context: /backend
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
│       └── b001_billing_init.py   # Crea las 5 tablas iniciales
├── docs/
│   └── CONTEXTO.md                # Especificación técnica completa
├── SERVICE_LOG.md                 # Bitácora de construcción
└── app/
    ├── main.py                    # Entry point FastAPI
    ├── dependencies.py            # JWT multitenant + service factories
    ├── core/enums.py              # InvoiceStatus, CreditNoteType, PaymentMethod
    ├── infrastructure/database.py # AsyncEngine + sesión
    ├── models/                    # Entidades SQLAlchemy (MultiTenantBase)
    ├── schemas/billing.py         # Pydantic Create/Read schemas
    ├── services/
    │   ├── invoice_service.py     # Auto-folio + totales
    │   └── payment_service.py     # Auto-estado PAID / PARTIALLY_PAID
    └── api/v1/endpoints/
        ├── invoices.py
        └── payments.py
```

---

## Variables de Entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `DATABASE_URL` | ✅ | `postgresql+asyncpg://user:pass@host/billing_db` |
| `SECRET_KEY` | ✅ | Clave de validación JWT |
| `ALLOWED_ORIGINS` | ❌ | CORS — lista CSV (default: `*`) |

---

## Ejecución Local (Docker)

```bash
# Desde /backend (build context)
docker compose up billing_service --build
```

## Migraciones

```bash
python -m alembic upgrade head
```

---

## Pendientes

- [ ] Agregar al `docker-compose.yml` (puerto `8001`)
- [ ] Integrar `common.security.decode_access_token` en `dependencies.py`
- [ ] Endpoints de `CreditNotes` y `PaymentTerms`
- [ ] Aging Report (cuentas por cobrar vencidas)
- [ ] Lógica `OVERDUE` automática (scheduled job)

📄 **Especificación técnica completa:** [`docs/CONTEXTO.md`](docs/CONTEXTO.md)
📋 **Bitácora de construcción:** [`SERVICE_LOG.md`](SERVICE_LOG.md)
