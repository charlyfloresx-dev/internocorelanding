# Implementation Plan: Dynamic Multitenant Timezone Support

This plan details the implementation of a dynamic timezone system for InternoCore. It allows each tenant (Company) to configure its own timezone (e.g., `America/Monterrey` or `America/Chicago`), includes this metadata within JWT claims on session generation, and formats all dates on the frontend dynamically using a dedicated Angular Pipe (`localDate`).

## 1. Database and Replication Synchronization

> [!IMPORTANT]
> The `Company` model is mirrored/shared across several databases. We must verify and execute Alembic migrations in both **`auth_service`** (`auth_db`) and **`master_data_service`** (`master_data_db`), as both define schemas relating to company configurations.
> Both microservices will have parallel migration scripts applied.

- **Seeded Companies & default timezones**:
  - `Interno Enterprise`: `America/Monterrey` (MX)
  - `Planta MX`: `America/Monterrey` (MX)
  - `Planta US`: `America/Chicago` (US)
  - `Demo Operativo S.A.`: `America/Monterrey` (MX)
  - Default fallback: `UTC`

---

## 2. Proposed Changes

### 🏢 Common Model Updates

#### [MODIFY] [company.py](file:///c:/API/interno/backend/common/models/company.py)
- Add a new column `timezone` to the unified `Company` class:
  ```python
  timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
  ```

---

### 🔑 Backend Auth & JWT

#### [MODIFY] [security.py](file:///c:/API/interno/backend/auth_service/auth_app/core/security.py)
- Update `create_final_access_token` to accept `timezone: Optional[str] = "UTC"` and embed it in the payload:
  ```python
  payload = {
      ...
      "timezone": timezone,
  }
  ```
- Update `create_access_token` shim to read `timezone` from the `data` dictionary.

#### [MODIFY] [select_company_command.py](file:///c:/API/interno/backend/auth_service/auth_app/commands/select_company_command.py)
- Retrieve the `Company` object inside `handle` and load its `timezone` value.
- Add `"timezone": company_obj.timezone` into the JWT claim construction data dictionary.
- Return `"timezone": company_obj.timezone` in the endpoint payload.

#### [MODIFY] [auth.py](file:///c:/API/interno/backend/auth_service/auth_app/api/v1/endpoints/auth.py)
- Update the `AccessTokenResponse` schemas in `auth_service/auth_app/schemas/auth.py` to include `timezone: str = "UTC"`.
- Populate `timezone` in `/refresh` and `/me` endpoint responses to ensure Zero Trust validations maintain timezone integrity.

#### [MODIFY] [unified_industrial_seed.py](file:///c:/API/interno/backend/auth_service/scripts/unified_industrial_seed.py)
- Incorporate appropriate `timezone` attributes into seeded companies.

---

### 🎨 Frontend State & Angular Setup

#### [MODIFY] [domain.types.ts](file:///c:/API/interno/frontend/src/app/core/models/domain.types.ts)
- Add `timezone?: string;` property to `AuthSession` interface.

#### [MODIFY] [auth.service.ts](file:///c:/API/interno/frontend/src/app/core/services/auth.service.ts)
- Expose a computed signal:
  ```typescript
  public companyTimezone = computed(() => this.session()?.timezone ?? 'UTC');
  ```
- In `setSession()`, include `timezone: data.timezone` inside the local storage item `_ic_auth_ctx`.
- In `selectCompany()`, extract and store the returned `timezone` claim.

---

### 🕒 Angular Date Pipes

#### [NEW] [local-date.pipe.ts](file:///c:/API/interno/frontend/src/app/shared/pipes/local-date.pipe.ts)
- Create a standalone Angular pipe `localDate` that extends standard date formatting but fetches the current tenant's active timezone dynamically:
  ```typescript
  import { Pipe, PipeTransform, inject } from '@angular/core';
  import { DatePipe } from '@angular/common';
  import { AuthService } from '../../core/services/auth.service';

  @Pipe({
    name: 'localDate',
    standalone: true
  })
  export class LocalDatePipe implements PipeTransform {
    private auth = inject(AuthService);
    private datePipe = new DatePipe('en-US');

    transform(value: any, format: string = 'medium', timezone?: string): any {
      if (!value) return value;
      const activeTz = timezone || this.auth.companyTimezone();
      return this.datePipe.transform(value, format, activeTz);
    }
  }
  ```

#### [MODIFY] Key Views Integration
We will incrementally swap standard `| date` with `| localDate` across components like:
- [tickets-form.component.ts](file:///c:/API/interno/frontend/src/app/modules/monitor/tickets/components/tickets-form.component.ts)
- [tickets-dashboard.component.ts](file:///c:/API/interno/frontend/src/app/modules/monitor/tickets/tickets-dashboard.component.ts)
- [inventory-documents.component.ts](file:///c:/API/interno/frontend/src/app/modules/inventory/inventory-documents.component.ts)

---

## 3. Verification Plan

### Automated Tests
- Execute database migrations to confirm the column `timezone` was successfully applied in `auth_service` and `master_data_service`.
- Re-run `unified_industrial_seed.py` and verify all seeds work correctly.
- Perform a handshake login simulation to ensure dynamic claims are populated.

### Manual Verification
- Log in to `Planta MX` and confirm dates render under Central Time (`America/Monterrey`).
- Switch company to `Planta US` and verify the same dates dynamically render under `America/Chicago`.
