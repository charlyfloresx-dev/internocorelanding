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
> Use this if you only need Login, Products, Stock, and WhatsApp notifications.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d auth-service subscription-service master-data-service inventory-service notification-service hcm-service whatsapp-gateway gateway
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

## 4. Verify Status
// turbo
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml ps
```

## 5. Ecosystem Validation
// turbo
```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1
```

## 6. WhatsApp Gateway — Sesión y Pruebas

> [!IMPORTANT]
> El contenedor `whatsapp-gateway` ya arranca en el Paso 2 (Option A y B).
> Este paso cubre la vinculación de sesión y las pruebas de envío.

### 6.1 Verificar que el gateway está corriendo
// turbo
```powershell
docker logs interno-whatsapp-gateway-dev --tail 5
# Esperado: 🚀 InternoCore WhatsApp Gateway running on port 3000
```

### 6.2 Vincular sesión WhatsApp (escanear QR)

1. Abre el portal Angular como `admin` → **Administración → WhatsApp Gateway**
2. Haz clic en **"Iniciar y generar QR"**
3. En tu teléfono: **WhatsApp → Ajustes → Dispositivos vinculados → Vincular dispositivo**
4. Escanea el QR que aparece en pantalla
5. Espera el estado **CONNECTED** (aparece en ~10 s)

> [!TIP]
> La sesión persiste en el volumen `docker_whatsapp_sessions_dev` entre reinicios.
> Si el QR expira, vuelve a hacer clic en "Iniciar y generar QR".

### 6.3 Probar envío de mensaje

```powershell
# Paso A: Obtener JWT (requiere stack corriendo)
cd backend
python auth_service/scripts/full_auth_flow.py
# Copia el access_token del output

# Paso B: Enviar mensaje de prueba (número individual o grupo @g.us)
curl -X POST http://localhost:8000/api/v1/whatsapp/test-send `
  -H "Authorization: Bearer <ACCESS_TOKEN>" `
  -H "Content-Type: application/json" `
  -d '{"to": "+52XXXXXXXXXX", "message": "Prueba InternoCore WhatsApp ✅"}'

# Verificar entrega en logs del gateway
docker logs interno-whatsapp-gateway-dev --tail 10
# Esperado: [Queue] Message successfully delivered to 52XXXXXXXXXX@c.us
```

### Variables de entorno (ya en docker-compose.dev.yml)
```
PORT=3000
API_KEY=DEV_INTERNAL_KEY_123
SESSIONS_PATH=/app/sessions
```

### Ruta Nginx
```
GET|POST /api/v1/whatsapp/* → notification-service:8009 → proxy → whatsapp-gateway:3000
```

### How-To completo
Ver: `docs/howto/whatsapp_pairing_and_notifications.md`

## 7. Frontend Dev Server (Optional)
```powershell
cd frontend
npm run start
```
