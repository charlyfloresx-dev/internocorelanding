---
description: Initialize InternoCore (Dockers, DBs, Seeds, Compliance)
---

This workflow initializes the development environment, ensures databases are ready, runs seeds, and performs an architectural audit.

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

2. Verify Database Existence and Schema
   ```powershell
   # Check if main databases are ready
   docker exec -t interno-db psql -U user -d postgres -c "\l"
   ```

3. Run Architectural Audit (Rules from generate_code_graph.py)
   ```powershell
   python backend/scripts/generate_code_graph.py
   ```

4. Verify Microservice Stability
   ```powershell
   docker compose ps
   ```

5. Suggest fixes if any microservice is 'Exited'
   - Check logs: `docker compose logs --tail 20 [service-name]`
   - Apply Pydantic BaseSettings for config if missing (Critical for AWS Readiness)
   - Ensure MultiTenantBase is used correctly in Repositories
