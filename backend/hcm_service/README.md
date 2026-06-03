# 👥 HCM Service — Human Capital Management (Puerto 8004)

El **HCM Service** es el **motor de validación de capacidades humanas y custodio del expediente transaccional operativo** del ecosistema Interno Core. No es un simple archivo de empleados: es el servicio que determina quién puede operar qué máquina, en qué turno y con qué certificación vigente. Actúa como el **"Gatekeeper" del factor humano** para el MES, CMMS, ERP y controla el **Kardex del Colaborador** — un registro histórico inmutable de la vida laboral que impacta directamente en elegibilidad, plan de carrera y disponibilidad de personal en piso.

> **Rename Log:** Este servicio fue previamente conocido como `hr_service`. Renombrado a `hcm_service` (2026-04-30) para reflejar su rol como **Human Capital Management** bajo la arquitectura industrial de Interno Core.

> **Fase 161+:** Introducción del **Kardex Transaccional** (histórico operativo inmutable) y el patrón **Header-Detail** con flujos de aprobación jerárquica supervisor→RH.

---

## 🏛️ El Kardex del Colaborador — Expediente Transaccional Inmutable

El **Kardex** deja de ser un repositorio estático para convertirse en el **expediente de la vida laboral completa** del colaborador dentro de cada empresa (`company_id`). Es un registro histórico inmutable que captura todos los eventos que impactan disponibilidad, elegibilidad de carrera y cumplimiento operativo.

### Categorías de Eventos en el Kardex

```
┌─────────────────────────────────────────────────────────────┐
│             KARDEX DEL COLABORADOR                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📋 DISCIPLINARIOS                                          │
│     • Amonestaciones (acta administrativa)                  │
│     • Suspensiones (temporal o indefinida)                  │
│     → Impacta: Elegibilidad promoción (90d penalización)   │
│                                                              │
│  🕐 ASISTENCIA                                              │
│     • Permisos (con/sin goce de sueldo)                    │
│     • Faltas justificadas (médico, personal)               │
│     • Faltas injustificadas                                │
│     → Impacta: Acumulado de disponibilidad, nómina         │
│                                                              │
│  📊 MOVIMIENTOS                                             │
│     • Vacaciones gozadas (DFS, DUF)                         │
│     • Cambios de estatus (Activo→Inactivo, Incapacidad)   │
│     • Retiros y cambios de empresa                         │
│     → Impacta: Headcount real en MES, ERP                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Reglas de Negocio Críticas: Elegibilidad y Plan de Carrera

#### 🚫 Filtro de Postulación Interna (Kardex Limpio)
Para que un colaborador sea **elegible para aplicar a una vacante interna** (promoción), el sistema exige:

```
✅ REQUISITO MANDATORIO:
   • "Kardex Limpio" durante los **últimos 90 días naturales**
   • = Sin registros de Amonestación, Suspensión, o Falta Injustificada
   • = Sin penalizaciones activas desde infracciones previas

❌ SI HAY VIOLACIÓN:
   • Campo `affects_eligibility = True` en el evento
   • Se calcula `eligibility_penalty_until = NOW() + 90 días`
   • Backend bloquea automáticamente cualquier intento de promoción
   • Error: "Kardex tiene afectaciones vigentes hasta {date}"
```

#### 📅 Headcount Real para Planeación (MES Integration)
El Kardex impacta directamente el cálculo de disponibilidad de personal:

```
Headcount Disponible por Línea/Turno = 
  Total Asignados
  - Permiso/Incapacidad/Vacaciones (activas en la fecha)
  - Suspensión (si está vigente)
```

---

## 🔄 Flujo de Aprobaciones Jerárquicas (Documento-Movimiento)

El control de asistencia y disponibilidad de personal sigue un patrón de **cadena de responsabilidades**:

```
[ORIGEN: Solicitud del Colaborador]
              │
              ▼
    ┌─────────────────────┐
    │ FIRMA 1: SUPERVISOR │ (Supervisor de Línea/Producción)
    ├─────────────────────┤
    │ • Valida impacto    │
    │   en Headcount      │
    │ • Revisa con MES    │
    │   capacidad línea   │
    │ • Estado: PENDING   │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │ FIRMA 2: RH         │ (Recursos Humanos)
    ├─────────────────────┤
    │ • Valida contra     │
    │   políticas empresa │
    │ • Verifica saldos   │
    │   (vacaciones, etc) │
    │ • Aplica documento  │
    │ • Estado: POSTED    │
    │ • Escribe en Kardex │
    │ • Impacta nómina    │
    └──────────┬──────────┘
               │
               ▼
    [REGISTRO ATÓMICO EN KARDEX]
    [EVENT: CollaboratorKardexEvent]
