# 📋 Consolidado de Pendientes — Interno Core (2026-06-03)

**Principio Core:** `best-effort` — Nada bloquea operaciones de piso (órdenes de producción, movimientos de inventario, registros de kardex, escaneos). Todo genera **logs estructurados + notificaciones** para reconciliación posterior.

**Estado:** 177 phases completadas. Deuda identificada y organizada por criticidad.

---

## 🔴 CRÍTICAS BLOQUEADAS (Requieren Decisión/Fix Previo)

### 1. **auth_service RTR Phase D — Integración Login**
- **Estado:** Phase A+B ✅ DONE, Phase D ⏳ PENDING
- **Bloqueador:** `create_family()` call al select-company handler requiere que todo flujo de login funcione atomically
- **Acción:** Verificar que `refresh_token_handler.py` se llamada correctamente desde `select_company_command.py`
- **Estimado:** 1h (validation + smoke test)
- **Criticidad:** ALTA — RTR no está 100% integrado
- **Principio Best-Effort:** LOGIN no debe fallar si RTR falla → generar log WARNING pero continuar con access token

**PR:** `integrate-rtr-phase-d`
```
[ ] Verificar select_company_command.py llama create_family()
[ ] Tests: 5+ (happy path + error cases)
[ ] RTR logging: crear familia con generation=0
```

---

### 2. **Promotion Service — Bloqueada por HCM Kardex**
- **Estado:** ⏳ ESPERANDO Phase 3 HCM
- **Requiere:** `GET /internal/check-eligibility/{collaborator_id}` del HCM Service
- **Acción:** No puede implementarse hasta PR-HCM-010
- **Bloqueador Secuencial:** Phase 2 HCM → Phase 3 HCM (Kardex) → Promotion Service
- **Estimado:** 4h (después que HCM esté listo)

**PR:** `implement-promotion-service` (cuando Phase 3 HCM terminada)
```
[ ] Crear Promotion Service que valida elegibilidad
[ ] Endpoint: POST /promotions (crear candidatura)
[ ] Bloquear si hcm.check_eligibility() retorna is_eligible=False
[ ] Generar evento: CandidatureCreated o RejectedByEligibility
[ ] Tests: 15+ (eligibility checks, error cases)
```

---

## 🟠 OPERACIONALES CRÍTICAS (NO BLOQUEAN PISO, pero sí alertan)

### 3. **POS Checkout End-to-End Validation**
- **Estado:** ⏳ BLOQUEADO por auth_service en modificación
- **Qué Falta:** `flow_pos_checkout.py` existe pero no se ha validado contra sistema completo
- **Acción:** Ejecutar flujo completo: escanear → precio → cambio cliente → confirmar → Kardex escrito
- **Principio Best-Effort:**
  - ✅ Permiso POST /pos/checkout → crea InventoryDocument (DRAFT)
  - ⚠️ Si fail pricing/stocks → LOG ERROR pero aceptar orden (reconciliar después)
  - ⚠️ Si fail nómina integration → LOG WARNING pero procesar movimiento inventario
- **Estimado:** 2h (flujo end-to-end + script)

**PR:** `validate-pos-checkout-e2e`
```
[ ] Script: backend/inventory_service/scripts/flows/flow_pos_checkout.py
[ ] Valida: escaneo → precio → documento → movimiento → Kardex
[ ] Error handling: LOG pero no BLOCK
[ ] Tests: 8+ casos (happy path + graceful degradation)
```

---

### 4. **MES Shift-End Auto-Logout (Labor Density)**
- **Estado:** ⏳ PENDING — Requiere APScheduler + automation
- **Qué Hace:** Al terminar turno, si NO aprobó OT → auto clock-out de labores activas
- **Acción:** Implementar tarea cron que:
  1. Cada minuto: compara NOW() vs Shift.end_time + grace_period (15min)
  2. Si turno terminó → llama LaborDensityService.materialize_range()
  3. Genera evento: LaborClosedAutomatically (para auditoría)
