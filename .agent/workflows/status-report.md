---
description: Generate end-of-day project status report for InternoCore (backend + frontend)
---

// turbo-all

## When to Run
Run this workflow whenever the user asks for:
- "estatus del proyecto"
- "estado del sistema"
- "dame el reporte de hoy"
- "status report"
- Any request to generate/update the project status at end of day.

---

## Steps

### Step 1 — Explore current state of backend and frontend

Explore the following directories to understand what has changed since the last report:
- `C:\API\interno\backend\` — list all microservice folders and check `SERVICE_LOG.md` files
- `C:\API\interno\frontend\src\app\modules\` — list all modules and check `ENGINEERING_LOG.md`

Cross-reference with:
- `C:\API\interno\docs\historial\tasks\consolidated_tasksYYYYMMDD.md`
- `C:\API\interno\REPO_LOG.md`
- `C:\API\interno\docs\historial\implementation\master_implementation_historyYYYYMMDD.md`

---

### Step 2 — Generate `backend_status_report.md`

Create or overwrite the file in the project's persistent documentation:
`C:\API\interno\docs\historial\implementation\backend_status_report_YYYYMMDD.md`

The report MUST include:
1. **Table: Completitud por Microservicio** — for each service: name, port, % complete, status emoji, brief description.
   - Services to include: `auth_service` (8001), `kiosk_service` (8020), `master_data_service` (8003), `subscription_service` (8005), `inventory_service` (8006), `wms_service` (8007), `tickets_service` (8004), `mes_service` (8002), `hr_service` (8009), `notification_service` (8008), `common`.
2. **Section: ¿Qué le falta a cada servicio?** — bullet checklist per service of all remaining gaps.
3. **Table: Cobertura Funcional del Ecosistema** — capability rows with % coverage.
4. **Table: Bloqueos Principales** — priority (🔴/🟡/🟢), blocker, affected service.
5. **Footer**: Global % estimate and date.

---

### Step 3 — Generate `frontend_status_report.md`

Create or overwrite the file in the project's persistent documentation:
`C:\API\interno\docs\historial\implementation\frontend_status_report_YYYYMMDD.md`

The report MUST include:
1. **Table: Completitud por Módulo** — for each Angular module: name, route, % complete, status emoji.
   - Modules to include: `auth`, `core`, `onboarding`, `home`, `inventory`, `catalog`, `users`, `tickets`, `production`, `admin`, `system`, `shared`, `event-kiosk`.
2. **Section: ¿Qué le falta a cada módulo?** — bullet checklist per module of remaining gaps.
3. **Table: Cobertura Funcional Frontend→Backend** — capability alignment with backend.
4. **Table: Bloqueos Principales** — priority, blocker, affected module.
5. **Table: Resumen Comparativo Backend vs Frontend** — side-by-side completion comparison.
6. **Footer**: Stack info (Angular 21 Zoneless, Signals, TailwindCSS), global % estimate, date.

---

### Step 4 — Update Historical Task Files
- Mark as `[x]` all tasks that were completed during the day in `docs/historial/tasks/consolidated_tasksYYYYMMDD.md`.
- Ensure `docs/historial/implementation/master_implementation_historyYYYYMMDD.md` accurately describes the technical progress.

---

### Step 5 — Update `REPO_LOG.md` and `PHASE_SPECS.md`
- Add a new dated entry (today's date) with the work done during the session in `C:\API\interno\REPO_LOG.md`.
- Mark the current phase status in `C:\API\interno\docs\specs\PHASE_SPECS.md` (✅ COMPLETED / 🔄 IN PROGRESS / 🟡 PLANNED).

---

### Step 6 — Update SERVICE_LOG.md files (if changed)
For each microservice that had code changes during the session, update its `SERVICE_LOG.md`.
Add or update the **Pending Backlog** section with checkboxes for remaining tasks.

---

### Step 7 — Final Summary to User
After all files are generated and updated, provide the user with:
1. A brief summary table of the 2 status reports (backend %, frontend %, global %).
2. The top 3 critical blockers across the system.
3. A suggested priority for the next session.
