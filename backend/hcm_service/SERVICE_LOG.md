# HCM Service (ex HR Service) — SERVICE LOG

> **Service:** HCM Service — Human Capital Management (Port 8004)
> **Status:** Operational / Industrial Identity Source of Truth
> **Compliance:** Multi-tenant Isolation Verified

---

### [2026-05-27] - Phase 145: Department Description + Seed Hardening + Mobile Departments ✅
- **Migration `003_add_department_description`**: Columna `description VARCHAR(250) NULL` añadida a `departments`. Alembic múltiples heads resuelto — usar `alembic upgrade heads` (plural) para respetar las dos ramas paralelas `001_add_audit_logs` y `001_add_id_pattern`.
- **Model `Department`** (`models/department.py`): Campo `description: Mapped[Optional[str]]` añadido. Espeja `Department.Description` del .NET legacy (max 250 chars).
- **Schemas `DepartmentRead/Create/Update`** (`schemas/department.py`): `description` añadido en los tres schemas.
- **Seed `scripts/seed.py`** — tres bugs de compatibilidad corregidos:
  1. `last_name=` → `last_name_paternal=` (incompatible con migration `002_split_last_name` Phase 138).
  2. `department="Warehouse"/"Logistics"` (string) → `department_id=uuid.uuid5(...)` FK correcto (incompatible con `department` como relationship desde Phase 118).
  3. `first_name="Luis (Enterprise)"` / `first_name="Luis (USA)"` → `first_name="Luis"` (nombre limpio en full_name).
- **18 departamentos seeded**: 6 por empresa (Producción/PROD, Calidad/QUAL, Mantenimiento/MANT, Almacén/ALM, Administración/ADMIN, Ingeniería/ENG) × 3 empresas (Enterprise, Logistics MX, Logistics US). UUIDs deterministas con `uuid.uuid5(NAMESPACE_DNS, f"interno.dept.{company_id}.{code}")`.
- **Nginx**: Ruta `/api/v1/hcm` añadida en `nginx.conf` → expone todos los endpoints HCM al gateway (incluyendo `/api/v1/hcm/departments/`).
- **Mobile Flutter**: `CreateTicketScreen._departmentDropdown()` — estado vacío mejorado con botón "Toca para reintentar" + `_loadDepartments()` resetea `_loadingDepts=true` antes de cada fetch.
- **Status**: ✅ COMPLETED — Departamentos visibles en app móvil.

---

### [2026-05-26] - Phase 138: Mexicanización del Expediente ✅
- **Migration `002_split_last_name`**: `last_name VARCHAR(100)` dividido en `last_name_paternal VARCHAR(50) NOT NULL` + `last_name_maternal VARCHAR(50) NULL`. Data copy: `SET last_name_paternal = last_name` antes del DROP COLUMN. Downgrade reconstituye `last_name` con CONCAT.
- **Model `Collaborator`**: `last_name` → `last_name_paternal` + `last_name_maternal`. `full_name` property actualizada para componer ambos apellidos (omite maternal si NULL).
- **Schemas `CollaboratorRead`, `CollaboratorCreate`, `CollaboratorUpdate`**: campos actualizados. RFC y CURP ya existían con regex validators desde Phase 50 — sin cambios requeridos.
- **Status**: ✅ COMPLETED — Code Graph 100% Compliance.

---

### [2026-05-21] - Phase 120: Audit Trail Completado en bulk_upload ✅
- **`api/v1/endpoints/collaborators.py` — `bulk_upload`**: Añadida llamada `AuditService.log_action(action="COLLABORATOR_BULK_UPLOAD")` con métricas `{created, updates, errors}` antes del `db.commit()`. Anteriormente la carga masiva de colaboradores no quedaba registrada en audit_logs. El evento se registra incluso si hay errores parciales (imported N, errors M).

