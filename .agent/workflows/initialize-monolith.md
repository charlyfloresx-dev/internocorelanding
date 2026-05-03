---
description: Initialize InternoCore Unified Monolith (Exclusive Mode)
---

This workflow initializes the **Unified Monolith** environment using `docker-compose.monolith.yml`.
It ensures all microservices are stopped before starting the monolith to avoid port conflicts.

// turbo
0. Start Docker Desktop (if not running)
   ```powershell
   if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) { Start-Process 'C:\Program Files\Docker\Docker\Docker Desktop.exe'; Start-Sleep -Seconds 15 }
   ```

// turbo
1. Stop any running Microservices & Start Monolith
   ```powershell
   docker compose down; docker compose -f docker/docker-compose.monolith.yml up -d --remove-orphans
   ```

2. Wait for Monolith to be healthy
   ```powershell
   docker compose -f docker/docker-compose.monolith.yml ps
   ```

// turbo
3. Run Unified Industrial Seed (Idempotent)
   This now includes Master Data, Auth, WMS Locations, and Initial Stock Flows.
   ```powershell
   docker exec interno-monolith python3 scripts/unified_industrial_seed.py
   ```
   Expected output: `✅ SEED COMPLETED SUCCESSFULLY`

4. Smoke Test: Verify API Health
   ```powershell
   Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
   ```

// turbo
5. Verify Forensic Audit Trail
   ```powershell
   docker exec interno-db psql -U user -d dbname -c "SELECT action, table_name, count(*) FROM audit_logs GROUP BY action, table_name;"
   ```

Notes:
- This workflow uses `docker-compose.monolith.yml`.
- Access the unified API at `http://localhost:8000`.
- All operations are now recorded in the Forensic Audit Ledger.

---
**Status:** ✅ Monolith Protocol Active (WMS Ready) — 2026-05-03
