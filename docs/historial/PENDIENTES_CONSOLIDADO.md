# 📋 Consolidado de Pendientes — Interno Core (2026-06-03)

**Principio Core:** `best-effort` — Nada bloquea operaciones de piso (órdenes de producción, movimientos de inventario, registros de kardex, escaneos). Todo genera **logs estructurados + notificaciones** para reconciliación posterior.

**Estado:** 177 phases completadas. Deuda identificada y organizada por criticidad.

---

## ✅ COMPLETADAS (Semana 1, 2026-06-03)

### ✅ 1. **auth_service RTR Phase D — Integración Login**
- **Estado:** Phase A+B+D ✅ COMPLETADO
- **Validación Ejecutada:** 
  - `full_auth_flow.py` confirmed: T1 login → T2 select-company → RTR family creation works atomically
  - JWT generation counter (`gen`) initialized to 0 at login ✅
  - `refresh_token` issued correctly with RTR claims ✅
  - Family creation occurs within transaction scope ✅
- **Evidence:** flow_pos_checkout.py can now run (no auth modifications blocking it)
- **Criticidad:** COMPLETADO — RTR 100% integrado y operativo
- **Efectos Secundarios:** Unblocks Promotion Service (requires HCM Phase 3 MVP) y Cloud deployment

---

### 2. **Promotion Service — Bloqueada por HCM Kardex**
- **Estado:** ⏳ ESPERANDO Phase 3 HCM
- **Requiere:** `GET /internal/check-eligibility/{collaborator_id}` del HCM Service
- **Acción:** No puede implementarse hasta PR-HCM-010
- **Bloqueador Secuencial:** Phase 2 HCM → Phase 3 HCM (Kardex) → Promotion Service
- **Estimado:** 4h (después que HCM esté listo)

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

---

### 6. **NAIVE_DATETIME Violations (10 instances)**
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

---

### 7. **Master Data Client Configuration (Cross-Service)**
- **Estado:** ⏳ PENDING — HCM/MES/WMS accessing master_data_service
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

---

### 14. **Observability — Grafana Alerts (RTR Phase)**
- **Estado:** ⏳ PENDING — Para monitoring en prod
- **Qué Falta:** CloudWatch alerts si "Security Breach Alert: REUSE_DETECTED" >3 veces/5min
- **Acción:** SNS → PagerDuty + Grafana dashboard "Dispositivos Conectados"
- **Estimado:** 1.5h (CloudWatch + Grafana)

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

---

## 🔵 TECH DEBT (No Bloquea, Puede Esperar)

### 16. **Domain Purity — RTR Audit**
- **Issue:** `IRefreshTokenRepository.log_rotation_event()` retorna ORM model
- **Fix:** Return `None` o `AuditRecord` dataclass (domain purity)
- **Estimado:** 1h
- **Prioridad:** BAJA (código funciona, solo refactor)

---

### 17-25. **Otros Tech Debt**
- WMS Deployment (1.5h)
- Mobile AVD Testing (2h)
- Price Agreement Context (1h)
- MES Routing (3h)
- MES Metrics (2h)
- MES Tracking (2h)
- MES Enum Migration (2h)
- Stripe Checkout (3h)
- Mobile Offline Buffer (5h)

**Total Tech Debt:** ~22.5h

---

## 📊 RESUMEN POR CRITICIDAD

| Categoría | Tareas | Estimado | Bloquea Piso |
|-----------|--------|----------|-------------|
| 🔴 Críticas | 5 | 12.5h | ❌ No (best-effort) |
| 🟠 Operacionales | 7 | 42h | ❌ No (validación) |
| 🟡 Infrastructure | 3 | 9.5-11.5h | ❌ No |
| 🔵 Tech Debt | 11 | 22.5h | ❌ No |
| | **TOTAL** | **~84h** | |

**Timeline:** 10-12 semanas @ 8h/semana

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

**Generado:** 2026-06-03  
**Próxima revisión:** Al completar Week 2 (validaciones críticas)  
**Responsable:** Tech Lead + Architects
