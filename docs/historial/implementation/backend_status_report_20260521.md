# Backend Status Report — InternoCore
**Fecha:** 2026-05-21 | **Phase actual:** 122 | **Stack:** FastAPI · SQLAlchemy Async · Alembic · PostgreSQL · Redis

---

## 1. Completitud por Microservicio

| Servicio | Puerto | % | Estado | Última Fase |
|---|---|---|---|---|
| `common` | — | 93% | ✅ Producción | Phase 122 |
| `auth_service` | 8001 | 92% | ✅ Producción | Phase 122 |
| `inventory_service` | 8006 | 90% | ✅ Producción | Phase 121 |
| `subscription_service` | 8002 | 88% | ✅ Producción | Phase 122 |
| `master_data_service` | 8003 | 86% | ✅ Producción | Phase 119 |
| `tickets_service` | 8008 | 83% | ✅ Producción | Phase 118 |
| `notification_service` | 8009 | 78% | 🔄 Dev — Gateway pendiente | Phase 121 |
| `hcm_service` | 8004 | 75% | ✅ Producción | Phase 120 |
| `wms_service` | 8007 | 35% | 🟡 No desplegado | Phase 3 |
| `mes_service` | — | 28% | 🟡 No desplegado | Phase 1 |
| `kiosk_service` | 8020 | 55% | 🟡 Alterno / no core | — |

**Estimación Global Backend:** ~**82%** listo para producción (servicios desplegados)

---

## 2. ¿Qué le falta a cada servicio?

### `common` (93%)
- [ ] Pruebas unitarias del `SubscriptionGuard` con mock Redis
- [ ] `AuditService` — modo batch para reducir writes en alta concurrencia
- [ ] RLS Postgres — validar en producción AWS RDS (reconfigurar connection pool settings)

### `auth_service` (92%)
- [ ] OAuth Google/Facebook — `GOOGLE_CLIENT_ID` configurado pero flujo E2E no probado
- [ ] WebAuthn — `WEBAUTHN_RP_ID` requiere dominio de producción real para funcionar
- [ ] Rate limiting por endpoint en `/biometric` y `/companies`
- [ ] Tests de integración para el flujo T1/T2 completo

### `inventory_service` (90%)
- [ ] **Bug conocido:** `GET /products/{id}/variants` retorna 403 para rol `collaborator` — agregar `inventory:read` al scope mapping en `select_company_command.py`
- [ ] Validación E2E de `POST /api/v1/pos/checkout` (flujo completo de ventas)
- [ ] Rate limiting en endpoints de alta frecuencia (`/movements`, `/stock`)
- [ ] Offline buffer SQLite en mobile para zonas sin conectividad
- [ ] Integración con `wms_service` para despacho coordinado

### `subscription_service` (88%)
- [ ] Self-Service Stripe Checkout para tenants `UNPAID` (actualmente paywall sin salida)
- [ ] Rate limiting en endpoints `/billing/*` y `/subscriptions/*`
- [ ] Alertas automáticas por email al tenant antes de expirar (grace period)
- [ ] Tests de integración Stripe Webhook (actualmente solo Stripe CLI manual)

### `master_data_service` (86%)
- [ ] **`default_tax_rate` Planta US:** debería ser 0.0 (actualmente 0.16)
- [ ] `PriceAgreement` context en typeahead: `GET /products/?q=` no aplica precio B2B al buscar
- [ ] Rate limiting en `/products?q=` y `/prices/*`
- [ ] Bulk import de productos vía CSV/Excel
- [ ] Caché Redis para catálogos estáticos (UOM, categorías, marcas)

### `tickets_service` (83%)
- [ ] Rate limiting en endpoints de escritura
- [ ] SLA reporting completo: métricas de cumplimiento por período/área
- [ ] Push notifications a técnico asignado (actualmente solo WhatsApp grupal)
- [ ] Integración con `mes_service` para auto-cierre de tickets por evento de planta

