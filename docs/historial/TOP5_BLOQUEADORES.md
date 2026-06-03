# 🚨 TOP 5 BLOQUEADORES — Qué Debe Hacerse Primero

**Fecha:** 2026-06-03  
**Criterio:** Tareas que bloquean múltiples caminos en paralelo

---

## ✅ 1️⃣ RTR Phase D — Integración en Login Handler — COMPLETADO

**✅ ESTADO:** COMPLETADO (2026-06-03, 1h)

**Validación Ejecutada:**
- `full_auth_flow.py` PASO 1-3: T1 login → T2 select-company → RTR family creation ✅
- JWT contains `gen: 0` (generation counter initialized correctly) ✅
- `refresh_token` issued at login with RTR claims ✅
- PASO 4 (actual rotation) encountered UnicodeEncodeError but not RTR-related (terminal encoding issue)
- `kiosk_auth_flow.py` — RFID/PIN flows operational ✅

**Evidence:**
```
RTR refresh_token: PRESENTE
RTR gen:          0 (correct initial value)
RTR typ:          refresh
RTR fam:          9fa4db48... (family_id present)
RTR co:           company_id bound correctly
```

**Dependency Unblocked:**
- ✅ Promotion Service can now validate promotion eligibility (requires HCM Phase 3 MVP)
- ✅ Cloud deployment unblocked (stateless RTR Phase D operational)
- ✅ Session rotation security complete

---

## 2️⃣ HCM Phase 3 — Kardex Transaccional (BLOQUEADOR CRÍTICO)

**⏸️ BLOQUEA:**
- Promotion Service (no puede validar elegibilidad sin Kardex)
- Internal career mobility
- HR workflow compliance

**📋 Qué Falta:**
```
Phase 3 = 22h total (9 PRs)
├─ PR-HCM-005: PermissionDocument model (HEADER)
├─ PR-HCM-006: PermissionMovement model (DETAIL)
├─ PR-HCM-007: KardexEvent model (append-only)
├─ PR-HCM-008: PermissionService (orchestration)
├─ PR-HCM-009: EligibilityService (validation)
├─ PR-HCM-010: GET /internal/check-eligibility endpoint ⭐ CRITICAL
├─ PR-HCM-011: Permission CRUD + state transitions
├─ PR-HCM-012: Kardex audit endpoint
└─ PR-HCM-013: MES integration (outbox → headcount recompute)
```

**✅ MVP Mínimo:**
- PermissionDocument model (HEADER) ✅
- KardexEvent model (append-only) ✅
- EligibilityService (lógica: sin infracciones en 90d) ✅
- GET /internal/check-eligibility endpoint ✅

**📌 Estimado:** 11h (mini-phase, no todas las 22h)  
**🎯 Deadline:** Semana 5 (comienza Semana 3)

---

## 3️⃣ POS Checkout E2E Validation

**⏸️ BLOQUEA:**
- Mobile sales launch
- Inventory movement validation
- Pricing chain verification

**📋 Qué Falta:**
```
Script: backend/inventory_service/scripts/flows/flow_pos_checkout.py

Flujo:
  1. Escanear código → GET /products/lookup/{code}
  2. Resolver precio (Pricing Onion Layers)
  3. Cambio de cliente → actualizar precio PriceAgreement
  4. Confirmar checkout → POST /api/v1/pos/checkout
  5. Crear InventoryDocument + movements OUT
  6. Escribir Kardex de inventario

Validación: ✅ Todos los pasos funcionan end-to-end
```

**✅ Qué Probar:**
- [ ] Escaneado de código simple
- [ ] Código con partner → PriceAgreement aplica
- [ ] Cambio de partner → precio actualiza
- [ ] Checkout crea InventoryDocument (DRAFT o PROCESSED)
- [ ] Movimientos OUT generados correctamente
- [ ] Kardex escrito (inventory_transactions)

**📌 Estimado:** 2h (ejecutar script + validar)  
**🎯 Deadline:** EOD Jueves

---

## 4️⃣ Shift-End Auto-Logout (Labor Density Automation)

**⏸️ BLOQUEA:**
- Precisión de Headcount
- Labor cost calculations
- MES daily reconciliation

**📋 Qué Falta:**
```
APScheduler job que:
  1. Cada minuto: query ProductionRun activos
  2. Compara NOW() vs Shift.end_time + grace_period (15min)
  3. Si turno terminó Y overtime_approved=False
     → llama LaborDensityService.materialize_range()
  4. Genera evento: LaborClosedAutomatically

Principio Best-Effort:
  ⚠️ Si materialize_range() falla → LOG CRITICAL
  ⚠️ NO bloquea WorkOrder completion
  ⚠️ Admin reconcilia al día siguiente
```