```

### Header-Detail (Documento-Movimiento)

Cada solicitud sigue el patrón estándar de Interno Core:

```python
# HEADER: Documento
class PermissionDocument(MultiTenantBase):
    company_id: UUID           # Tenant isolation
    collaborator_id: UUID      # Quién solicita
    document_type: str         # PERMISSION / VACATION / SUSPENSION
    status: str                # DRAFT → PENDING_SUPERVISOR → PENDING_RH → POSTED
    
    supervisor_id: UUID        # Firma 1
    supervisor_signed_at: datetime
    
    hr_approver_id: UUID       # Firma 2
    hr_posted_at: datetime     # Timestamp de aplicación a Kardex
    
    notes: str                 # Justificación del cambio

# DETAIL: Movimientos (líneas del documento)
class PermissionMovement(MultiTenantBase):
    document_id: UUID
    start_date: date
    end_date: date
    movement_type: str         # IN_PERMISSION / OUT_PERMISSION / VACATION_DAY
    quantity_days: int         # Duración
    
    # Impacto financiero
    salary_impact: Money       # Monto deducido/acreditado
    is_salaried: bool          # Con/sin goce de sueldo
```

---

## 🏗️ Arquitectura del Dominio

El HCM se divide en 4 dominios funcionales, implementados en fases:

### Fase 1 — Identidad y Estructura Organizacional
Gestión de la entidad **Collaborator** (sustituyendo el término "Operador") con soporte pleno de Multitenancy. Cada colaborador existe dentro de un `company_id` y puede pertenecer a múltiples empresas a través del Auth Service.

- **Collaborator**: Entidad central. Hereda `MultiTenantBase` + `AuditBase`. Referencia `user_id` del Auth Service.
  - Campos clave: `assigned_plant`, `shift`, `global_entry_id`, `supervisor_id`, `manager_id`, `director_id`
  - Métodos críticos: `is_eligible_for_promotion()`, `calculate_headcount_impact(date_range)`
- **Department**: Área organizacional por empresa. CRUD operacional ✅ (Phase 158).
- **Position**: Puesto de trabajo. Define los `Skills` requeridos para desempeñar el rol.
- **ContractType**: Tipos de contrato (Indefinido, Temporal, Subcontratado).

### Fase 2 — Motor de Competencias (Skills Engine)
El HCM se convierte en el **"Gatekeeper"** de la operación industrial. El MES y el CMMS consultan este servicio antes de permitir que un colaborador inicie una tarea de alto riesgo o una Orden de Producción.

- **Skill**: Catálogo de habilidades (Operación Torno CNC, Soldadura MIG, etc.) con nivel `TRAINEE → EXPERT`.
- **CollaboratorSkill**: Nivel actual del colaborador en cada skill.
- **Certification**: Certificaciones formales con `issued_at` / `expires_at` y alertas de vencimiento.
- **TrainingRecord (Kardex)**: Historial de cursos y horas acumuladas ("Horas de Vuelo").

**API Interna crítica (SLA < 100ms):**
```
GET /internal/validate-access/{collaborator_id}/{skill_required}
→ { is_valid: bool, reason: str, expires_at: datetime | null }

GET /internal/check-eligibility/{collaborator_id}
→ { is_eligible: bool, penalty_until: datetime | null, 
    violations: [amonestación, suspensión, falta] }
```

### Fase 3 — Control de Tiempo y Disponibilidad (T&A)
El HCM alimenta al ERP y a la planeación de producción con datos de disponibilidad en tiempo real.

- **Shift**: Definición de turnos (matutino, vespertino, nocturno, rotativo).
  - Cálculo: `hours = TotalTimeWorkday - TotalTimeBreaks` (ej: 8h turno - 1h break = 7h disponibles)
  - Relación con **BreakGroup** (Phase 157): Grupos de descansos por turno, capacidad por slot
- **ShiftAssignment**: Asignación colaborador-turno por período.
- **TimeRecord**: Entradas/Salidas desde scanner RFID o biométrico WebAuthn.
- **WorkCalendar**: Días hábiles, festivos y paros programados por planta.
- **PermissionDocument** / **PermissionMovement**: Documentos de solicitud y movimientos de asistencia (Phase 161+).

**API de planeación para el MES:**
```
GET /internal/man-hours?line_id={id}&date={YYYY-MM-DD}
→ { available_hours: float, collaborators: int, by_shift: [...],
    headcount_impact: [...] }

POST /internal/check-collaborator-eligibility/{collaborator_id}
→ { is_eligible: bool, penalty_expiry: datetime | null,
    active_violations: [...] }
