# Workflow: Initialize InternoCore Dev Environment (Microservices Mode)

Use this workflow to start the full microservices stack for development.

## 1. Environment Cleanup
// turbo
> [!IMPORTANT]
> This will stop all running containers and remove volumes.
```powershell
docker compose down -v --remove-orphans
```

## 2. Infrastructure Startup
// turbo
```powershell
docker compose up -d postgres-db
```

## 3. Database Initialization
// turbo
Wait for Postgres to be healthy, then run the unified seed.
```powershell
# We use the monolith container or a temporary one to run the seed if the services are not up yet.
# Or better, start the core services first.
docker compose up -d auth-service master-data-service inventory-service
```

// turbo
```powershell
# Run the seed (ensure PYTHONPATH is set or run from a service container)
docker exec auth-service-api python3 /app/scripts/unified_industrial_seed.py
```

## 4. Full Stack Startup
// turbo
```powershell
docker compose up -d
```

## 5. Verify Status
// turbo
```powershell
docker compose ps
```

## 6. Frontend Dev Server (Optional)
If you want to run the frontend outside of Docker for faster HMR:
```powershell
cd frontend
npm run start
```
