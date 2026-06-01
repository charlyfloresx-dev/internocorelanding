# Tareas Consolidadas — 2026-06-01

## Completadas

### Phase 162 RTR — Phase C Tests + Phase D Login Integration ✅

**Phase C — 10/10 integration tests PASSED contra PostgreSQL real:**
- `family_salt` único por test (`os.urandom(32).hex()`) — evita deadlock por UNIQUE constraint
- `datetime.now(timezone.utc)` en handlers — ImmatureSignatureError corregido (non-UTC timezones)
- `await db.refresh(model)` post-flush en `rotate_family_atomically()` y `revoke_family()` — MissingGreenlet corregido
- `log_rotation_event()` con `tenant_id=company_id` — MultiTenantBase NOT NULL
- Assertions de test corregidas: tampering detectado por FASE 2 compound WHERE, idempotencia = misma generación (no tokens bitwise-equal)
- conftest.py reescrito sin duplicación, NullPool para evitar conflictos de event loop
- pytest.ini con `asyncio_mode = auto`

**Phase D — Login integration (select-company emite 2 tokens):**
- `select_company_command.py` líneas 195-257: `RefreshToken` legacy → `create_family()` + `_issue_refresh_token()` (RTR gen=0, HMAC-sealed)
- Respuesta `select-company`: `{ access_token, refresh_token (RTR gen=0), token_type, user_id, company_id, ... }`
- Colaboradores industriales: `refresh_token: null` (sin FK `users.id` en HCM, acceso por AT corto-viviente)
- Migration `a9e3b1c0d2f4`: `drop_table('refresh_tokens')` — tabla legacy deprecada (pendiente ejecutar `alembic upgrade head`)
- `full_auth_flow.py`: PASO 4 RTR E2E validation (Login → SelectCompany → RTR Refresh gen 0→1)
- `kiosk_auth_flow.py`: nota Phase D sobre colaboradores sin RTR

---

### Phase 159 RTR — Auditoría A+B Correcciones ✅
- **B-01 ALTA RESUELTO** — `company_id` añadido como parámetro en `get_family()`, `rotate_family_atomically()`, `revoke_family()`. Compound WHERE `(id == X) & (company_id == Y)`. `IRefreshTokenRepository` actualizado.
- **Stack trace leak ALTA RESUELTO** — `except Exception as e: detail=f"Internal error: {str(e)}"` → `detail="An internal error occurred"` + `logging.error(..., exc_info=True)`.
- **B-02 StaleDataError RESUELTO** — Eliminado try/except inválido; SQLAlchemy maneja via `version_id` nativo `__mapper_args__`.
- **GAP-1 RESUELTO** — `TokenFamily.__post_init__` valida `re.fullmatch(r'^[0-9a-f]{64}$', self.family_salt)`.
- **GAP-2 RESUELTO** — Handler usa `version_id` (ORM-managed); `version_counter` eliminado del flujo.
- **GAP-3 RESUELTO** — Event Listeners SQLAlchemy en `RefreshTokenRotationAudit` bloquean UPDATE/DELETE con `RuntimeError`.

---

## Pendientes activos (por prioridad)

### ALTA
- **RTR Frontend Semáforo (Angular + Flutter)**: Interceptores deben implementar request queueing para evitar ráfagas concurrentes de `/auth/refresh`. Patrón: `BehaviorSubject<boolean>` + encolado en Angular; `Completer<String>` en Flutter. Sin esto: N requests simultáneos al expirar AT → N rotaciones → REUSE_DETECTED → logout falso.
- **POS checkout E2E**: Validar `POST /api/v1/pos/checkout` end-to-end — script `flow_pos_checkout.py` listo (desbloqueado ahora que auth_service RTR está completo)

### MEDIA
- **RTR DB Worker (auth_service)**: Script de purga periódica. Borrar `RefreshTokenFamily` con `refresh_window_expires_at < NOW() - 7d` + CASCADE en `refresh_token_rotation_audit`. Usar `db.execute(text("DELETE ..."))` — bypassa Event Listeners ORM que bloquean DELETE. Ejecutar como cron diario.
- **RTR Migration aplicar**: `docker exec interno-auth-dev alembic upgrade head` → drop `refresh_tokens` legacy table
- Rate limit por endpoint en WMS, MES, HCM, Subscription
- PriceAgreement context en typeahead `GET /products/?q=`
- Mobile AVD Pixel 7 API 34 — dark/light theme + flujo de venta
- Domain purity: `log_rotation_event()` retorna ORM model — cambiar a `None` o `AuditRecord`

### BAJA
- **RTR AWS WAF**: Regla rate-limit en ALB/CloudFront antes de proceso Python. Revisar `pool_size`/`max_overflow` para ~1,000 refreshes simultáneos en cambio de turno.
- **RTR Observabilidad**: Alerta CloudWatch si `REUSE_DETECTED` >3 veces en 5min por company_id → SNS/PagerDuty. Dashboard `GET /admin/sessions` → familias activas (`revoked_at IS NULL`).
- GAP-5: Documentar `CompanyIdMismatchError → 401` (ADR, desviación intencional)
- GAP-6: `concurrent_attempt_detected=True` en `_revoke_family_for_breach()`
- HCM `JobPosition`, `shift_id`, WMS deploy, MES `routing.py`
- Agentes `.github/agents/` — "NexoSuite" → "InternoCore"

## Code Graph Status (2026-06-01)
- 0 CRITICALs confirmados tras sync-docs Phase 162
- Requiere re-ejecutar si se toca `auth_service` o cualquier servicio con nuevas rutas