### `notification_service` (78%)
- [ ] **Desplegar `whatsapp_gateway`:** `docker compose up --build whatsapp-gateway` + escaneo QR
- [ ] Push Notifications (FCM/APNs) — no implementadas
- [ ] HMAC en webhook endpoints (`/webhooks/*`)
- [ ] Rate limiting en `/events` (endpoint de ingestión inter-servicio)
- [ ] Template engine Jinja2 para mensajes WhatsApp formateados

### `hcm_service` (75%)
- [ ] Rate limiting en endpoints de escritura
- [ ] Control de asistencia / marcaje de tiempo con RFID
- [ ] Gestión de certificaciones con expiración y alertas
- [ ] Integración con `tickets_service` por `department_id`

### `wms_service` (35%) — No desplegado
- [ ] Habilitar upstream en nginx.conf y `docker-compose.dev.yml`
- [ ] Algoritmos de optimización de picking (wave picking, zone routing)
- [ ] UI Angular para picking y despacho
- [ ] Integración completa con `inventory_service`

### `mes_service` (28%) — No desplegado
- [ ] Habilitar upstream y desplegar
- [ ] OEE (Overall Equipment Effectiveness) — cálculo y reportes
- [ ] Andon system y alertas de parada de línea
- [ ] Integración con `tickets_service`

---

## 3. Cobertura Funcional del Ecosistema

| Capacidad | % | Detalle |
|---|---|---|
| Autenticación Multi-Tenant | 95% | T1/T2, JWT, RFID, Biometría, GOD MODE JTI, RTR |
| Autorización (Scopes/Roles) | 90% | require_scope, SubscriptionGuard, permissionGuard Angular |
| Gestión de Suscripciones | 88% | Planes, Stripe, grace period, paywall, PAST_DUE guard |
| Inventario / Kardex | 90% | Ledger inmutable, ICT, Density Guard, FIFO, POS checkout |
| Datos Maestros | 86% | Productos, UOM, precios Soft-Close, PIT reprint, variantes SSOT |
| Capital Humano (HCM) | 75% | Colaboradores, RFID/PIN, departamentos, audit |
| Tickets / Soporte | 83% | Triple Identity, SLA, Outbox, escalación dinámica, debouncing |
| Notificaciones | 75% | Email Resend ✅ · WhatsApp Twilio ✅ · Gateway Local código ✅ deploy ❌ |
| Seguridad Inter-Servicio | 88% | HMAC tickets + subscription. Gap: otros `/internal/*` |
| Auditoría / Compliance | 85% | AuditService en auth_db, inventory_db, hcm_db, subscription_db |
| WMS / Warehouse Mgmt | 35% | Código existe, no desplegado |
| MES / Manufactura | 28% | Código base, no desplegado |
| FinOps / Rate Limiting | 65% | SlowAPI multi-capa activo. Gap: subscription, master_data, hcm |

---

## 4. Bloqueos Principales

| Prioridad | Bloqueador | Servicio |
|---|---|---|
| 🔴 ALTA | `POST /pos/checkout` no validado E2E con flujos mobile completos | `inventory_service` |
| 🔴 ALTA | WhatsApp Gateway no desplegado — tenants sin canal WhatsApp local | `notification_service` |
| 🔴 ALTA | Bug: `GET /products/{id}/variants` → 403 para colaboradores | `inventory_service` |
| 🟡 MEDIA | Self-Service Stripe Checkout para tenants `UNPAID` | `subscription_service` |
| 🟡 MEDIA | Rate limiting ausente en subscription, master_data, hcm | múltiples |
| 🟡 MEDIA | `default_tax_rate` US = 0.16 (debe ser 0.0) | `master_data_service` |
| 🟡 MEDIA | PriceAgreement no aplica en typeahead de búsqueda | `master_data_service` |
| 🟢 BAJA | WMS y MES no desplegados en stack dev | `wms_service`, `mes_service` |
| 🟢 BAJA | Offline buffer SQLite mobile | `inventory_service` (mobile) |

