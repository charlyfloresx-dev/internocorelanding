# HCM Service — Roadmap de Implementación (Phase 161+)

**Versión:** 1.0  
**Fecha:** 2026-06-03  
**Basado en:** Análisis de legacy .NET + Arquitectura Kardex Transaccional + Integración Outset Medical  
**Responsable:** Arquitecto HCM (Carlos Flores)  

---

## 📌 Contexto Operativo

El **Kardex del Colaborador** es el expediente transaccional definitivo de la vida laboral dentro de cada empresa (`company_id`). Impacta:

1. **Elegibilidad de Promoción Interna** — "Kardex Limpio" (sin infracciones en 90 días)
2. **Disponibilidad de Personal (Headcount)** — Usado por MES para planeación
3. **Nómina y Finanzas** — Cálculo de impacto salarial
4. **Auditoría y Cumplimiento** — Registro inmutable de eventos

---

## 🗂️ Plan por Fase

### Phase 1: ✅ COMPLETADO — Base Estructural

| Tarea | Estado | Notas |
|-------|--------|-------|
| Collaborator model + MultiTenantBase | ✅ | Exist with `supervisor_id`, `manager_id`, `director_id` |
| Department CRUD | ✅ | Phase 158 completado |
| Shift model base | ✅ | Con cálculo de horas disponibles |
| Jerarquía 3 niveles (Supervisor→Manager→Director) | ✅ | Phase 158 completado |
| Auth integration (`user_id`) | ✅ | JWT mapping funcional |

---

### Phase 2: ⏳ PRÓXIMA — Motor de Competencias y Posiciones

