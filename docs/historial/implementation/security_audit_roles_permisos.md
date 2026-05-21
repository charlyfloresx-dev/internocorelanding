# Auditoría de Seguridad — Roles y Permisos · InternoCore
**Fecha de auditoría:** 2026-05-21  
**Estado Tier 1:** ✅ Parcialmente completado (Phase 120) — ver sección "Estado Post-Phase 120"

---

## Resumen Ejecutivo

| Servicio | Endpoints | 🔴 Crítico | 🟠 Alto | 🟡 Medio | ✅ OK | % Protegido |
|---|---|---|---|---|---|---|
| Auth Service | 34 | 18 | 2 | 8 | 6 | 18% |
| Inventory Service | 45 | 10 | 8 | 12 | 15 | 33% |
| Master Data Service | 60 | 32 | 20 | 5 | 3 | 5% |
| HCM Service | 7 | 0 | 0 | 1 | 6 | 86% |
| Subscription Service | 13 | 7 | 0 | 4 | 2 | 15% |
| Notification Service | 8 | 2 | 0 | 2 | 4 | 50% |
| Tickets Service | 10 | 0 | 0 | 0 | 10 | 100% |
| **TOTAL** | **177** | **69** | **30** | **32** | **46** | **26%** |

---

## 1. Auth Service

| Endpoint | Método | Guard | Riesgo |
|---|---|---|---|
| /login | POST | Ninguno (rate limit 5/min) | 🟡 |
| /select-company | POST | SelectionToken | ✅ |
| /refresh | POST | Ninguno (rate limit 20/min) | 🟡 |
| /me | GET | get_current_tenant_context | ✅ |
| /users/ | GET/POST | get_current_tenant_context | ✅ |
| /users/invite | POST | get_current_tenant_context | ✅ |
| /users/force-assign | POST | verify_admin_master_key | 🔴 |
| /companies/ | GET/POST | Ninguno | 🔴 |
| /companies/{id} | PUT/DELETE | Ninguno | 🔴 |
| /biometric/register/begin | POST | Ninguno | 🔴 |
| /biometric/register/complete | POST | Ninguno | 🔴 |
| /biometric/auth/begin | POST | Ninguno | 🔴 |
| /biometric/auth/complete | POST | Ninguno | 🔴 |
| /seed/run | POST | Ninguno | 🔴 |
| /elevate | POST | verify_admin_master_key | 🟠 God Mode |
| /elevate/{jti} | DELETE | SubscriptionGuard | ✅ |

**Vulnerabilidades clave:**
- `/companies/*`: usuario anónimo puede crear/eliminar empresas → bypass multi-tenancy
- Biometría: 4 endpoints completamente abiertos → cualquiera puede registrar dispositivos biométricos
- `/seed/run`: reinicia la DB desde internet sin autenticación

---

## 2. Inventory Service

| Endpoint | Método | Guard | Riesgo |
|---|---|---|---|
| /bulk-load | POST | Solo X-Internal-Secret | 🔴 |
| /movements | POST | Ninguno | 🔴 |
| /reconcile | POST | Ninguno | 🔴 |
| /reserve | POST | Ninguno | 🔴 |
| /release | POST | Ninguno | 🔴 |
| /transfers/dispatch | POST | Ninguno | 🔴 |
| /pos/checkout | POST | Ninguno | 🔴 |
| /dashboard/summary | GET | Solo header company_id | 🟠 |
| /dashboard/reports/kardex | GET | Ninguno | 🟠 |
| /dashboard/reports/valuation | GET | Ninguno | 🟠 |
| /dashboard/mission-control | GET | Ninguno | 🟠 |
| /boms | POST/PATCH/DELETE | SubscriptionGuard | ✅ |
| /variants | GET/POST/DELETE | SubscriptionGuard | ✅ |
| /audit | GET | require_scope(inventory:read) | ✅ |

**Vulnerabilidades clave:**
- `/movements` y `/reconcile`: cualquiera puede mutar el kardex (ledger inmutable) sin auth
- `/pos/checkout`: crea documentos de inventario sin ninguna validación de identidad
- Dashboard financiero: KPIs, valoración, kardex — expuestos sin scope

---

## 3. Master Data Service 🔴 Peor estado del ecosistema

53% de endpoints son CRÍTICOS. Solo `brands.py` tiene guards consistentes.