---

## 5. Resumen de Seguridad (Post-Phase 122)

| Vector | Estado |
|---|---|
| Iron Wall — IDOR company_id | ✅ JWT-only en todos los endpoints |
| Endpoints admin sin auth | ✅ `verify_admin_master_key` en companies, seed, wallet |
| 403 ≠ logout en frontend | ✅ Interceptor separado |
| Biometric IDOR (register) | ✅ user_id del JWT, no del body |
| HMAC inter-service | ✅ tickets + subscription. Resto: sin `/internal/*` que proteger actualmente |
| JTI GOD MODE revocation | ✅ Redis gate en `get_current_active_user` + `SubscriptionGuard` |
| Rate limiting | 🟡 Activo en auth + inventory. Gap: subscription, master_data, hcm |

---

**Estimación Global:** ~**82% listo para producción** (servicios desplegados)
**Code Graph:** ✅ 0 CRITICALs — 14 servicios CLEAN | **Ecosistema:** 8/8 OK
**Fecha:** 2026-05-21

| Microservicio | Puerto | Completitud | Estado | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `auth_service` | 8001 | 100% | 🟢 | Login JWT, Roles, Multitenancy, MFA |
| `master_data_service` | 8003 | 98% | 🟢 | Empresas, Sucursales, Usuarios |
| `inventory_service` | 8006 | 95% | 🟢 | Movimientos, ubicaciones, catálogos (Limpieza completada) |
| `notification_service` | 8008 | 90% | 🟢 | Email (SMTP), WhatsApp (Twilio + Local Gateway Proxy) |
| `whatsapp_gateway` | 3011 | 100% | 🟢 | Pasarela Local Node.js (Multitenant, Headless Chromium, Cola de retrasos) |
| `wms_service` | 8007 | 85% | 🟡 | Lotes, Transferencias, Trazabilidad, RFIDs |
| `mes_service` | 8002 | 80% | 🟡 | Órdenes de producción, recetas, consumo BOM |
| `tickets_service` | 8004 | 75% | 🟡 | Tickets IT/Mantenimiento, SLAs, Chat WebSocket |
| `subscription_service` | 8005 | 70% | 🟡 | Stripe, Planes, Límite de Usuarios |
| `kiosk_service` | 8020 | 60% | 🟡 | Reloj Checador (RFID/PIN), Eventos en piso |
| `hcm_service` (HR) | 8009 | 50% | 🟡 | Colaboradores, Turnos, Nómina base |
| `common` | N/A | 100% | 🟢 | Modelos base, DB, Middleware JWT, Excepciones |

## 2. ¿Qué le falta a cada servicio?

- **`wms_service`**:
  - Consolidar la impresión ZPL/PDF de etiquetas de lotes.
  - Finalizar las rutas de inventario cíclico.
- **`mes_service`**:
  - Integrar la notificación automática por WhatsApp de órdenes de producción cerradas.
- **`tickets_service`**:
  - Webhooks de asignación de SLA integrados vía WhatsApp Gateway.
- **`hcm_service`**:
  - Módulos de reclutamiento y evaluaciones de desempeño.
- **`kiosk_service`**:
  - Sincronización offline-first robusta para fallas de red en piso.

## 3. Cobertura Funcional del Ecosistema

| Capacidad | Cobertura |
| :--- | :--- |
| Multitenancy Estricto (RLS / Filtros) | 100% |
| Seguridad y Roles (RBAC) | 100% |
| Notificaciones Email/SMS | 100% |
| WhatsApp Automático Multitenant | 100% |
| Logística e Inventarios | 95% |
| Manufactura (MES) | 80% |

## 4. Bloqueos Principales

| Prioridad | Bloqueo | Servicio Afectado |
| :--- | :--- | :--- |
| 🟢 | Ninguno crítico | N/A |

**Estimación Global Backend: 85% Completado (2026-05-21)**
