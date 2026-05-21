# Frontend Status Report — InternoCore
**Fecha:** 2026-05-21 | **Stack:** Angular 19 Zoneless · Signals · TailwindCSS | **Phase actual:** 122

---

## 1. Completitud por Módulo

| Módulo Angular | Ruta | % | Estado | Componentes activos |
|---|---|---|---|---|
| `core` + `shared` | — | 95% | ✅ Producción | 23 servicios, 6 interceptores, 3 guards |
| `auth` | `/auth` | 92% | ✅ Producción | login, tenant-selection, onboarding |
| `inventory` | `/inventory` | 88% | ✅ Producción | 12 vistas, 9 subcomponentes |
| `catalog` | `/catalog` | 83% | ✅ Producción | 8 vistas de catálogo maestro |
| `dashboard` | `/dashboard` | 80% | ✅ Producción | latency, integrity, usage monitors, tenant-view |
| `admin` | `/admin` | 75% | 🔄 En desarrollo | user-mgmt, staff-mgmt, forensic-dashboard |
| `monitor` | `/monitor` | 73% | 🔄 En desarrollo | resource-monitor, tickets-dashboard, industrial-flows |
| `billing` | `/billing` | 60% | 🟡 Parcial | subscription page — falta self-service |
| `production` | `/production` | 40% | 🟡 Parcial | dashboard básico — sin interfaces de piso |

**Estimación Global Frontend:** ~**79%** listo para producción

---

## 2. ¿Qué le falta a cada módulo?

### `core` + `shared` (95%)
- [ ] `navigation.service.ts` — scope aliases para módulos `billing`, `production`, `monitor` (colon-format vs dot-format)
- [ ] Paywall reactivo: componente visual para estado `UNPAID` en módulos bloqueados

### `auth` (92%)
- [ ] Flujo OAuth (Google/Facebook) — botones presentes pero flujo backend no probado E2E
- [ ] WebAuthn registration UI — actualmente solo via endpoint directo, sin flujo guiado
- [ ] Error boundary para fallo de `selection_token` expirado

### `inventory` (88%)
- [ ] Vista de variantes de producto accesible para rol `collaborator` (bloqueada por bug 403 de backend)
- [ ] Pantalla de reimpresión de documentos históricos con precios Point-in-Time
- [ ] Filtro de historial en `document-list` por rango de fechas y tipo de documento
- [ ] Vista de Kardex por producto (trazabilidad completa de movimientos)
- [ ] UI para `cycle-count` — formulario incompleto

### `catalog` (83%)
- [ ] `price-import-dashboard` — carga masiva de precios via CSV sin UI de progreso/errores
- [ ] Vista de `PriceAgreements` B2B por partner — solo existe en backend
- [ ] Editor de variantes de proveedor (MPN, brand, `unit_price`) sin pantalla dedicada
- [ ] Filtros avanzados en `product-catalog` (por categoría + marca + estado)

### `dashboard` (80%)
- [ ] `tenant-dashboard.component.ts` — widgets de OEE y producción vacíos (MES no desplegado)
- [ ] Alertas en tiempo real de `inventory_service` densidad/capacidad en panel
- [ ] KPIs financieros (valor total del inventario, WAC promedio por almacén)

### `admin` (75%)
- [ ] **UI de WhatsApp Gateway QR** — pantalla para inicializar sesión, mostrar QR Base64, y monitorear estado CONNECTED/DISCONNECTED. Backend listo, frontend falta.
- [ ] `staff-management` — asignación de departamentos y permisos avanzados
- [ ] Vista de audit trail con filtros (`forensic-dashboard` básico)
- [ ] GOD MODE panel — activación desde Angular (actualmente solo via curl/Postman)
- [ ] Gestión de configuración de notificaciones por empresa (`company_notification_configs`)

### `monitor` (73%)
- [ ] `tickets-dashboard` — vista Kanban drag-and-drop para triaje
- [ ] Chat en tiempo real en detalle de ticket (WebSocket ya implementado en backend)
- [ ] `industrial-flows` — visualización de flujos de inventario en tiempo real
- [ ] SLA timeline por ticket — indicador visual de tiempo restante

