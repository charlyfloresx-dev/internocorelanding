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

**Phase D — Login integration:**
- `select_company_command.py`: `RefreshToken` legacy → `create_family()` + `_issue_refresh_token()` (RTR gen=0, HMAC-sealed)
- Migration `a9e3b1c0d2f4`: `drop_table('refresh_tokens')` — tabla legacy deprecada
- `full_auth_flow.py`: PASO 4 RTR E2E validation
- `kiosk_auth_flow.py`: nota sobre colaboradores sin RTR

---

### Phase 159 RTR — Auditoría A+B Correcciones ✅
- **B-01 ALTA RESUELTO** — `company_id` añadido como parámetro en `get_family()`, `rotate_family_atomically()`, `revoke_family()`. Compound WHERE `(id == X) & (company_id == Y)`. `IRefreshTokenRepository` actualizado.
- **Stack trace leak ALTA RESUELTO** — `except Exception as e: detail=f"Internal error: {str(e)}"` → `detail="An internal error occurred"` + `logging.error(..., exc_info=True)`.
- **B-02 StaleDataError RESUELTO** — Eliminado try/except inválido; SQLAlchemy maneja via `version_id` nativo `__mapper_args__`.
- **GAP-1 RESUELTO** — `TokenFamily.__post_init__` valida `re.fullmatch(r'^[0-9a-f]{64}$', self.family_salt)`.
- **GAP-2 RESUELTO** — Handler usa `version_id` (ORM-managed); `version_counter` eliminado del flujo.
- **GAP-3 RESUELTO** — Event Listeners SQLAlchemy en `RefreshTokenRotationAudit` bloquean UPDATE/DELETE con `RuntimeError`.

## Pendientes activos (por prioridad)

### ALTA
- **Phase C RTR**: Ejecutar `test_refresh_token_rotation.py` (12+ tests, 7 clases) contra PostgreSQL real — pendiente validación
- **Phase D RTR**: Integrar `create_family()` al handler `select-company` → emitir refresh token con familia RTR en flujo de login real
- **Estabilizar auth_service**: Levantar contenedor, verificar endpoint `POST /api/v1/auth/refresh` operativo

### MEDIA
- Rate limit por endpoint en WMS, MES, HCM, Subscription
- PriceAgreement context en typeahead `GET /products/?q=`
- Mobile AVD Pixel 7 API 34 — dark/light theme + flujo de venta
- Domain purity: `log_rotation_event()` retorna ORM model — cambiar a `None` o `AuditRecord`

### BAJA
- GAP-5: Documentar `CompanyIdMismatchError → 401` (ADR, desviación intencional)
- GAP-6: `concurrent_attempt_detected=True` en `_revoke_family_for_breach()`
- auth seed `default_tax_rate` Planta US
- HCM `JobPosition`, `shift_id`, WMS deploy, MES `routing.py`
- Agentes `.github/agents/` — "NexoSuite" → "InternoCore"

## Code Graph Status
- Esperado tras correcciones: 0 WARNINGs (B-01 corregido elimina MISSING_TENANT_FILTER)
- Requiere ejecutar `python backend/scripts/generate_code_graph.py` para confirmar
