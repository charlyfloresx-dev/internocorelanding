# 🌐 Estado General del Frontend — InternoCore
**Fecha**: 2026-03-04 | **Stack**: Angular 19.1 Zoneless · Signals · TailwindCSS · Standalone Components  
**Alineado con**: [backend_status_report.md](file:///C:/Users/flore/.gemini/antigravity/brain/77976df3-8351-4bcf-9d65-0a1dde97ca84/backend_status_report.md) (Fases 1‑10)

---

## 📊 Completitud por Módulo

| # | Módulo Frontend | Ruta | % | Estado |
|---|-----------------|------|---|--------|
| 1 | **Auth (Login + T1/T2)** | `/auth` | **95%** | ✅ Login, tenant-selection, forgot-password, registro |
| 2 | **Core (Interceptores + Guards)** | `core/` | **88%** | ✅ AuthInterceptor, MultiTenantInterceptor, ErrorMapper |
| 3 | **Onboarding** | `/onboarding` | **85%** | ✅ Wizard + setup-warehouse. Pendiente: `complete-onboarding` POST real |
| 4 | **Home / Dashboard** | `/home` | **75%** | 🟡 Estructura lista. Pendiente: KPIs dinámicos en tiempo real |
| 5 | **Inventory** | `/inventory` | **72%** | 🟡 Dashboard, editor de documentos, lista. Pendiente: stock-break alerts UI |
| 6 | **Catalog (Productos + UOM)** | `/catalog` | **70%** | 🟡 Páginas y servicios. Pendiente: bulk-import UOM, gestión de precios |
| 7 | **Users** | `/users` | **65%** | 🟡 Páginas y servicios presentes. Pendiente: RBAC granular de UI por rol |
| 8 | **Tickets** | `/tickets` | **60%** | 🟡 List + Editor. Pendiente: estados MES, MTTR/OEE, StopLog view |
| 9 | **Production (MES)** | `/production` | **45%** | 🔴 Dashboard, line-monitor, work-order. Sin integración real con `mes_service` |
| 10 | **Admin (God Mode)** | `/admin` | **40%** | 🔴 Componente básico. Pendiente: consola de control de inventario, force-release UI |
| 11 | **System** | `/system` | **30%** | 🔴 Solo estructura. Pendiente: configuración empresa, preferencias, i18n UI |
| — | **Shared UI Kit** | `shared/` | **55%** | 🟡 Componentes básicos. Pendiente: tabla genérica, modales, formularios reutilizables |

**Completitud global estimada: ~65% (Beta Funcional)**

---

## 🔍 ¿Qué le falta a cada módulo para llegar al 100%?

### ✅ `auth` — 95% | Falta 5%
- [ ] Flujo real de `forgot-password` (integración con backend reset endpoint)
- [ ] Manejo de `is_new` → redirección al Welcome Wizard post-login
- [ ] E2E tests del handshake T1/T2

### ✅ `core` — 88% | Falta 12%
- [ ] `api.interceptor.ts` vacío — implementar desempaquetado de `ApiResponse { status, data }`
- [ ] `multi-tenant.interceptor.ts` vacío — confirmar que inyecta `X-Company-Id` en todas las requests
- [ ] Guard de `CanActivate` para el selector de empresa (si hay `selection_token` sin `access_token`)
- [ ] Tests unitarios de interceptores

### 🟡 `onboarding` — 85% | Falta 15%
- [ ] Llamada real a `POST /complete-onboarding` con `X-Company-Id`
- [ ] Setup inicial de warehouse conectado a `wms_service`
- [ ] Indicador de progreso del wizard en múltiples pasos

### 🟡 `home` — 75% | Falta 25%
- [ ] KPIs dinámicos: stock total, tickets abiertos, órdenes en tránsito
- [ ] Widget de alertas P1/P2 desde `notification_service`
- [ ] Panel de accesos rápidos por rol (OWNER vs OPERATOR)

### 🟡 `inventory` — 72% | Falta 28%
- [ ] Vista de Auditoría de Stock (`GET /dashboard/stock`) — consumir Phase 8 backend
- [ ] UI para `force-release` de reservas huérfanas (con confirmación RBAC)
- [ ] Indicadores visuales de stock-break (alerta roja cuando `available < 0`)
- [ ] Identidad Triple (UUID + Folio + Sequence) visible en todas las vistas
- [ ] `[readonly]` en formularios cuando documento está `CONFIRMED`
- [ ] Paginación + filtros avanzados en lista de movimientos

### 🟡 `catalog` — 70% | Falta 30%
- [ ] Gestión de precios por empresa/almacén
- [ ] Bulk-import de UOM desde CSV
- [ ] Vista de relaciones producto → categoría → proveedor
- [ ] Filtros compuestos (categoría + precio + disponibilidad)

### 🟡 `users` — 65% | Falta 35%
- [ ] Asignación granular de roles por empresa en UI
- [ ] Invitación de usuarios por email
- [ ] Vista de permisos activos (rol → permisos expandidos)
- [ ] Gestión de `UserPreferences` (canales de notificación por usuario)

### 🟡 `tickets` — 60% | Falta 40%
- [ ] Visualización de estados MES: OPEN → IN_PROGRESS → RESOLVED → CLOSED
- [ ] Vista de recursos consumidos (`TicketResource`)
- [ ] Panel de métricas: MTTR, tickets por prioridad, tiempo promedio de resolución
- [ ] `StopLog` viewer para downtime de estaciones
- [ ] Integración con `notification_service` para alertas en-app (badge)

### 🔴 `production` — 45% | Falta 55%
- [ ] Integración real de `LineMonitor` con `mes_service` (actualmente usa datos simulados)
- [ ] Work Orders: crear, asignar y cerrar órdenes de producción
- [ ] OEE Calculator visible en dashboard
- [ ] Registro de downtime vinculado a `StopLog` del `tickets_service`
- [ ] Trazabilidad por lote (`lot_number`, `batch_id`)

### 🔴 `admin` — 40% | Falta 60%
- [ ] Consola de control de inventario (consumir Phase 8 `/dashboard/stock`)
- [ ] Botón de force-release con confirmación modal
- [ ] Vista de suscripciones por empresa (activar/desactivar módulos)
- [ ] Panel de usuarios y roles gestionables por OWNER

### 🔴 `system` — 30% | Falta 70%
- [ ] Configuración de empresa (logo, moneda, timezone)
- [ ] Gestión de preferencias globales (notificaciones, idioma)
- [ ] i18n UI completo con diccionarios en `src/locales/`
- [ ] Página de salud del sistema (health checks de microservicios)

---

## 🧩 Cobertura Funcional Frontend→Backend

| Capacidad | Cobertura Frontend |
|-----------|-------------------|
| Login T1/T2 + Selector de empresa | ✅ 95% |
| `X-Company-Id` en todas las requests | 🟡 75% (interceptor vacío) |
| Visualización de stock e inventario | 🟡 72% |
| Creación/confirmación de documentos | 🟡 70% |
| Gestión de productos y catálogo | 🟡 70% |
| Tickets operativos (crear, editar) | 🟡 60% |
| Consola de auditoría (Phase 8) | 🔴 0% (no implementada en frontend) |
| Notificaciones In-App (Phase 10) | 🔴 0% (sin integración) |
| Dashboard de producción / OEE | 🔴 45% (datos simulados) |
| i18n / Idiomas | 🔴 20% (parcial) |
| Tests E2E frontend | 🔴 0% |

---

## 🚦 Bloqueos Principales para llegar al 100%

| Prioridad | Bloqueo | Módulo afectado |
|-----------|---------|----------------|
| 🔴 Crítico | `api.interceptor.ts` y `multi-tenant.interceptor.ts` vacíos | Todo el frontend |
| 🔴 Crítico | Tests E2E — ninguno implementado | Todo |
| 🔴 Crítico | `production` sin integración real con `mes_service` | Production, Admin |
| 🟡 Alto | Consola de auditoría Phase 8 sin UI | Admin |
| 🟡 Alto | Notificaciones In-App sin integrar | Home, Tickets |
| 🟡 Alto | Identidad Triple (UUID+Folio+Seq) no validada en todas las vistas | Inventory, Catalog |
| 🔴 Crítico | Infraestructura AWS (S3 + CloudFront) — sin desplegar | Deploy |

---

## 🏁 Resumen Comparativo Backend vs Frontend

| Dimensión | Backend | Frontend |
|-----------|---------|----------|
| Completitud global | **~76%** | **~65%** |
| Tests automatizados | 30% | 0% |
| Infraestructura prod | 0% | 0% |
| Módulos Production/MES | 40% | 45% |
| Notificaciones | 65% | 0% |
| Auth/Multitenancy | 95% | 88% |
