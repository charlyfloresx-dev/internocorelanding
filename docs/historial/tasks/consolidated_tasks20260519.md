# Consolidated Tasks — 2026-05-19 (Phase 115)

## Completadas ✅

### Sprint 2 — GOD MODE Angular Frontend
- [x] `GodModeStore` — signal store volátil, sin localStorage, auto-destrucción via setTimeout
- [x] `godModeInterceptor` — HttpInterceptorFn, registrado al FINAL del array (no primero)
- [x] `SystemControlComponent` — doble confirmación, countdown reactivo, revocación en closeSession()
- [x] `ForensicDashboardComponent` — tab "Alertas de Seguridad", filas rojas pulsantes < 24h
- [x] `app.routes.ts` — ruta `/admin/system-control`
- [x] `main-layout.component.ts` — nav links Auditoría Forense + Consola Emergencia

### Post-Sprint Hardening
- [x] Eliminado bloque `isSuperAdmin()` obsoleto en `multi-tenant.interceptor.ts`
- [x] `GET /security-logs` — guard cambiado a `scopes=["*"]` OR `role in (admin, owner)`
- [x] Rate limit real IP: `limiter.py` lee `X-Real-IP` → `X-Forwarded-For` antes del fallback
- [x] `TokenPayload` — campos `jti` y `god_mode` agregados
- [x] `/elevate` — escribe `SET godmode:{jti} 1 EX 300` en Redis tras emitir token
- [x] `get_current_active_user` — JTI gate para tokens god_mode (Redis lookup)
- [x] `DELETE /admin/elevate/{jti}` — revocación anticipada con audit log
- [x] `SystemControlComponent.closeSession()` — llama DELETE antes de store.clear()

### Code Graph & TypeScript
- [x] Code Graph: 0 CRITICALs en 14 servicios
- [x] `npx tsc --noEmit`: 0 errores

### Smoke test E2E — ✅ COMPLETADO vía gateway (port 8000)
- [x] Clave incorrecta → 401 ERR_INVALID_MASTER_KEY ✅
- [x] Clave correcta → JTI generado, expires_in=300, Redis SET godmode:{jti}=1 ✅
- [x] GOD_MODE_ACTIVATED en audit_logs con IP y JTI ✅
- [x] DELETE /elevate/{jti} → revoked=True, Redis DEL ✅
- [x] Token revocado → 401 en get_current_active_user + SubscriptionGuard ✅
- [x] GOD_MODE_REVOKED en audit_logs ✅

### Bug fixes descubiertos durante smoke test — ✅ RESUELTOS
- [x] nginx.conf: `proxy_set_header Connection "upgrade"` global → bloqueaba TODOS los POST via gateway. Fix: `Connection ""` en server block; `upgrade` solo en `/ws` location
- [x] `SubscriptionGuard`: no chequeaba JTI gate → tokens revocados pasaban. Fix: JTI Redis lookup agregado con mismo fail-safe

## Pendiente

### Deuda técnica activa (no relacionada con GOD MODE)
- [ ] `GET /products/{id}/variants` → 403 para rol `collaborator` (scope `inventory:read` faltante)
- [ ] `audit_logs` faltante en hcm_db / subscription_db (AuditService falla silenciosamente)
- [ ] Point-in-Time Price Lookup para documentos históricos
- [ ] `internal_id_pattern` faltante en `hr_tenant_configs`
- [ ] WMS y MES no desplegados en dev stack