- **Principio Best-Effort:**
  - ⚠️ Si LaborDensityService.materialize_range() falla → generar LOG CRITICAL
  - ⚠️ NO bloquear WorkOrder completion
  - ⚠️ Reconciliar manualmente al día siguiente
- **Estimado:** 3h (scheduler + service + tests)

**PR:** `implement-shift-end-auto-logout`
```
[ ] Crear APScheduler job en mes_service/scheduler.py
[ ] Lógica: query ProductionRun activos, check shift end
[ ] Llamar LaborDensityService.materialize_range()
[ ] Generar evento: LaborClosedAutomatically
[ ] Tests: 12+ (cron timing, labor state, edge cases)
```

---

### 5. **Headcount Recompute Integration (MES ← HCM)**
- **Estado:** ⏳ PENDING — Requiere outbox pattern
- **Qué Falta:** Cuando PermissionDocumentPosted → MES debe recompute headcount
- **Acción:** 
  1. HCM publica PermissionDocumentPosted al outbox
  2. Notification Service consume
  3. MES consume y recomputa: Total - (Permisos + Vacaciones + Suspensiones activos)
- **Principio Best-Effort:**
  - ⚠️ Si recompute falla → LOG ERROR en MES
  - ⚠️ Usar valor anterior de headcount (fallback)
  - ⚠️ Notificar operador: "Headcount desactualizado, revisar HCM"
- **Estimado:** 2.5h (outbox handler + recompute logic + tests)

**PR:** `implement-headcount-recompute`
```
[ ] Backend: hcm_app/services/outbox_event_publisher.py
[ ] Backend: mes_app/services/headcount_service.py (recompute)
[ ] Event: PermissionDocumentPosted schema
[ ] Tests: 10+ (happy path + fallback logic)
[ ] Logging: structured logs con permission_id, collaborator_id
```

---