```

**Integración con Industrial Scanner:**
- Endpoint `POST /clock-in` y `POST /clock-out` para lectores RFID.
- Salt de seguridad: `CORE_HCM_RFID_SALT` para hashing de IDs de tarjeta.

### Fase 4 — Seguridad, EHS y Domain Events
Implementación de **Zero Trust** para datos médicos y arquitectura **Event-Driven** para limpieza automática de procesos operativos.

- **MedicalRecord**: Expediente médico bajo protocolo Zero Trust. Solo accesible con rol `MEDICAL_STAFF`.
- **PPERecord**: Registro de entrega de Equipo de Protección Personal por puesto. El costo se carga al centro de costos en el ERP.

**Domain Events:**

| Evento | Suscriptores |
|--------|-------------|
| `CollaboratorStatusChanged(INACTIVE)` | MES desasigna estación; CMMS reasigna OT pendientes |
| `CertificationExpired` | Notification Service → alerta a supervisor y colaborador |
| `NewCollaboratorOnboarded` | Auth Service → crea `UserCompanyRole` |
| `PPEDelivered` | ERP → genera línea de costo en el centro de costos del puesto |
| `PermissionDocumentPosted` | MES recomputa headcount; Nómina procesa deducción |
| `CollaboratorKardexViolation` | Promotion Service → bloquea elegibilidad por 90d |

---

## 🔗 Integraciones con el Ecosistema

| Servicio | Dirección | Propósito | Criticidad |
|----------|-----------|----------|-----------|
| **Auth Service** | HCM ← Auth | Obtiene `user_id` para vincular al Collaborator | CRÍTICA |
| **MES** | MES ↔ HCM | Valida `SkillLevel` + Calcula `headcount_impact` + Escribe BreakGroups | CRÍTICA |
| **CMMS** | CMMS → HCM | Valida `AccessPermit` antes de asignar una Orden de Mantenimiento | ALTA |
| **ERP** | HCM → ERP | Envía costos de mano de obra (`Money VO`) y cargos de EPP | ALTA |
| **Notification Service** | HCM → Notif. | Dispara alertas: vencimiento de certificaciones, elegibilidad bloqueada | MEDIA |
| **Promotion / Reclutamiento Interno** | Promotion ← HCM | Consulta `is_eligible_for_promotion()` antes de permitir candidatura | CRÍTICA |
| **Master Data Service** | HCM ← Master | Obtiene catálogos configuracionales (empresas, centros de costo) | ALTA |

**Contrato de Integración:**
- HCM expone un endpoint **`/internal/check-eligibility/{collaborator_id}`** para validación de promoción
- HCM expone un evento `PermissionDocumentPosted` al outbox para que MES recompute headcount
- HCM consume `BreakGroup` configurados por MES y valida capacidad de descansos

---

## ⚙️ Variables de Entorno Requeridas

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:password@interno-db-dev:5432/hcm_db
CORE_SECRET_KEY=ROTATED_SECRET_KEY_987654321_DEV
CORE_ALGORITHM=HS256
CORE_ADMIN_MASTER_KEY=ROTATED_MASTER_KEY_GOD_MODE

# RFID / Biometría
CORE_HCM_RFID_SALT=ROTATED_HR_RFID_SALT_7890  # Salt para hashing de tarjetas RFID

# Rate Limiting & Redis
CORE_REDIS_URL=redis://interno-redis-dev:6379/0
CORE_INTERNAL_API_KEY=ROTATED_INTERNAL_API_KEY_4567

# Cross-service
CORE_MES_SERVICE_URL=http://interno-mes-dev:8005
CORE_MASTER_DATA_SERVICE_URL=http://interno-master-data-dev:8003

# Python
PYTHONPATH=/app
CORE_ENV_MODE=development
```

---

## 🗄️ Base de Datos — Modelo de Datos

- **DB Name:** `hcm_db` (aislada de `dbname` y demás servicios)
- **ORM:** SQLAlchemy Async
- **Migrations:** Alembic (version_table="alembic_version_hcm")

### Tablas Principales (Phase 161+)