### [2026-05-20] - Phase 118: Department Model + Ticket Routing Support ✅
- **Nuevo Modelo `Department`** (`models/department.py`): Entidad `Department(MultiTenantBase)` con `name`, `code`, `description`. Migración Alembic `a6054c79a22f_add_department_model.py`.
- **CRUD Endpoint** (`api/v1/endpoints/departments.py`): `GET/POST /departments`, `GET/PATCH/DELETE /departments/{id}`. Guard: `Security(require_scope(["hcm:read/write"]))`.
- **Router** (`api/v1/api.py`): Departamentos incluidos con prefix `/departments`.
- **Schemas** (`schemas/department.py`): `DepartmentCreate`, `DepartmentRead`.
- **Collaborator** (`models/collaborator.py` + `schemas/collaborator.py`): Actualizado para soportar `department_id` opcional en asignación de tickets.
- **Migración audit_logs** (`001_add_audit_logs.py`): Tabla `audit_logs` creada en `hcm_db` — resuelve `AuditService` fire-and-forget silencioso para eventos `GOD_MODE_ACTIVATED` y `ACCESS_DENIED_402`.
- **Migración id_pattern** (`001_add_id_pattern.py`): Columna `internal_id_pattern` añadida a `hr_tenant_configs` — resuelve deuda técnica MEDIA.
- **Seed industrial** (`scripts/seed_manufacturing_collaborators.py`): Seed de 15 colaboradores industriales de manufactura con roles PLC, Mantenimiento, Logística.
- **Status**: ✅ COMPLETED — Code Graph 0 errores.

### [2026-05-16] - Phase 108: Industrial Ecosystem Cold-Start & Seed Hardening
- **Baseline Consolidation**: Engineered `000_hcm_baseline.py`, a unified migration that replaces all fragmented histories. This baseline includes the `collaborators`, `hr_tenant_configs`, and the new `external_contacts` tables.
- **Triple Identity Seeding**: Successfully seeded industrial collaborators (Carlos Ramírez) and external providers (Alicia Torres) into the `hcm_db` from a cold-start state.
- **Audit Compliance**: Verified that all HCM models correctly inherit from `MultiTenantBase` and populate audit columns during the industrial seeding process.
- **Status**: ✅ Phase 108 COMPLETED — HCM Baseline Stabilized & Identity Seeding Certified.

---

### [2026-05-04] - Phase 86: Unified Identity & Security Audit Foundations
- **Unified Identity**: Se añadió el campo `user_id` al modelo `Collaborator` para vincular formalmente la identidad administrativa (`Users` en `auth_service`) con la identidad física en piso (`Collaborators` en `hcm_service`).
- **Audit Integration**: Este es el primer paso arquitectónico para poder rastrear con precisión de auditoría quién está autorizando operaciones en terminales industriales (PIN/RFID), permitiendo unificar perfiles en el UI (e.g. asignación de tickets).
- **Status**: ⏳ Phase 86 PAUSED - Model updated, pending logic propagation.

---

### [2026-04-30] - Phase 73: Estabilización de Autenticación Industrial
- **HCM Migration**: Migración definitiva de la gestión de colaboradores al microservicio independiente `hcm_service`.
- **RFID/PIN Restoration**: Restauración del flujo de login industrial mediante RFID (SHA-256) y PIN (Bcrypt).
- **Identidad Triple (Física)**: Consolidación de la Identidad Física como el SSOT para operaciones en piso de producción (MES).
- **Identidad Legal**: Aislamiento de datos mediante `company_id` para cumplimiento fiscal.
- **Variable de entorno**: `CORE_HR_RFID_SALT` → `CORE_HCM_RFID_SALT`.
- **Status**: ✅ COMPLETED - Industrial Identity Stabilized.

---

### [2026-04-30] - Phase 72: HR → HCM Rename & Domain Upgrade
- **Rename**: Directorio `hr_service` → `hcm_service`. Imagen Docker `interno-backend-hcm-service:latest`. DB `hr_db` → `hcm_db`.
- **Dominio elevado**: De "Recursos Humanos" a **Human Capital Management (HCM)** para reflejar la gestión de Competencias, T&A y EHS.
- **docker-compose.yml**: Servicio `hr-service` → `hcm-service`. URL interna del Auth actualizada a `http://hcm-service:8000`.

