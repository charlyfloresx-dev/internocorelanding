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

**Aceptación:**
- [ ] Crear modelo `Position` (mapeo de `JobPosition` C# legacy)
- [ ] Campos: name, department_id, salary_range_from, salary_range_to, description
- [ ] Relación: 1:N con Collaborator (un colaborador en una posición)
- [ ] CRUD endpoints: `GET /positions`, `POST /positions`, `PATCH /positions/{id}`, `DELETE /positions/{id}`
- [ ] Rate limit: 30/minute
- [ ] Tests: 10+ unit tests (validation, CRUD, multi-tenant isolation)

**Estimado:** 2h  
**Archivos:**
- `hcm_app/models/position.py`
- `hcm_app/schemas/position.py`
- `hcm_app/api/v1/endpoints/positions.py`
- `hcm_app/infrastructure/repositories/position_repository.py`
- `tests/integration/test_positions.py`

---

#### **PR-HCM-002: Skill Model (Competencias)**

**Aceptación:**
- [ ] Crear modelo `Skill` (Competence legacy con evolución)
- [ ] Campos: name, description, category (TECHNICAL / BEHAVIORAL / MANAGEMENT), level_min (TRAINEE/JUNIOR/INTERMEDIATE/EXPERT)
- [ ] MultiTenantBase: cada empresa tiene su catálogo de skills
- [ ] Endpoint de validación: `GET /internal/skills/{skill_name}?company_id={id}`
- [ ] Rate limit: 30/minute
- [ ] Tests: 8+ tests de validación y filtro

**Estimado:** 1.5h  
**Archivos:**
- `hcm_app/models/skill.py`
- `hcm_app/schemas/skill.py`
- `hcm_app/api/v1/endpoints/skills.py`
- `hcm_app/infrastructure/repositories/skill_repository.py`

---

#### **PR-HCM-003: CollaboratorSkill Link**

**Aceptación:**
- [ ] Modelo `CollaboratorSkill` (asignación de nivel a colaborador)
- [ ] Campos: collaborator_id, skill_id, current_level, achieved_at, expires_at (opcional)
- [ ] Endpoints:
  - `POST /collaborators/{id}/skills` (asignar skill)
  - `PATCH /collaborators/{id}/skills/{skill_id}` (actualizar nivel)
  - `DELETE /collaborators/{id}/skills/{skill_id}` (remover skill)
  - `GET /collaborators/{id}/skills` (listar skills)
- [ ] Tests: 12+ tests (assignment, level validation, deletion)

**Estimado:** 2h  
**Archivos:**
- `hcm_app/models/collaborator_skill.py`
- `hcm_app/schemas/collaborator_skill.py`
- `hcm_app/api/v1/endpoints/collaborator_skills.py`

---

#### **PR-HCM-004: Certification Model**

**Aceptación:**
- [ ] Modelo `Certification` (Certificaciones formales)
- [ ] Campos: collaborator_id, cert_name, issued_at, expires_at, certification_body, cert_number
- [ ] Validaciones: expires_at > issued_at, no expiry futuro > 10 años
- [ ] Domain event: `CertificationExpiringAlert` (30 días antes) → Notification Service
- [ ] Endpoint: `GET /collaborators/{id}/certifications`
- [ ] Tests: 10+ tests

**Estimado:** 2h  
**Archivos:**
- `hcm_app/models/certification.py`
- `hcm_app/schemas/certification.py`
- `hcm_app/services/certification_alerts_service.py`
- `hcm_app/domain/events/certification_events.py`

---

### Phase 3: 🔄 EN PROGRESO — Kardex Transaccional (Phase 161+)

#### **PR-HCM-005: PermissionDocument Model (HEADER)**

**Aceptación:**
- [ ] Crear modelo `PermissionDocument` (cabecera de solicitud)
- [ ] Campos:
  - `company_id, collaborator_id, document_type` (PERMISSION/VACATION/SUSPENSION)
  - `status` (DRAFT → PENDING_SUPERVISOR → PENDING_RH → POSTED)
  - `supervisor_id, supervisor_signed_at` (Firma 1)
  - `hr_approver_id, hr_posted_at` (Firma 2)
  - `notes, created_at, updated_at`
- [ ] Validaciones:
  - Solo RH puede marcar como POSTED
  - POSTED requiere ambas firmas
  - Transición de estado: solo avance permitido, no retroceso
- [ ] Estado de máquina:
  ```
  DRAFT ──POST → PENDING_SUPERVISOR
  PENDING_SUPERVISOR ──approve_supervisor → PENDING_RH
  PENDING_RH ──approve_rh/post → POSTED
  ```
- [ ] Tests: 15+ tests (state transitions, auth, validations)

**Estimado:** 3h  
**Archivos:**
- `hcm_app/models/permission_document.py`
- `hcm_app/schemas/permission_document.py`
- `hcm_app/api/v1/endpoints/permission_documents.py` (POST, PATCH status)
- `hcm_app/infrastructure/repositories/permission_document_repo.py`

---

#### **PR-HCM-006: PermissionMovement Model (DETAIL)**

**Aceptación:**
- [ ] Crear modelo `PermissionMovement` (líneas del documento)
- [ ] Campos:
  - `document_id, start_date, end_date`
  - `movement_type` (PERMISSION_DAY / VACATION_DAY / SUSPENSION)
  - `quantity_days (int)`
  - `salary_impact (Numeric 18,4)` (monto deducido/acreditado)
  - `is_salaried (bool)` (con/sin goce de sueldo)
- [ ] Validaciones:
  - end_date > start_date
  - Si is_salaried=True, salary_impact=0
  - Si is_salaried=False, salary_impact > 0
- [ ] Cálculo automático de `quantity_days` basado en start_date/end_date y tipo de movimiento
- [ ] Tests: 12+ tests

**Estimado:** 2.5h  
**Archivos:**
- `hcm_app/models/permission_movement.py`
- `hcm_app/schemas/permission_movement.py`

---

#### **PR-HCM-007: KardexEvent Model (Append-Only)**

**Aceptación:**
- [ ] Crear modelo `KardexEvent` (registro inmutable de eventos)
- [ ] Campos:
  - `company_id, collaborator_id`
  - `event_type` (AMONESTACION / SUSPENSION / PERMISSION / VACATION / FALTA_INJUSTIFICADA)
  - `document_reference` (FK opcional a permission_documents.id)
  - `affects_eligibility (bool)` — si impacta elegibilidad de promoción
  - `eligibility_penalty_until (datetime)` — fecha de expiración de penalización (90 días desde now)
  - `description (str)` — texto libre del evento
  - `created_at (immutable datetime)`
- [ ] Restricciones:
  - NO UPDATE / DELETE permitidos (append-only)
  - Event listeners SQLAlchemy bloquean modificaciones
- [ ] Índices: (company_id, collaborator_id, created_at) para queries rápidas
- [ ] Tests: 10+ tests (immutability, penalties, querying)

**Estimado:** 2h  
**Archivos:**
- `hcm_app/models/kardex_event.py`
- `hcm_app/infrastructure/event_listeners/kardex_listeners.py` (bloquear UPDATE/DELETE)

---

#### **PR-HCM-008: PermissionService (Orchestration)**

**Aceptación:**
- [ ] Crear `PermissionService` que orquesta el flujo de aprobación
- [ ] Métodos:
  - `create_permission_request(collaborator_id, document_type, movements[], notes) → PermissionDocument`
  - `approve_by_supervisor(document_id, supervisor_id) → updated_document`
  - `approve_and_post_by_rh(document_id, hr_approver_id) → posted_document`
  - `reject_by_supervisor(document_id, reason) → updated_document`
  - `reject_by_rh(document_id, reason) → updated_document`
- [ ] Lógica:
  - Al crear: status = DRAFT
  - Al aprobar supervisor: status = PENDING_RH, valida headcount con MES (consulta)
  - Al aprobar RH:
    - status = POSTED
    - Escribe evento(s) en KardexEvent
    - Publica `PermissionDocumentPosted` al outbox
    - MES consume y recomputa headcount
    - Nómina procesa salary_impact
- [ ] Atomicidad: usar `begin_nested()` para transacciones
- [ ] Tests: 20+ tests (flujos completos, validaciones, atomicidad)

**Estimado:** 4h  
**Archivos:**
- `hcm_app/services/permission_service.py`
- `hcm_app/domain/commands/create_permission_command.py`
- `hcm_app/domain/commands/approve_permission_command.py`

---

#### **PR-HCM-009: EligibilityService (Validación de Kardex)**

**Aceptación:**
- [ ] Crear `EligibilityService` para validar elegibilidad de promoción
- [ ] Métodos:
  - `is_eligible_for_promotion(collaborator_id, as_of_date=NOW) → bool`
  - `get_eligibility_status(collaborator_id) → EligibilityStatus dataclass`
    - `is_eligible: bool`
    - `last_violation_date: datetime | None`
    - `penalty_expires_at: datetime | None`
    - `active_violations: List[KardexEvent]`
- [ ] Lógica:
  - Query: `KardexEvent` donde `affects_eligibility=True` y `collaborator_id=X` en últimos 90 días
  - Si `eligibility_penalty_until > NOW`, retorna False
  - Si no hay violaciones en 90 días, retorna True
- [ ] Validaciones: siempre filtrar por `company_id` del contexto
- [ ] Tests: 15+ tests (happy path, edge cases, multi-tenant)

**Estimado:** 2h  
**Archivos:**
- `hcm_app/services/eligibility_service.py`
- `hcm_app/schemas/eligibility.py`
- `tests/integration/test_eligibility_service.py`

---

#### **PR-HCM-010: /internal/check-eligibility Endpoint**

**Aceptación:**
- [ ] Endpoint: `GET /internal/check-eligibility/{collaborator_id}?company_id={id}`
- [ ] Respuesta (ApiResponse[EligibilityStatus]):
  ```json
  {
    "data": {
      "is_eligible": true,
      "last_violation_date": null,
      "penalty_expires_at": null,
      "active_violations": []
    }
  }
  ```
- [ ] Consumidores: Promotion Service (antes de permitir candidatura)
- [ ] Rate limit: 100/minute (internal API)
- [ ] Auth: Requires `hcm:read` scope
- [ ] Tests: 8+ tests (auth, filtering, responses)

**Estimado:** 1h  
**Archivos:**
- `hcm_app/api/v1/endpoints/eligibility.py`

---

#### **PR-HCM-011: Permission Endpoints (CRUD + State Transitions)**

**Aceptación:**
- [ ] Endpoints:
  - `POST /permissions` — crear solicitud
  - `GET /permissions/{id}` — obtener detalles
  - `GET /collaborators/{id}/permissions` — listar historial
  - `POST /permissions/{id}/approve-supervisor` — Firma 1
  - `POST /permissions/{id}/approve-rh` — Firma 2 → POSTED
  - `POST /permissions/{id}/reject` — rechazo
  - `PATCH /permissions/{id}` — editar solo si DRAFT
  - `DELETE /permissions/{id}` — eliminar solo si DRAFT
- [ ] Validaciones:
  - No se puede editar después de PENDING_SUPERVISOR
  - No se puede deshacer una firma
- [ ] Rate limit: 30/minute (mutations), 60/minute (reads)
- [ ] Tests: 25+ tests (CRUD, state, auth, boundaries)

**Estimado:** 3h  
**Archivos:**
- `hcm_app/api/v1/endpoints/permissions.py`

---

#### **PR-HCM-012: Kardex Query & Audit Endpoint**

**Aceptación:**
- [ ] Endpoint: `GET /collaborators/{id}/kardex?from_date={date}&to_date={date}`
- [ ] Retorna: lista de `KardexEvent` filtrada por rango de fechas
- [ ] Ordena: por `created_at DESC`
- [ ] Paginación: 50 items por página
- [ ] Acceso: Solo RH y el mismo colaborador pueden consultar su Kardex
- [ ] Tests: 12+ tests (auth, filtering, pagination)

**Estimado:** 1.5h  
**Archivos:**
- `hcm_app/api/v1/endpoints/kardex.py`

---

#### **PR-HCM-013: MES Integration (Headcount Recompute)**

**Aceptación:**
- [ ] Crear `MESClient` en `infrastructure/clients/mes_client.py`
- [ ] Método: `async def recompute_headcount(company_id, date_range)`
- [ ] Lógica:
  - Cuando `PermissionDocumentPosted` se publica en outbox
  - Notification Service → MES lo consume
  - MES recomputa disponibilidad de personal
  - Suma: Total asignados - (Permiso + Vacación + Suspensión activos en fecha)
- [ ] Resiliencia: best-effort, no bloquea la aprobación en HCM
- [ ] Tests: 8+ tests (HTTP calls, error handling)

**Estimado:** 2h  
**Archivos:**
- `hcm_app/infrastructure/clients/mes_client.py`
- `hcm_app/services/outbox_event_publisher.py`

---

### Phase 4: ⏳ Control Avanzado de Tiempo (T&A Advanced)

#### **PR-HCM-014: TimeRecord Model (RFID/Biometric)**

**Aceptación:**
- [ ] Modelo `TimeRecord` (entradas/salidas)
- [ ] Campos:
  - `collaborator_id, recorded_at (datetime), record_type` (CLOCK_IN / CLOCK_OUT)
  - `source` (RFID / BIOMETRIC / MANUAL)
  - `rfid_hash` (si aplica) — hash de tarjeta usando CORE_HCM_RFID_SALT
  - `location` (str, opcional) — lugar de registro
- [ ] Endpoints:
  - `POST /clock-in` (scanner RFID POST aquí)
  - `POST /clock-out` (scanner RFID POST aquí)
  - `GET /time-records/{collaborator_id}?from={date}&to={date}` (listado)
- [ ] Validaciones:
  - No puede haber dos CLOCK_IN consecutivos (validar último TimeRecord)
  - No puede haber CLOCK_OUT sin CLOCK_IN previo
- [ ] RFID Security: validar hash usando salt
- [ ] Tests: 15+ tests

**Estimado:** 3h  

---

#### **PR-HCM-015: WorkCalendar Model**

**Aceptación:**
- [ ] Modelo `WorkCalendar` (días especiales)
- [ ] Campos:
  - `company_id, date, type` (HOLIDAY / WORKDAY / PLANNED_SHUTDOWN)
  - `description (str)` (ej: "Navidad", "Paro General")
- [ ] Usado por: Cálculo de disponibilidad, nómina
- [ ] Endpoint CRUD: `GET /work-calendar`, `POST /work-calendar`, etc.
- [ ] Tests: 8+ tests

**Estimado:** 1.5h  

---

### Phase 5: ⏳ Seguridad y EHS

#### **PR-HCM-016: MedicalRecord Model (Zero Trust)**

**Aceptación:**
- [ ] Modelo `MedicalRecord` (expediente médico privado)
- [ ] Campos:
  - `collaborator_id, record_date, record_type` (CHECKUP / TREATMENT / RESTRICTION)
  - `description, doctor_name, next_review_date`
- [ ] Acceso:
  - Solo rol `MEDICAL_STAFF` puede leer/crear
  - Nunca expuesto en endpoints públicos
  - Logs de auditoría de cada acceso
- [ ] Tests: 10+ tests (access control, logging)

**Estimado:** 2h  

---

#### **PR-HCM-017: PPERecord Model**

**Aceptación:**
- [ ] Modelo `PPERecord` (Equipo de Protección Personal)
- [ ] Campos:
  - `collaborator_id, position_id, delivery_date, equipment_type` (HELMET / GLOVES / etc.)
  - `cost (Money VO)`, `center_code` (para ERP)
- [ ] Integración: publicar evento `PPEDelivered` → ERP genera costo en centro de costos
- [ ] Tests: 10+ tests

**Estimado:** 2h  

---

### Phase 6: ⏳ Analytics y Reporting

#### **PR-HCM-018: Kardex Reports**

**Aceptación:**
- [ ] Endpoint: `GET /reports/kardex?company_id={id}&from={date}&to={date}`
- [ ] Retorna: agregaciones por tipo de evento, violaciones por departamento, etc.
- [ ] Rendimiento: < 2 segundos para 1M registros
- [ ] Tests: 5+ tests

**Estimado:** 2h  

---

## 📊 Resumen de Esfuerzo

| Phase | Tareas | Estimado Total |
|-------|--------|-----------------|
| 1 (Base) | Completado | ✅ |
| 2 (Skills) | PR-HCM-001 a 004 | ~7.5h |
| 3 (Kardex) | PR-HCM-005 a 013 | ~22h |
| 4 (T&A Advanced) | PR-HCM-014, 015 | ~4.5h |
| 5 (Seguridad) | PR-HCM-016, 017 | ~4h |
| 6 (Reporting) | PR-HCM-018 | ~2h |
| **TOTAL PHASES 2-6** | | **~40h** |

**Recomendación de Sprint:** 2 PRs por semana (1 grande + 1 pequeña), ~20h/semana = 2 semanas para completar todas las fases.

---

## 🔗 Dependencias y Críticos

| Tarea | Bloqueada por | Bloquea |
|-------|---------------|---------|
| Phase 2 (Skills) | None | Phase 3 |
| Phase 3 (Kardex) | Phase 2 | Promotion Service |
| PR-HCM-010 | PR-HCM-009, PR-HCM-007 | Promotion Service (crítica) |
| PR-HCM-013 | PR-HCM-008, MES `/mes_app/infrastructure/clients` | Headcount accuracy |

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

**Próxima revisión:** Después de completar Phase 3 (Kardex)  
**Responsable de seguimiento:** Arquitecto HCM + Tech Lead