```
┌────────────────────────┐
│    hcm_collaborators   │ ← Entidad principal (MultiTenantBase)
├────────────────────────┤
│ id (UUID)              │
│ company_id (UUID)      │ ← MURO DE HIERRO: multitenancy obligatoria
│ user_id (UUID)         │ → Auth Service
│ first_name, last_name  │
│ assigned_plant         │
│ shift_id (FK)          │
│ supervisor_id (FK)     │
│ manager_id (FK)        │
│ director_id (FK)       │
│ is_active              │
│ created_at, updated_at │
└────────────────────────┘

┌────────────────────────────────┐
│ hcm_permission_documents       │ ← HEADER (Documento)
├────────────────────────────────┤
│ id (UUID)                      │
│ company_id (UUID)              │
│ collaborator_id (FK)           │
│ document_type                  │ PERMISSION / VACATION / SUSPENSION
│ status                         │ DRAFT → PENDING_SUPERVISOR → POSTED
│ supervisor_id (FK)             │
│ supervisor_signed_at           │
│ hr_approver_id (FK)            │
│ hr_posted_at                   │
│ created_at, updated_at         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_permission_movements       │ ← DETAIL (Movimientos/líneas)
├────────────────────────────────┤
│ id (UUID)                      │
│ document_id (FK)               │
│ start_date, end_date           │
│ movement_type                  │ PERMISSION_DAY / VACATION_DAY / SUSPENSION
│ quantity_days (int)            │
│ salary_impact (Numeric 18,4)   │
│ is_salaried (bool)             │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_kardex_events              │ ← Registro inmutable (append-only)
├────────────────────────────────┤
│ id (UUID)                      │
│ company_id (UUID)              │
│ collaborator_id (FK)           │
│ event_type                     │ AMONESTACION / SUSPENSION / PERMISSION / VACATION
│ document_reference (FK)        │ → permission_documents.id si aplica
│ affects_eligibility (bool)     │ Si True: bloquea promoción
│ eligibility_penalty_until      │ Fecha de expiración de penalización
│ description                    │
│ created_at (immutable)         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_shifts                     │ ← Catálogo de turnos
├────────────────────────────────┤
│ id (UUID)                      │
│ company_id (UUID)              │
│ code (str)                     │ "MAT", "VES", "NOT"
│ name (str)                     │ "Matutino", "Vespertino", etc.
│ start_time, end_time (TimeSpan)│
│ total_hours_available          │ Horas = end - start - descansos
│ break_group_id (FK)            │ → MES break_groups
│ created_at, updated_at         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_departments                │ ← Áreas / Sectores
├────────────────────────────────┤
│ id (UUID)                      │
│ company_id (UUID)              │
│ name (str)                     │ "Línea 1", "Embalaje", etc.
│ description                    │
│ created_at, updated_at         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_break_groups               │ ← BreakGroups (Phase 157)
├────────────────────────────────┤
│ id (UUID)                      │
│ company_id (UUID)              │
│ name (str)                     │
│ capacity_per_slot (int)        │
│ created_at, updated_at         │
└────────────────────────────────┘

┌────────────────────────────────┐
│ hcm_break_slots                │ ← Slots de descanso disponibles
├────────────────────────────────┤
│ id (UUID)                      │
│ break_group_id (FK)            │
│ time_slot (TimeSpan)           │
│ capacity (int)                 │
│ created_at, updated_at         │
└────────────────────────────────┘
```

---

## 📋 Plan de Migración del Legacy (.NET Interno.HumanResource)

Basado en el análisis del código legacy en `archive/legacy-dotnet/src/Interno.HumanResource`, se mapea la arquitectura C# → Python con los siguientes pasos:

### Mapeo de Entidades Legacy → Python (HCM Service)

| Legacy C# | Python HCM | Estado | Notas |
|-----------|----------|--------|-------|
| `Employee` | `Collaborator` | ✅ Existe | Extendido con `assigned_plant`, `global_entry_id` |
| `Department` | `Department` | ✅ CRUD Phase 158 | Relación 1:N con Collaborator |
| `JobPosition` | `Position` | ⏳ Fase 2 | Requiere modelo de Skills |
| `Shift` | `Shift` | ✅ Modelo base | Extendido con `BreakGroup` (Phase 157) |
| `BreaksGroup` | `BreakGroup` | ✅ Phase 157 | Nuevo modelo separado de Shift |
| `Break` | `ShiftBreak` | ⏳ Fase 3 | Deuda: implementación MES |
| `Contract` | `ContractType` | ⏳ Fase 2 | Catálogo de tipos de contrato |
| `Competence` | `Skill` | ⏳ Fase 2 | Motor de competencias |
| `Supervisor/Manager/Director` | Foreign keys + treemap | ✅ Phase 158 | Jerarquía 3 niveles implementada |
| **N/A** | `PermissionDocument` | ✅ Phase 161 | **NUEVO**: Flujo de permisos con firma |
| **N/A** | `PermissionMovement` | ✅ Phase 161 | **NUEVO**: Movimientos de asistencia |
| **N/A** | `KardexEvent` | ✅ Phase 161 | **NUEVO**: Registro histórico inmutable |