---

### [2026-04-16] - Phase 44: Media Assets & Storage Integration ✅
- **Status**: ✅ COMPLETED — **Multi-tenant Asset Management**
- **Model Expansion** (`models/collaborator.py`):
  - Added `photo_path` (String(255)) to persist S3 Object Keys.
- **Domain Identity** (`domain/entities/collaborator_entities.py`): Updated `Collaborator` dataclass to include `photo_path`.
- **Collaborator Service** (`services/collaborator_service.py`):
  - Integrated `StorageProvider` for Fail-Safe photo uploads.
  - Implementated hierarchical naming: `{company_id}/hr/collaborators/{collaborator_id}.jpg`.
- **API Endpoint** (`api/v1/endpoints/collaborators.py`):
  - Updated `POST /` to support `multipart/form-data` with optional `photo` upload.
  - Dynamic `profile_url` injection in response using Pre-signed URLs.
- **Infrastructure**: Integrated central `common.infrastructure.storage` provider.
- **Cleanup**: Repositories updated to map `photo_path` between ORM and Domain layers.

---

### [2026-04-15] - Phase 50: Cross-Border Eligibility & Compliance ✅
- **Status**: ✅ COMPLETED — **Binational Logistics Compliance Layer**
- **Model Expansion** (`models/collaborator.py`): Added 15 new fields across 4 categories:
  - *Fiscal Identity*: `rfc` (regex validated), `curp` (regex validated), `nss`
  - *Cross-Border Credentials*: `visa_number`, `visa_expiry` (Date), `sentry_id`, `driver_license_number`, `driver_license_expiry` (Date)
  - *HazMat & Medical Compliance (SCT/DOT)*: `hazardous_material_certified` (Boolean), `medical_certificate_expiry` (Date), `last_drug_test_date` (Date)
  - *Industrial Safety*: `blood_type`, `emergency_contact` (JSONB: standardized `{name, relationship, phone, alt_phone}`)
  - *ERP Bridge*: `m3_operator_id`, `job_title`
- **Pydantic Schemas** (`schemas/collaborator.py`):
  - RFC regex from legacy .NET (`Interno.Domain/InternoExtensions.cs`) ported to `Field(pattern=...)`
  - CURP full 18-char pattern with state code validation
  - `EligibilityResponse` with `details` breakdown (document, expiry_date, days_remaining)
  - `EmergencyContact` typed sub-model for JSONB contract
  - `CollaboratorSensitiveRead` schema for HR-manager-level access
- **Endpoints** (`api/v1/endpoints/collaborators.py`):
  - `GET /collaborators/validate-scan/{badge_id}?type=CROSS_BORDER` — Handheld barcode scan, strict tenant scope
  - `GET /collaborators/{id}/eligibility?type=CROSS_BORDER` — Full eligibility check with first-failure short-circuit
  - Priority order: License > Medical > Visa
- **Config** (`core/config.py`): `CROSS_BORDER_EXPIRY_THRESHOLD_DAYS = 15` (configurable via env `CORE_HR_EXPIRY_THRESHOLD_DAYS`)
- **Migration** (`alembic/versions/b2c3d4e5f6a7_collaborator_phase50_identity.py`): Full `ALTER TABLE` migration, reversible via `downgrade()`

