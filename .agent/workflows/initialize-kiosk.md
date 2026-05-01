# Workflow: Initialize InternoCore Kiosk Environment

Use this workflow to start the Industrial Kiosk environment (subset of services + MinIO).

## 1. Environment Cleanup
// turbo
```powershell
docker compose -f docker/docker-compose.kiosk.yml down -v --remove-orphans
```

## 2. Startup
// turbo
```powershell
docker compose -f docker/docker-compose.kiosk.yml up -d --build
```

## 3. Database Seed (Industrial)
// turbo
```powershell
docker exec kiosk-auth-service python3 /app/scripts/unified_industrial_seed.py
```

## 4. MinIO Setup
Ensure the bucket `kiosk-events` exists.
// turbo
```powershell
# Optional: Setup MinIO via CLI if needed
```

## 5. Verify Status
// turbo
```powershell
docker compose -f docker/docker-compose.kiosk.yml ps
```
