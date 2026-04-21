---
description: Initialize InternoCore Unified Monolith (Docker, DB Schema, Unified Seed, Compliance)
---

This workflow initializes the **Unified Monolith** development environment:
ensures Docker is running, the monolith container is up, the DB schema is
synchronized and the industrial seed is loaded.

// turbo
0. Start Docker Desktop (if not running)
   ```powershell
   if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) { Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'; Start-Sleep -Seconds 15 }
   ```

// turbo
1. Start/Restart Docker Services
   ```powershell
   docker compose up -d --remove-orphans
   ```

2. Wait for monolith to be healthy
   ```powershell
   docker compose ps
   ```

// turbo
3. Run Unified Industrial Seed (Idempotent — safe to re-run)
   ```powershell
   docker cp backend/scripts/unified_industrial_seed.py interno-monolith:/app/scripts/unified_industrial_seed.py
   docker exec interno-monolith python3 scripts/unified_industrial_seed.py
   ```
   Expected output: `✅ SEED COMPLETADO EXITOSAMENTE`
   Credentials loaded: `charly@interno.com / charly123` → Company: `9cd9986b-89da-48b7-8733-26a2a1225b01`

4. Smoke Test: Verify monolith health endpoint
   ```powershell
   Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
   ```

5. Verify Microservice Stability
   ```powershell
   docker compose ps
   ```

6. Suggest fixes if the monolith container is 'Exited'
   - Check logs: `docker compose logs --tail 30 interno-monolith`
   - Ensure all service routers are correctly imported in `main_monolith.py`
   - Verify PYTHONPATH in `Monolith.Dockerfile` includes all service roots

Notes:
- The **unified seed** replaces the per-service seeds (`auth_service/scripts/seed.py`,
  `master_data_service/master_app/seeds/`). Those are now **legacy** and should not
  be run against the unified monolith database.
- Auth Core: BusinessGroup → Company → Roles → User Charly (ADMIN + OPERATIONS_MANAGER)
- Master Data: UOMs → MovementConcepts → Warehouse WH-001 → LOC-AUDIT-01 (cap 100) → SKU-PROD-01