### [2026-04-14] - Phase 45: Industrial Identity & Discovery-First Auth ✅
- **Status**: ✅ COMPLETED — **Global Identity Authority**
- **Alphanumeric Migration**: Successfully migrated `internal_id` from `Integer` to `String(50)` across the entire stack (Postgres, SQLAlchemy, Pydantic). Supports industrial formats like `003709A`.
- **Cross-Tenant Identity Discovery**: Implemented a fallback mechanism in `CollaboratorVerifyService` that utilizes shared physical credentials (RFID/Barcode) to link identities across different company tenants. This enables "identity jumping" without duplicate physical enrollment.
- **Enhanced Verification API**: Updated the verification schema to support lookup by `collaborator_id` (UUID), providing a more deterministic path for the Auth Service during company selection handshakes.
- **Deterministic Industrial Identity**: Standardized `seed.py` with deterministic UUIDs for all demo collaborators, ensuring stable cross-service tracking (SSOT) across HR, Auth, and Inventory.
- **Tenant Validation Engine**: Implemented `HrTenantConfig` and a dynamic Regex validation hook in `CollaboratorService`. Each tenant can now enforce its own payroll ID format.
- **Physical Identity Hashing**: Established SHA-256 hashing for RFID tags with per-environment `CORE_HR_RFID_SALT`, ensuring physical credentials cannot be reverse-engineered from the database.
- **Unified Configuration**: Adopted the `CORE_` environmental prefix standard for AWS compatibility, including `CORE_HR_RFID_SALT` and `CORE_INTERNAL_API_KEY`.
- **Bulk Upload Resiliency**: Integrated pattern validation into the bulk collaborator creation flow, preventing invalid IDs from entering the system.

---

### [2026-04-10] - Phase 44: Organization Hierarchy & RBAC Control ✅
- **Status**: ✅ COMPLETED
- **Supervisor Hierarchy**: Fully enabled the `supervisor_id` self-referential relationship. Supports recursive organizational tree queries for reporting lines.
- **Role-Based Provisioning**: Implemented automatic creation of default roles for new collaborators based on their primary warehouse assignment.
- **Service-to-Service Security**: Hardened the internal verification endpoint with `X-Internal-API-Key` validation to prevent unauthorized identity lookups from outside the cluster.

---

### [2026-04-05] - Phase 40: Multi-Tenant Audit Hardening ✅
- **Status**: ✅ COMPLETED
- **Audit Ledger Inheritance**: Migrated all HR models (`Collaborator`, `Shift`, `HrTenantConfig`) to inherit from `MultiTenantBase`.
- **Traceability**: All collaborator creations now record `created_by` and `updated_by` automatically via SQLAlchemy listeners, even for internal system-triggered events.

---

### [2026-03-30] - Phase 39: Auth Proxy & Kiosk Integration ✅
- **Status**: ✅ COMPLETED
- **Collaborator Login Handshake**: Successfully integrated with `auth_service`. The login flow now supports a secure proxy where Auth issues the JWT after HR verifies the physical credentials (RFID/PIN).
- **O(1) Physical Scans**: Database indexing optimized for SHA-256 RFID hashes, ensuring sub-10ms response times for high-volume entry/exit points in Kiosk mode.

---

### [2026-03-26] - Phase 38: HR Microservice Bootstrap ✅
- **Status**: ✅ COMPLETED
- **Service Extraction**: Decoupled HR logic from the monolithic Auth Service into its own dedicated microservice (`hr_service`) with its own database (`hr_db`).
- **Domain Modeling**: Created the core `Collaborator` entity with support for legacy payroll IDs, shift management, and warehouse linking.
- **Infrastructure**: Added `hr_service` and `hr_db` to the `docker-compose.yml` ecosystem with healthchecks and automated migrations.

---

### [2026-03-25] - Phase 37: HR Microservice Inception 🌟
- **Status**: 🏁 ARCHITECTURAL SPECIFICATION
- **Decision to Extract**: Decided to follow SRP (Single Responsibility Principle) by separating Physical Identity from Administrative Auth.
- **Physical Identity Design**: Defined the multi-tenant architecture for RFID tags (SHA-256 + Salt) and PIN codes (Bcrypt).
- **Warehouse Lock Pattern**: Conceptualized the zero-trust barrier that binds a collaborator to their physical location during inventory operations.
