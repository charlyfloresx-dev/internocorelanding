# Workflow: Initialize InternoCore Dev Environment (Microservices Mode)

Use this workflow to start the full microservices stack for development.

## 1. Environment Cleanup
// turbo
> [!IMPORTANT]
> This will stop all running containers and remove volumes to ensure a clean state.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans
```

## 2. Application Startup

### Option A: Core Stack (Lightweight - For Frontend/Mobile Dev)
// turbo
> [!TIP]
> Use this if you only need Login, Products, and Stock.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d auth-service subscription-service master-data-service inventory-service notification-service hcm-service gateway
```

### Option B: Full Industrial Stack (Everything - Recommended)
// turbo
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build
```

### Option C: Async Workers (Optional)
// turbo
> [!NOTE]
> Use this if you need to process Tickets, SLAs, or Email notifications.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml -f infrastructure/docker/docker-compose.workers.yml up -d
```

## 3. Database Migration & Initialization
// turbo
> [!IMPORTANT]
> The containers must be UP before running the migrations. This step runs the unified Alembic migration sweep across all active services and executes the industrial seed.
```powershell
powershell -ExecutionPolicy Bypass -File infrastructure/docker/migrate_all.ps1
docker run --rm --network docker_interno-network -v ${PWD}/backend:/backend -w /backend --env-file .env --env DATABASE_URL=postgresql+asyncpg://user:internocore_db_pass_2026@interno-db-dev:5432/dbname --env CORE_DATABASE_URL=postgresql+asyncpg://user:internocore_db_pass_2026@interno-db-dev:5432/dbname --env PYTHONPATH=/backend interno-auth-service:latest python scripts/unified_industrial_seed.py
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
