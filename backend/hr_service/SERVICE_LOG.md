# InternoCore HR Service - SERVICE LOG

> **Service:** HR Service (Port 8009)
> **Status:** Operational / Industrial Identity Source of Truth
> **Compliance:** Multi-tenant Isolation Verified

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