#### **PR-HCM-001: Position Model (JobPosition Legacy)**
- [ ] Crear modelo `Position` (mapeo de `JobPosition` C# legacy)
- [ ] Campos: name, department_id, salary_range_from, salary_range_to, description
- [ ] CRUD endpoints: `GET /positions`, `POST /positions`, `PATCH /positions/{id}`, `DELETE /positions/{id}`
- [ ] Tests: 10+ unit tests
- **Estimado:** 2h

#### **PR-HCM-002: Skill Model (Competencias)**
- [ ] Crear modelo `Skill` con categorías (TECHNICAL / BEHAVIORAL / MANAGEMENT)
- [ ] Endpoint de validación: `GET /internal/skills/{skill_name}`
- [ ] Tests: 8+ tests
- **Estimado:** 1.5h

#### **PR-HCM-003: CollaboratorSkill Link**
- [ ] Modelo `CollaboratorSkill` (asignación de nivel a colaborador)
- [ ] Endpoints: POST/PATCH/DELETE/GET skills
- [ ] Tests: 12+ tests
- **Estimado:** 2h

#### **PR-HCM-004: Certification Model**
- [ ] Modelo `Certification` (Certificaciones formales)
- [ ] Domain event: `CertificationExpiringAlert` (30 días antes)
- [ ] Tests: 10+ tests
- **Estimado:** 2h

**Phase 2 Total:** 7.5h (Timeline: 2 semanas)

---

### Phase 3: 🔄 EN PROGRESO — Kardex Transaccional (CRÍTICA)

#### **PR-HCM-005: PermissionDocument Model (HEADER)**
- [ ] Crear modelo `PermissionDocument` (cabecera de solicitud)
- [ ] Estados: DRAFT → PENDING_SUPERVISOR → PENDING_RH → POSTED
- [ ] Campos: document_type, status, supervisor_id, hr_approver_id, timestamps
- [ ] Tests: 15+ tests (state transitions, auth, validations)
- **Estimado:** 3h

#### **PR-HCM-006: PermissionMovement Model (DETAIL)**
- [ ] Crear modelo `PermissionMovement` (líneas del documento)
- [ ] Campos: document_id, start_date, end_date, movement_type, quantity_days, salary_impact, is_salaried
- [ ] Tests: 12+ tests
- **Estimado:** 2.5h

#### **PR-HCM-007: KardexEvent Model (Append-Only)**
- [ ] Crear modelo `KardexEvent` (registro inmutable de eventos)
- [ ] Campos: event_type, affects_eligibility, eligibility_penalty_until, description
- [ ] Restricciones: NO UPDATE / DELETE (append-only)
- [ ] Event listeners SQLAlchemy bloquean modificaciones
- [ ] Tests: 10+ tests (immutability, penalties, querying)
- **Estimado:** 2h

#### **PR-HCM-008: PermissionService (Orchestration)**
- [ ] Crear `PermissionService` que orquesta el flujo de aprobación
- [ ] Métodos: create_permission_request, approve_by_supervisor, approve_and_post_by_rh
- [ ] Lógica: DRAFT → PENDING_RH → POSTED → Kardex escrito + outbox publicado
- [ ] Atomicidad: usar `begin_nested()` para transacciones
- [ ] Tests: 20+ tests (flujos completos, validaciones, atomicidad)
- **Estimado:** 4h

#### **PR-HCM-009: EligibilityService (Validación de Kardex)**
- [ ] Crear `EligibilityService` para validar elegibilidad de promoción
- [ ] Métodos: is_eligible_for_promotion(), get_eligibility_status()
- [ ] Lógica: Query KardexEvent donde `affects_eligibility=True` en últimos 90 días
- [ ] Tests: 15+ tests (happy path, edge cases, multi-tenant)
- **Estimado:** 2h

#### **PR-HCM-010: /internal/check-eligibility Endpoint** ⭐ CRÍTICA
- [ ] Endpoint: `GET /internal/check-eligibility/{collaborator_id}?company_id={id}`
- [ ] Consumidores: Promotion Service (antes de permitir candidatura)
- [ ] Tests: 8+ tests (auth, filtering, responses)
- **Estimado:** 1h

#### **PR-HCM-011: Permission Endpoints (CRUD + State Transitions)**
- [ ] Endpoints: POST/GET/PATCH/DELETE permissions, approve-supervisor, approve-rh, reject
- [ ] Validaciones: No editar post-PENDING, no deshacer firmas
- [ ] Tests: 25+ tests (CRUD, state, auth, boundaries)
- **Estimado:** 3h

#### **PR-HCM-012: Kardex Query & Audit Endpoint**
- [ ] Endpoint: `GET /collaborators/{id}/kardex?from_date={date}&to_date={date}`
- [ ] Paginación: 50 items por página
- [ ] Acceso: Solo RH y el mismo colaborador
- [ ] Tests: 12+ tests (auth, filtering, pagination)
- **Estimado:** 1.5h

#### **PR-HCM-013: MES Integration (Headcount Recompute)**
- [ ] Crear `MESClient` en `infrastructure/clients/mes_client.py`
- [ ] Lógica: PermissionDocumentPosted → MES recomputa headcount
- [ ] Resiliencia: best-effort, no bloquea la aprobación
- [ ] Tests: 8+ tests (HTTP calls, error handling)
- **Estimado:** 2h

**Phase 3 Total:** 22h (Timeline: 3 semanas, 3 PRs/semana)

---

### Phase 4: ⏳ Control Avanzado de Tiempo (T&A Advanced)

#### **PR-HCM-014: TimeRecord Model (RFID/Biometric)**
- [ ] Modelo `TimeRecord` (entradas/salidas)
- [ ] Campos: collaborator_id, recorded_at, record_type (CLOCK_IN/CLOCK_OUT), source (RFID/BIOMETRIC/MANUAL)
- [ ] Endpoints: POST /clock-in, POST /clock-out, GET /time-records/{id}
- [ ] RFID Security: validar hash usando salt
- [ ] Tests: 15+ tests
- **Estimado:** 3h

#### **PR-HCM-015: WorkCalendar Model**
- [ ] Modelo `WorkCalendar` (días especiales)
- [ ] Campos: company_id, date, type (HOLIDAY/WORKDAY/PLANNED_SHUTDOWN), description
- [ ] CRUD endpoints
- [ ] Tests: 8+ tests
- **Estimado:** 1.5h

**Phase 4 Total:** 4.5h (Timeline: 1 semana)

---

### Phase 5: ⏳ Seguridad y EHS

#### **PR-HCM-016: MedicalRecord Model (Zero Trust)**
- [ ] Modelo `MedicalRecord` (expediente médico privado)
- [ ] Acceso: Solo rol `MEDICAL_STAFF`
- [ ] Logs de auditoría de cada acceso
- [ ] Tests: 10+ tests (access control, logging)
- **Estimado:** 2h

#### **PR-HCM-017: PPERecord Model**
- [ ] Modelo `PPERecord` (Equipo de Protección Personal)
- [ ] Campos: collaborator_id, position_id, delivery_date, equipment_type, cost (Money VO), center_code
- [ ] Integración: publicar evento `PPEDelivered` → ERP genera costo
- [ ] Tests: 10+ tests
- **Estimado:** 2h

**Phase 5 Total:** 4h (Timeline: 1 semana)

---

### Phase 6: ⏳ Analytics y Reporting

#### **PR-HCM-018: Kardex Reports**
- [ ] Endpoint: `GET /reports/kardex?company_id={id}&from={date}&to={date}`
- [ ] Agregaciones por tipo de evento, violaciones por departamento
- [ ] Rendimiento: < 2 segundos para 1M registros
- [ ] Tests: 5+ tests
- **Estimado:** 2h

**Phase 6 Total:** 2h (Timeline: 1 semana)

---

## 📊 Resumen de Esfuerzo

| Phase | Tareas | Estimado Total | Timeline |
|-------|--------|-----------------|----------|
| 1 (Base) | — | ✅ Completado | — |
| 2 (Skills) | 4 PRs | 7.5h | 2 semanas |
| 3 (Kardex) | 9 PRs | 22h | 3 semanas |
| 4 (T&A) | 2 PRs | 4.5h | 1 semana |
| 5 (Seguridad) | 2 PRs | 4h | 1 semana |
| 6 (Reporting) | 1 PR | 2h | 1 semana |
| **TOTAL PHASES 2-6** | **18 PRs** | **~40h** | **~8-9 semanas** |

**Recomendación de Sprint:** 2 PRs por semana (1 grande + 1 pequeña), ~20h/semana

---

## 🔗 Dependencias Críticas

```
RTR Phase D (1h)
    ↓
Promotion Service (4h) ← bloqueado por HCM-010 ⭐

Phase 2 (Skills) — 7.5h
    ↓
Phase 3 (Kardex) — 22h (es el bloqueador mayor)
    ├─ PR-HCM-010 es CRÍTICA (GET /internal/check-eligibility)
    │   ↓ Unblocks Promotion Service
    └─ PR-HCM-013 integra con MES (headcount recompute)

Phase 4 (T&A) — 4.5h (puede hacerse en paralelo parcialmente)
Phase 5 (Seguridad) — 4h (puede hacerse en paralelo)
Phase 6 (Reporting) — 2h (al final)
```

---

## ✅ Checklist de Aceptación Global

- [ ] Todos los modelos heredan `MultiTenantBase`
- [ ] Todos los endpoints requieren `company_id` en contexto JWT
- [ ] Code Graph audit: 0 CRITICAL, 0 violations
- [ ] Tests de integración contra `hcm_db` real
- [ ] SERVICE_LOG.md actualizado por cada Phase
- [ ] REPO_LOG.md actualizado con decisiones arquitectónicas
- [ ] Documentación de API OpenAPI completa
- [ ] Integración MES funcional (outbox → headcount recompute)
- [ ] Permission flow end-to-end: DRAFT → POSTED → Kardex escrito
- [ ] Elegibilidad validada: sin infracciones en 90 días = True

---

## 🎯 Hitos Clave

1. **Semana 1-2:** RTR Phase D + POS Checkout E2E + Shift-End Auto-Logout (críticos bloqueadores)
2. **Semana 3-4:** HCM Phase 2 (Motor de Competencias)
3. **Semana 5-7:** HCM Phase 3 (Kardex Transaccional) ⭐ CRÍTICA
4. **Semana 8:** HCM Phase 4-5 (T&A + Seguridad)
5. **Semana 9:** HCM Phase 6 (Reporting)
6. **Semana 10:** Infrastructure (AWS WAF + Observability)
7. **Semana 11-12:** Cloud Deployment + Testing

---

**Próxima revisión:** Después de completar Phase 3 (Kardex)  
**Responsable de seguimiento:** Arquitecto HCM + Tech Lead
