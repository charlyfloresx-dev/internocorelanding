---
description: Synchronize project documentation, logs, and implementation plans after completing a development phase
---

// turbo-all

## When to Run
Run this workflow whenever the user asks for:
- "actualiza la documentación"
- "terminamos la fase, sincroniza"
- "sync docs"
- "actualiza los logs"
- Any request to update documentation, logs, and plans after completing a phase or set of instructions.

---

## Steps

### Step 1 — Review recent changes
Explore the current changes to determine what was worked on during the recently completed phase:
- Identify which microservices in `C:\API\interno\backend\` were modified.
- Identify which modules in `C:\API\interno\frontend\` were modified.
- Review recent conversation history or artifacts to summarize the completed work.
- **Critical Check**: Verify if any new environment variables were introduced (prefix `CORE_`).

---

### Step 2 — Create Daily Snapshots from Gemini Brain
Extract the context, technical decisions, and progress from the current Gemini "brain" (conversation context and artifacts) and create daily snapshots.
Create new files in the appropriate `docs/historial/` subdirectories:
- **`docs/historial/implementation/master_implementation_historyYYYYMMDD.md`**: Write a detailed history of the implementation steps taken today. Include architectural decisions (SSOT), patterns used, and blockers resolved.
- **`docs/historial/tasks/consolidated_tasksYYYYMMDD.md`**: Consolidate all completed, in-progress, and pending tasks from the current session. Organize them by domain.

---

### Step 3 — Update Microservice Documentation and Logs
For every microservice or frontend module that was modified during the phase:
- Update its `SERVICE_LOG.md` (for backend) or `ENGINEERING_LOG.md` (for frontend).
- Document new features, architectural changes, models, DTOs, or endpoints added.
- Update any specific `README.md` within the service if the configuration or dependencies changed (using `CORE_` prefix).

---

### Step 4 — Update Master Implementation Plan and Phase Specs
Update the global implementation tracking files:
- **`docs/specs/PHASE_SPECS.md`**: Add the newly completed phase or update status to `✅ COMPLETED`.
- **`docs/architecture/01_ARCHITECTURE.md`**: Update if core architectural patterns evolved.
- **`docs/historial/implementation/master_implementation_history.md`**: Add technical details of today's implementation to the master historical record.

---

### Step 5 — Zero Root Pollution Check
Review the project root (`C:\API\interno\`) and ensure no "pollution" occurred:
- New scripts MUST reside in `scripts/`.
- New output files or temporary logs MUST reside in `logs/` or `scratch/`.
- New documentation must be properly categorized in `docs/` subdirectories.

---

### Step 6 — Update Master Index and Project Log
- **`docs/00_MASTER_INDEX.md`**: Update links to include new snapshots created in Step 2, ensuring they point to the correct `historial/` subfolders.
- **`C:\API\interno\REPO_LOG.md`**: Add a new dated entry describing the completed phase.
- **`C:\API\interno\README.md`**: Update "Estado Técnico" if necessary.

---

### Step 7 — Commit and Push Changes
Once all documentation and code changes are finalized:
- Run `git add .` to stage all changes (including docs, configs, and patches).
- Run `git commit -m "Phase XX: [Phase Description] - Unified Secret Lifecycle & Docs Sync"`.
- Run `git push` to synchronize with the remote repository.
- Verify that the push was successful.

---

### Step 8 — Final Summary to User
After all documentation files are successfully synchronized and pushed:
- Provide the user with a concise summary of the files updated.
- Highlight the key achievements documented in this sync.
- Confirm readiness for the next phase.

---

### Step 9 — AWS Deployment Pipeline (Pendientes Fase Comercial/Industrial)
Cuando aplique, continuar con la estrategia de despliegue ECR -> ECS -> ALB para los siguientes microservicios:
1. **`inventory_service`** (Siguiente fase inmediata)
2. **`master_data_service`**
3. **`hr_service`**
