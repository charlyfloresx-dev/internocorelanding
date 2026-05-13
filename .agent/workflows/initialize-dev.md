# Workflow: Initialize InternoCore Dev Environment (Microservices Mode)

Use this workflow to start the full microservices stack for development.

## 1. Environment Cleanup
// turbo
> [!IMPORTANT]
> This will stop all running containers and remove volumes to ensure a clean state.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans
```

## 2. Infrastructure Startup (The Basics)
// turbo
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres-db redis
```

## 3. Selective Startup

### Option A: Core Stack (Lightweight - For Frontend/Mobile Dev)
// turbo
> [!TIP]
> Use this if you only need Login, Products, and Stock.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d auth-service master-data-service inventory-service gateway
```

### Option B: Full Industrial Stack (Everything)
// turbo
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

### Option C: Async Workers (Optional)
// turbo
> [!NOTE]
> Use this if you need to process Tickets, SLAs, or Email notifications.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml -f infrastructure/docker/docker-compose.workers.yml up -d
```

## 4. Database Initialization (Seed)
// turbo
```powershell
# Run the master seed in the auth container
docker exec interno-auth-dev python scripts/unified_industrial_seed.py
```

## 5. Verify Status
// turbo
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml ps
```

## 6. Ecosystem Validation
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1
```

## 7. Frontend Dev Server (Optional)
```powershell
cd frontend
npm run start
```