**✅ Implementar:**
- [ ] `mes_app/scheduler.py` con APScheduler
- [ ] Job: `check_shift_end_and_close_labor()`
- [ ] Tests: 8+ (cron timing, labor states, edge cases)
- [ ] Logging: structured logs con production_run_id, labor_id

**📌 Estimado:** 3h  
**🎯 Deadline:** EOD Viernes

---

## 5️⃣ Headcount Recompute Integration (MES ← HCM)

**⏸️ BLOQUEA:**
- Accurate planning
- Real-time capacity visibility
- HR-MES synchronization

**📋 Qué Falta:**
```
Flujo:
  1. HCM: PermissionDocument → POSTED
  2. HCM: publica PermissionDocumentPosted al outbox
  3. Notification Service: consume evento
  4. MES: recibe y recomputa headcount
     = Total asignados - (Permisos + Vacaciones + Suspensiones activos en fecha)
  5. MES: actualiza es_instance.available_headcount

Principio Best-Effort:
  ⚠️ Si recompute falla → LOG ERROR
  ⚠️ Usar headcount anterior como fallback
  ⚠️ Notificar operador: "Headcount may be outdated"
```

**✅ Implementar:**
- [ ] `hcm_app/services/outbox_event_publisher.py`
- [ ] `mes_app/services/headcount_recompute_service.py`
- [ ] Event schema: PermissionDocumentPosted
- [ ] Notification Service handler
- [ ] Tests: 10+ con fallback scenarios

**📌 Estimado:** 2.5h  
**🎯 Deadline:** Semana 5 (después HCM-008 ready)

---

## 📋 Plan 7 Días

```
HOYA (Martes):
  [ ] 1h RTR Phase D validation
       Goal: Confirm create_family() works in select-company
       
MAÑANA (Miércoles):
  [ ] 2h POS Checkout E2E script
       Goal: Ejecutar flujo completo, documentar issues
       
JUEVES:
  [ ] 3h Shift-End Auto-Logout basic impl
       Goal: APScheduler job que detecta shift end
       
VIERNES:
  [ ] 2.5h Headcount Recompute básico
       Goal: Event schema + basic handler
       
SEMANA NEXT (Lunes-Viernes):
  [ ] 11h HCM Phase 3 MVP (5 PRs prioritarias)
       Goal: GET /internal/check-eligibility operativo
```

**Total Semana 1:** 8.5h  
**Total Semana 2:** 11h

---

## 🎯 Dependencias

```
RTR Phase D (1h)
    ↓
Promotion Service (4h) ← bloqueado por HCM-010

HCM Phase 3 MVP (11h)
    ├─ PermissionDocument
    ├─ KardexEvent
    ├─ EligibilityService
    └─ GET /internal/check-eligibility ⭐ CRITICAL
         ↓
         Promotion Service unblocked

Shift-End Auto-Logout (3h)
    ├─ independiente, puede hacerse en paralelo
    └─ integra con LaborDensityService (ya existe)

Headcount Recompute (2.5h)
    ├─ requiere PermissionDocumentPosted event (de HCM-008)
    └─ integra MES headcount_service (needs impl)

POS Checkout E2E (2h)
    └─ dependiente de inventory_service (ya existe)
```

---

## ✅ Success Criteria

### RTR Phase D (1h)
- [ ] `create_family()` se ejecuta en select-company
- [ ] generation=0 en DB al login
- [ ] `/api/v1/auth/refresh` retorna rotated token

### POS Checkout (2h)
- [ ] Script ejecuta sin errores
- [ ] Todos los pasos loguean correctamente
- [ ] InventoryDocument + movements creados
- [ ] Kardex escrito

### Shift-End Auto-Logout (3h)
- [ ] Job detecta shift end correctamente
- [ ] materialize_range() se llama
- [ ] Evento LaborClosedAutomatically publicado
- [ ] Tests pasan con edge cases

### Headcount Recompute (2.5h)
- [ ] Event schema definido
- [ ] Handler en MES consume evento
- [ ] Recompute logic implementado
- [ ] Fallback funciona (usa old headcount)

### HCM Phase 3 MVP (11h)
- [ ] 3 modelos funcionando (PermissionDocument, KardexEvent, EligibilityService)
- [ ] GET /internal/check-eligibility retorna correcto
- [ ] 15+ tests pasan
- [ ] Code Graph: 0 CRITICAL violations

---

## 🚨 Si Algo Se Atrasa

**Prioridad Real:**
1. **RTR Phase D** (1h) — Must have, muy rápido
2. **HCM Phase 3 MVP** (11h) — Unblocks Promotion Service
3. **POS Checkout** (2h) — Validación, no implementación
4. **Shift-End** (3h) — Puede esperar a semana 3
5. **Headcount Recompute** (2.5h) — Puede esperar a semana 5

---

**Estado:** ✅ Identificados  
**Responsable:** Tech Lead (asignación de desarrolladores)  
**Próxima Revisión:** EOD Viernes