### 6. **NAIVE_DATETIME Violations (8 instances)**
- **Estado:** ⏳ PENDING — Already identified in Phase 177
- **Qué Falta:** Replace `datetime.utcnow()` → `datetime.now(timezone.utc)`
- **Archivos:**
  - auth_service/commands/*.py (2 instances)
  - inventory_service/api/endpoints/*.py (3 instances)
  - inventory_service/repositories/sqlalchemy_*.py (2 instances)
  - tickets_service/services/ticket_service.py (1 instance)
  - wms_service/repositories/__init__.py (2 instances)
- **Principio Best-Effort:** No bloquea nada, pero requiere para cloud deployment
- **Estimado:** 0.5h (find + replace + test)

**PR:** `fix-naive-datetime-violations`
```
[ ] Replace 10 instances datetime.utcnow() → datetime.now(timezone.utc)
[ ] Verificar imports: from datetime import timezone
[ ] Code Graph audit: 0 NAIVE_DATETIME warnings
[ ] Tests: run all + code graph
```

---

### 7. **Master Data Client Configuration (Cross-Service)**
- **Estado:** ⏳ PENDING — Hcm/MES/WMS accessing master_data_service
- **Qué Falta:** Cada servicio necesita `MasterDataClient` HTTP
- **Acción:**
  1. HCM: `hcm_app/infrastructure/clients/master_data_client.py`
  2. MES: `mes_app/infrastructure/clients/master_data_client.py` (EXIST pero incomplete)
  3. WMS: `wms_app/infrastructure/clients/master_data_client.py`
- **Principio Best-Effort:**
  - ⚠️ Si master_data_service DOWN → use cached values (fallback)
  - ⚠️ Log: "Master Data unavailable, using cache"
  - ⚠️ SLA: < 3 segundos (con timeout fallback)
- **Estimado:** 1.5h (3 clients × 30min)

**PR:** `implement-master-data-clients`
```
[ ] HCM client: GET /skills, GET /products
[ ] MES client: GET /bom, GET /products
[ ] WMS client: GET /products, GET /locations
[ ] Resiliencia: timeout 3s + fallback cache
[ ] Tests: 12+ (happy + timeout + 500 error)
```

---

## 🟡 HCM KARDEX IMPLEMENTATION (Phase 161+)

### 8. **HCM Phase 2 — Motor de Competencias (7.5h)**
**PRs:** HCM-001 a HCM-004
- [ ] Position model (mapeo JobPosition legacy)
- [ ] Skill model + Skill catalog
- [ ] CollaboratorSkill link
- [ ] Certification model + alerting
- **No bloquea piso:** Competencias son validación, no negación de operación

**Timeline:** 2 semanas (1-2 PRs/semana)

---

### 9. **HCM Phase 3 — Kardex Transaccional (22h)**
**PRs:** HCM-005 a HCM-013
- [ ] PermissionDocument + PermissionMovement (Header-Detail)
- [ ] KardexEvent (append-only)
- [ ] EligibilityService + validation
- [ ] Permission endpoints (CRUD + state transitions)
- [ ] Integración MES (headcount recompute)
- **Principio Best-Effort:**
  - ✅ DRAFT/PENDING states no bloquean piso
  - ✅ POSTED escribe en Kardex (auditable)
  - ⚠️ Si Kardex write falla → LOG CRITICAL pero continuar
  - ⚠️ Elegibilidad es VALIDACIÓN, no BLOQUEO (alerta si "Kardex pendiente")

**Timeline:** 3 semanas (3 PRs/semana)

---

### 10. **HCM Phase 4 — T&A Advanced (4.5h)**
**PRs:** HCM-014, HCM-015
- [ ] TimeRecord model (RFID/Biometric)
- [ ] WorkCalendar model
- **Principio Best-Effort:**
  - ⚠️ RFID malfunction → generar evento TimeRecordFailed
  - ⚠️ Operador puede usar biometric fallback
  - ⚠️ Manual clock-in como última opción

**Timeline:** 1 semana (2 PRs)

---

### 11. **HCM Phase 5 — Seguridad (4h)**
**PRs:** HCM-016, HCM-017
- [ ] MedicalRecord (Zero Trust)
- [ ] PPERecord + ERP integration
- **No bloquea piso:** Solo lectura/auditoría

---

### 12. **HCM Phase 6 — Reporting (2h)**
**PR:** HCM-018
- [ ] Kardex reports + analytics

---

## 🟢 INFRASTRUCTURE & CLOUD (AWS Deployment)

### 13. **AWS WAF Configuration (RTR Phase)**
- **Estado:** ⏳ PENDING — Para producción
- **Qué Falta:** WAF rules en ALB/CloudFront
- **Acción:**
  - Bloquear IPs con >20 req/min (prevenir refresh token abuse)
  - SQlAlchemy pool_size + max_overflow para 1,000 concurrent refreshes
- **Estimado:** 2h (AWS console + load test)

**Task:** `configure-aws-waf-rtr`

---

### 14. **Observability — Grafana Alerts (RTR Phase)**
- **Estado:** ⏳ PENDING — Para monitoring en prod
- **Qué Falta:** CloudWatch alerts si "Security Breach Alert: REUSE_DETECTED" >3 veces/5min
- **Acción:** SNS → PagerDuty + Grafana dashboard "Dispositivos Conectados"
- **Estimado:** 1.5h (CloudWatch + Grafana)

**Task:** `setup-observability-rtr`

---

### 15. **Cloud Deployment Ready**
- **Estado:** ⏳ BLOCKED por Phase 177 + RTR Phase D
- **Acción:**
  - [ ] Phase 177 NAIVE_DATETIME fixes (✅ ya está hecho)
  - [ ] RTR Phase D integración (⏳ validate)
  - [ ] Database migrations en RDS (pendiente script)
  - [ ] Secrets management (AWS Secrets Manager)
  - [ ] Load testing (1,000 concurrent users)
- **Estimado:** 6-8h (scripting + testing)

**Phase:** `Phase 180 — Cloud Deployment`

---

## 🔵 TECH DEBT (No Bloquea, Puede Esperar)

### 16. **Domain Purity — RTR Audit**
- **Issue:** `IRefreshTokenRepository.log_rotation_event()` retorna ORM model
- **Fix:** Return `None` o `AuditRecord` dataclass (domain purity)
- **Estimado:** 1h
- **Prioridad:** BAJA (código funciona, solo refactor)

---

### 17. **WMS Deployment & Phase 6**
- **Estado:** ⏳ NO DEPLOYED — WMS service existe pero no en docker-compose
- **Acción:** 
  - [ ] Descomentar upstreams en nginx.conf
  - [ ] Agregar wms-service a docker-compose.dev.yml
  - [ ] Ejecutar migraciones
  - [ ] Smoke test
- **Estimado:** 1.5h
- **Criticidad:** BAJA (WMS es fase futura)

---

### 18. **Mobile AVD Testing**
- **Estado:** ⏳ PENDING — No validado en Pixel 7 API 34 emulator
- **Acción:** Ejecutar flujo completo de ventas en AVD
  - [ ] Theme: dark + light
  - [ ] Scanner: funcionalidad
  - [ ] PriceAgreement resolution
  - [ ] Checkout atomicity
- **Estimado:** 2h (manual testing)
- **Criticidad:** MEDIA (Phase 179 mobile e2e)

---

### 19. **Price Agreement Context in Typeahead**
- **Issue:** `GET /products/?q=` no incluye PriceAgreement context
- **Fix:** Pasar `partner_id` en query, resolver precio
- **Estimado:** 1h (query param + service logic)
- **Ubicación:** master_data_service product search

---

### 20. **MES Routing Model**
- **Issue:** `routing.py` vacío — `Rout` model sin implementar
- **Nota:** FK `rout_id` en WorkOrder es nullable (no bloquea)
- **Fix:** Implementar full routing spec
- **Estimado:** 3h (model + endpoints + tests)
- **Criticidad:** BAJA (feature futura)

---

### 21. **MES RunMetricsSnapshot Metrics**
- **Issue:** Faltan: OE, TEP, FirstPassYield, OverTime, Improvement
- **Fix:** Agregar métodos de cálculo + seeding
- **Estimado:** 2h
- **Criticidad:** BAJA (analytics)

---

### 22. **MES Tracking Model Completeness**
- **Issue:** Faltan campos: alias, target, comment, user_ids, reject_time
- **Fix:** Extender modelo + endpoints
- **Estimado:** 2h
- **Criticidad:** BAJA

---

### 23. **MES Enum Migration to Master Data**
- **Issue:** `WOType`, `ProdIssueType`, `IssueType` son PostgreSQL nativos
- **Fix:** Migrar a tabla `enumerations` en master_data (configurable por tenant)
- **Estimado:** 2h
- **Criticidad:** BAJA (mejor arquitectura)

---

### 24. **Stripe Self-Service Checkout**
- **Issue:** Tenants UNPAID no pueden pagar
- **Fix:** Implementar embedded Stripe Checkout
- **Estimado:** 3h
- **Criticidad:** BAJA (feature futura)

---

### 25. **Mobile Offline Buffer (SQLite)**
- **Issue:** Sin conectividad → app cae
- **Fix:** SQLite local buffer + sync al volver online
- **Estimado:** 5h (Flutter + sync logic)
- **Criticidad:** BAJA (Phase 180+)

---

## 📊 RESUMEN POR CRITICIDAD

### 🔴 CRÍTICAS BLOQUEADAS (5 tareas)
| Tarea | Estimado | Bloqueador |
|-------|----------|-----------|
| RTR Phase D Integración | 1h | auth_service validation |
| Promotion Service | 4h | HCM Phase 3 |
| POS Checkout E2E | 2h | auth_service estable |
| Shift-End Auto-Logout | 3h | APScheduler setup |
| Headcount Recompute | 2.5h | outbox pattern |
| **SUBTOTAL** | **12.5h** | |

### 🟠 OPERACIONALES (7 tareas)
| Tarea | Estimado | Bloquea Piso |
|-------|----------|-------------|
| NAIVE_DATETIME Fixes | 0.5h | ❌ No |
| Master Data Clients | 1.5h | ❌ No (fallback) |
| HCM Phase 2 | 7.5h | ❌ No |
| HCM Phase 3 | 22h | ❌ No (validación) |
| HCM Phase 4 | 4.5h | ❌ No (fallback) |
| HCM Phase 5 | 4h | ❌ No |
| HCM Phase 6 | 2h | ❌ No |
| **SUBTOTAL** | **42h** | |

### 🟡 INFRASTRUCTURE (3 tareas)
| Tarea | Estimado |
|-------|----------|
| AWS WAF | 2h |
| Observability | 1.5h |
| Cloud Deployment | 6-8h |
| **SUBTOTAL** | **9.5-11.5h** |

### 🔵 TECH DEBT (11 tareas)
| Tarea | Estimado |
|-------|----------|
| Domain Purity Refactor | 1h |
| WMS Deployment | 1.5h |
| Mobile AVD Testing | 2h |
| Price Agreement Context | 1h |
| MES Routing | 3h |
| MES Metrics | 2h |
| MES Tracking | 2h |
| MES Enum Migration | 2h |
| Stripe Checkout | 3h |
| Mobile Offline Buffer | 5h |
| **SUBTOTAL** | **22.5h** |

---

## 📅 PLAN RECOMENDADO (12 semanas)

### Week 1-2: Validaciones Críticas (12.5h)
- [ ] RTR Phase D integración + validation
- [ ] POS Checkout E2E script execution
- [ ] Shift-End Auto-Logout implementation
- [ ] NAIVE_DATETIME fixes

### Week 3-4: HCM Phase 2 (7.5h)
- [ ] Position, Skill, Certification models

### Week 5-7: HCM Phase 3 (22h)
- [ ] Kardex transactional + EligibilityService
- [ ] Headcount recompute integration
- [ ] Promotion Service implementation

### Week 8: HCM Phase 4-5 (8.5h)
- [ ] TimeRecord, WorkCalendar, Medical, PPE

### Week 9: HCM Phase 6 (2h)
- [ ] Reporting

### Week 10: Infrastructure (9.5-11.5h)
- [ ] AWS WAF + Observability
- [ ] Load testing

### Week 11-12: Cloud Deployment + Testing (6-8h)
- [ ] Phase 180 — AWS ECS/App Runner
- [ ] Performance tuning
- [ ] Mobile E2E testing

---

## ✅ Principio "Best-Effort" — Cómo Implementar

Para cada tarea operacional:

```python
# NUNCA:
if kardex_write_failed:
    raise Exception("Cannot continue")  # ❌ BLOQUEA PISO

# SIEMPRE:
try:
    kardex.write_event(event)
    logger.info("Kardex event written", extra={...})
except Exception as e:
    logger.critical("Kardex write failed, continuing anyway", 
                    exc_info=True, extra={...})
    notify_admin("Manual Kardex reconciliation needed for {collaborator_id}")
    # Continue serving the request
    return {"status": "created", "warning": "Kardex pending"}
```

---

## 🎯 Próximos 7 Días

1. **Hoy:** RTR Phase D integración validation (1h)
2. **Mañana:** POS Checkout E2E script execution (2h)
3. **Miércoles:** NAIVE_DATETIME fixes (0.5h)
4. **Jueves-Viernes:** Shift-End Auto-Logout + Headcount recompute (5.5h)
5. **Semana Next:** HCM Phase 2 kick-off

---

**Generado:** 2026-06-03  
**Próxima revisión:** Al completar Week 2 (validaciones críticas)  
**Responsable:** Tech Lead + Architects
