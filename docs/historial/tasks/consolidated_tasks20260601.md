# Tareas Consolidadas — 2026-06-01

## Completadas

### Phase 163 — RTR Frontend Semaphore (Angular + Flutter) ✅

**Angular `multi-tenant.interceptor.ts` — 2 bugs corregidos:**
- `authReq.clone()` en lugar de `req.clone()` → preserva `X-Company-ID`, `X-User-ID` en retry
- `REFRESH_ABORT` sentinel: emitido al `refreshTokenSubject` en `catchError` → desbloquea cola `filter(t !== null)` inmediatamente

**Flutter `auth_interceptor.dart` — nuevo:**
- `Completer<String>` semáforo: primer 401 inicia refresh, N concurrentes await en `completer.future`
- `complete(token)` / `completeError(e)` libera o falla a todos atómicamente
- Guard `_retried = true` + path `/auth/` → sin loops infinitos
- Registrado ÚLTIMO en DI → PRIMERO en `onError` (Dio LIFO)

Verificado en vivo: login → select-company → dashboard → inventory-documents ✅

---

### Phase 162 RTR — Phase C Tests + Phase D Login Integration ✅

**Phase C — 10/10 integration tests PASSED contra PostgreSQL real:**
- `family_salt` único por test (`os.urandom(32).hex()`) — evita deadlock por UNIQUE constraint
- `datetime.now(timezone.utc)` en handlers — ImmatureSignatureError corregido
- `await db.refresh(model)` post-flush — MissingGreenlet corregido
- `log_rotation_event()` con `tenant_id=company_id` — MultiTenantBase NOT NULL
- Assertions de test corregidas: tampering por FASE 2, idempotencia = misma generación

**Phase D — Login integration (select-company emite 2 tokens):**
- `select_company_command.py`: `create_family()` + `_issue_refresh_token()` (RTR gen=0, HMAC-sealed)
- Respuesta: `{ access_token, refresh_token (RTR gen=0), token_type, ... }`
- Colaboradores: `refresh_token: null` (sin FK users.id en HCM)
- Migration `a9e3b1c0d2f4`: `drop_table('refresh_tokens')` — pendiente `alembic upgrade head`

---

### Phase 159 RTR — Auditoría A+B Correcciones ✅
- B-01, Stack trace leak, B-02, GAP-1, GAP-2, GAP-3 — todos resueltos

---

## Pendientes activos (por prioridad)

### ALTA
- **POS checkout E2E**: Validar `POST /api/v1/pos/checkout` end-to-end — script `flow_pos_checkout.py` listo

### MEDIA
- **RTR DB Worker (auth_service)**: Script de purga vía `db.execute(text("DELETE ..."))`. Cron diario.
- **RTR Migration aplicar**: `docker exec interno-auth-dev alembic upgrade head` → drop `refresh_tokens`
- Rate limit por endpoint en WMS, MES, HCM, Subscription
- PriceAgreement context en typeahead `GET /products/?q=`
- Mobile AVD Pixel 7 API 34 — dark/light theme + flujo de venta
- Domain purity: `log_rotation_event()` retorna ORM model

### BAJA
- **RTR AWS WAF**: Regla rate-limit en ALB/CloudFront + pool_size/max_overflow para ~1,000 refreshes.
- **RTR Observabilidad**: Alerta `REUSE_DETECTED` >3×/5min + dashboard sesiones activas.
- GAP-5: `CompanyIdMismatchError → 401` ADR
- GAP-6: `concurrent_attempt_detected` en `_revoke_family_for_breach()`
- HCM `JobPosition`, `shift_id`, WMS deploy, MES `routing.py`
- Agentes `.github/agents/` — "NexoSuite" → "InternoCore"

## Code Graph Status (2026-06-01 Phase 163)
- 0 CRITICALs — 13 servicios CLEAN
- Ecosystem: 8/8 servicios OK
- Internal endpoints HMAC: tickets 403 ✅, subscription 403 ✅