| Módulo | POST | PATCH | DELETE | Estado |
|---|---|---|---|---|
| brands | require_scope(master_data:write) | require_scope | require_scope | ✅ |
| categories | Ninguno | Ninguno | Ninguno | 🔴 |
| products | Ninguno | Ninguno | Ninguno | 🔴 |
| variants | Ninguno | Ninguno | Ninguno | 🔴 |
| partners | Ninguno | Ninguno | Ninguno | 🔴 |
| warehouses | Ninguno | Ninguno | Ninguno | 🔴 |
| prices (12 endpoints) | Ninguno | Ninguno | Ninguno | 🔴 |
| currencies | Ninguno | Ninguno | Ninguno | 🔴 |
| uom | Ninguno | Ninguno | Ninguno | 🔴 |

**Vulnerabilidades clave:**
- Cualquier usuario (sin autenticar) puede crear/borrar productos, partners, precios
- Endpoints de precios expuestos → atacante puede modificar precios de lista
- `GET /currencies/update-all` (POST) sin guard → fuerza recarga de Banxico/Frankfurter

---

## 4. Subscription Service

| Endpoint | Método | Guard | Riesgo |
|---|---|---|---|
| /tenants/{id}/change-plan | POST | Ninguno | 🔴 |
| /tenants/{id}/force-activate | POST | Ninguno | 🔴 |
| /tenants/{id}/force-status | POST | Ninguno | 🔴 |
| /tenants/{id}/override-grace | POST | Ninguno | 🔴 |
| /wallet/award | POST | Ninguno | 🔴 |
| /wallet/deduct | POST | Ninguno | 🔴 |
| /billing/sessions/create-embedded | POST | Ninguno | 🔴 |
| /internal/entitlements/{id} | GET | Ninguno | 🟡 (inter-svc) |
| /internal/status/{id} | GET | Ninguno | 🟡 (inter-svc) |

**Vulnerabilidades clave:**
- `/force-activate` y `/change-plan`: cualquier cliente puede activar su propia suscripción gratis
- `/wallet/award`: cualquiera puede otorgarse créditos
- Endpoints `/internal/*` son de uso inter-servicio pero están expuestos al gateway

---

## 5. HCM Service ✅ Bien protegido

Todos los endpoints con SubscriptionGuard. Solo `/template` (descarga de CSV vacío) sin guard — riesgo bajo aceptable.

---

## 6. Tickets Service ✅ Modelo a seguir

100% protegido con `require_scope` granular + HMAC para comunicación inter-servicio.

---

## Prioridades de Corrección

### Tier 1 — Riesgo financiero/integridad de datos
- [x] Auth `/companies/*` — `verify_admin_master_key` (**Phase 120**)
- [x] Auth `/seed/run` — `verify_admin_master_key` (**Phase 120**)
- [x] Subscription `/wallet/award` + `/wallet/deduct` — `verify_admin_master_key` (**Phase 120**)
- [x] Inventory `/movements`, `/reconcile`, `/reserve`, `/release`, `/transfers/dispatch` — `SubscriptionGuard` (**Phase 120**)
- [x] Inventory dashboard endpoints (9) — `SubscriptionGuard` (**Phase 120**)
- [ ] **Master Data: ~30 endpoints de escritura** — `require_scope(["master_data:write"])` ← **PENDIENTE**
- [ ] **Subscription `/tenants/{id}/force-*` y `/change-plan`** — `verify_admin_master_key` ← **PENDIENTE (verificar)**

### Tier 2 — Próxima semana
- [ ] Auth biometría: 4 endpoints — `Depends(get_current_tenant_context)`
- [x] Inventory dashboard GETs — `SubscriptionGuard` (**Phase 120**)
- [ ] `/pos/checkout` — `SubscriptionGuard`
- [x] Auth `/seed/run` — `verify_admin_master_key` (**Phase 120**)

### Tier 3 — Este mes
- [ ] Rate limiting en endpoints de Subscription y Master Data
- [ ] Auditar endpoints `/internal/*` de subscription — considerar HMAC como en tickets_service

---

## Estado Post-Phase 120 (2026-05-21)

Phase 120 completó todos los Tier 1 excepto:
1. **Master Data** (~30 write endpoints) — el mayor gap restante
2. **Subscription `/tenants/{id}/*`** admin endpoints — estado real a verificar en código

Los contadores del Resumen Ejecutivo corresponden al estado PRE-Phase 120.
