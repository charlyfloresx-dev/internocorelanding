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
   ```powershell
   docker exec interno-monolith python3 scripts/unified_industrial_seed.py
   ```
   Expected output: `✅ SEED COMPLETADO EXITOSAMENTE`

4. Smoke Test: Verify API Health
   ```powershell
   Invoke-RestMethod -Uri http://localhost:8000/health -Method Get
   ```

Notes:
- This workflow uses `docker-compose.monolith.yml`.
- Access the unified API at `http://localhost:8000`.
- Authentication, Master Data, and Inventory are all handled by this single container.