### Implementación Progresiva (Phases)

#### ✅ Phase 1 (COMPLETADO) — Base Estructural
- [x] `Collaborator` model con MultiTenantBase
- [x] `Department` model con CRUD (Phase 158)
- [x] `Shift` model
- [x] Relaciones jerárquicas (supervisor_id, manager_id, director_id)
- [x] Auth integration (`user_id` link)

#### ⏳ Phase 2 (PRÓXIMA) — Motor de Competencias y Posiciones
- [ ] `Position` model (mapeo de `JobPosition` legacy)
  - Relación con catálogo de habilidades
  - SalaryRange (from/to)
  - Responsabilidades (lista de strings)
  - Requisitos (educación, idiomas, competencias)
  - Endpoint CRUD: `GET /positions`, `POST /positions`, `PATCH /positions/{id}`, `DELETE /positions/{id}`

- [ ] `Skill` model
  - Catálogo centralizado (SSOT por `company_id`)
  - Nivel: TRAINEE, JUNIOR, INTERMEDIATE, EXPERT
  - Endpoint: `GET /internal/skills/{skill_name}/validate`

- [ ] `CollaboratorSkill` model
  - Asignación de nivel a colaborador
  - CRUD: `POST /collaborators/{id}/skills`, `PATCH /collaborators/{id}/skills/{skill_id}`

- [ ] `Certification` model
  - `issued_at`, `expires_at`
  - Alert threshold (30 días antes de vencer)
  - Domain event: `CertificationExpiring` → Notification Service

#### 🔄 Phase 3 (EN PROGRESO) — Kardex Transaccional (Phase 161+)
- [ ] `PermissionDocument` model (HEADER)
  - Estados: DRAFT → PENDING_SUPERVISOR → PENDING_RH → POSTED
  - Endpoints:
    - `POST /permissions` (crear solicitud)
    - `POST /permissions/{id}/approve-supervisor` (Firma 1)
    - `POST /permissions/{id}/approve-rh` (Firma 2 → escribe en Kardex)

- [ ] `PermissionMovement` model (DETAIL)
  - Cálculo de impacto salarial
  - Integración con nómina

- [ ] `KardexEvent` model (append-only)
  - Registro inmutable de todo evento que afecta elegibilidad
  - `affects_eligibility` flag y `eligibility_penalty_until`
  - Endpoint: `GET /collaborators/{id}/kardex` (auditoría)

- [ ] Endpoint crítico: `GET /internal/check-eligibility/{collaborator_id}`
  - Valida Kardex limpio (90 días)
  - Retorna estado de penalizaciones
  - Usado por Promotion Service

- [ ] Integración MES
  - Outbox pattern: cuando se publica PermissionDocumentPosted
  - MES consume y recomputa headcount

#### ⏳ Phase 4 — Control Avanzado de Tiempo (T&A Advanced)
- [ ] `TimeRecord` model (RFID/Biometric)
  - `POST /clock-in`, `POST /clock-out`
  - Validación de salt RFID

- [ ] `WorkCalendar` model
  - Días hábiles, festivos, paros programados
  - Cálculo de disponibilidad

- [ ] Integración con `BreakGroup` (Phase 157)
  - Validación de capacidad de slots
  - Reserva de descansos por colaborador

#### ⏳ Phase 5 — Seguridad y EHS
- [ ] `MedicalRecord` model
  - Zero Trust: rol MEDICAL_STAFF requerido
  - Endpoint: `/medical-records` (protegido)

- [ ] `PPERecord` model
  - Registro de entrega de EPP
  - Integración ERP: genera costo en centro de costos

#### ⏳ Phase 6 — Analytics y Reporting
- [ ] Reportes de Kardex por empresa
- [ ] Análisis de elegibilidad por departamento
- [ ] Predicción de disponibilidad de personal (MES planning)

---

## 🏭 Ecosistema Interno Core

| Módulo | Dominio | Integración HCM |
|--------|---------|-----------------|
| CRM | Clientes | N/A |
| ERP | Finanzas y Compras | ← Recibe costos de mano de obra, EPP |
| MES | Ejecución en Piso | ↔ Valida skills, calcula headcount, BreakGroups |
| WMS | Inventario y Almacén | N/A |
| QMS | Calidad | ← Datos de certificaciones de calidad |
| CMMS | Mantenimiento | → Valida permisos de acceso |
| **HCM** ← *Este servicio* | **El Factor Humano y sus Competencias** | **CRÍTICO** |
| **Promotion / Reclutamiento Interno** | Gestión de carrera | ← Valida elegibilidad (Kardex limpio) |