### `billing` (60%)
- [ ] Self-Service Stripe Checkout para tenants `UNPAID` — solo existe paywall
- [ ] Historial de facturas y descargas PDF
- [ ] Cambio de plan sin contacto a ventas (upgrade/downgrade self-service)
- [ ] Vista de uso de módulos vs. límites del plan

### `production` (40%)
- [ ] Interfaces táctiles de piso (grande, contraste alto) para operadores de línea
- [ ] Registro de paradas de línea (Andon) con integración a tickets
- [ ] OEE en tiempo real por estación (requiere `mes_service` desplegado)
- [ ] Production orders y work orders UI

---

## 3. Cobertura Funcional Frontend → Backend

| Capacidad | Backend | Frontend | Alineación |
|---|---|---|---|
| Autenticación T1/T2 | ✅ 92% | ✅ 92% | ✅ Alineado |
| Multitenancy (JWT + headers) | ✅ 100% | ✅ 100% | ✅ Alineado |
| Scope/Permission Guards | ✅ 90% | ✅ 88% | ✅ Alineado (Phase 120) |
| Inventario / Kardex | ✅ 90% | ✅ 88% | ✅ Alineado |
| Catálogo / Precios | ✅ 86% | ✅ 83% | ✅ Alineado |
| Tickets / Soporte | ✅ 83% | 🟡 73% | Gap: chat RT, Kanban |
| Capital Humano (HCM) | ✅ 75% | 🟡 60% | Gap: dept. UI, certs |
| Notificaciones / WhatsApp | ✅ 78% | ❌ 20% | Gap crítico: UI QR Gateway |
| Suscripciones / Billing | ✅ 88% | 🟡 60% | Gap: self-service, history |
| WMS / Producción | 🟡 35% | ❌ 15% | Ambos incompletos |
| Rate Limiting visible | ✅ activo | ✅ toast 429 | ✅ Alineado |
| Modo Offline (mobile) | ❌ pendiente | ❌ pendiente | Sin brecha — ambos pendientes |

---

## 4. Bloqueos Principales

| Prioridad | Bloqueador | Módulo afectado |
|---|---|---|
| 🔴 ALTA | UI de QR WhatsApp Gateway — backend 100% listo, cero UI | `admin` |
| 🔴 ALTA | Vista de variantes bloqueada para collaborador (bug 403 backend) | `inventory` |
| 🟡 MEDIA | Self-Service Checkout — tenants `UNPAID` sin salida visual | `billing` |
| 🟡 MEDIA | Chat en tiempo real en ticket — WebSocket conectado, UI falta | `monitor` |
| 🟡 MEDIA | GOD MODE panel en Angular — actualmente solo via API | `admin` |
| 🟡 MEDIA | Pantallas Kanban / SLA en tickets-dashboard | `monitor` |
| 🟢 BAJA | Interfaces táctiles de piso para operadores | `production` |
| 🟢 BAJA | Offline mode con Service Workers | `inventory` (mobile) |

---

## 5. Resumen Comparativo Backend vs Frontend

| Área Funcional | Backend | Frontend | Brecha |
|---|---|---|---|
| Autenticación | 92% | 92% | Sin brecha |
| Inventario | 90% | 88% | Mínima — detalle de variantes |
| Catálogo Maestro | 86% | 83% | Mínima — bulk import, PriceAgreements |
| Tickets | 83% | 73% | Chat RT, Kanban drag-and-drop |
| Notificaciones | 78% | 20% | **Brecha alta** — UI de QR Gateway |
| HCM / Staff | 75% | 60% | Departamentos, certificaciones |
| Suscripciones | 88% | 60% | **Brecha alta** — self-service billing |
| Producción / MES | 28% | 40% | Backend más rezagado |
| **GLOBAL** | **82%** | **79%** | Backend 3pts adelante |

---

**Estimación Global Frontend:** ~**79% listo para producción**
**Stack:** Angular 19 Zoneless · Signals reactivos · TailwindCSS · Playwright E2E
**Fecha:** 2026-05-21
