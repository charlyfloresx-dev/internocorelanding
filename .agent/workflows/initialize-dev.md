# Workflow: Initialize InternoCore Dev Environment (Microservices Mode)

Use this workflow to start the full microservices stack for development.

## 1. Environment Cleanup

> [!IMPORTANT]
> Detiene todos los contenedores y elimina volúmenes para un estado limpio.
> Para un reset sin borrar datos (mantiene la DB), omite el flag `-v`.
```powershell
# Reset completo (borra DB y sesiones WhatsApp)
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans

# Reset suave (mantiene datos, solo baja contenedores)
docker compose -f infrastructure/docker/docker-compose.dev.yml down --remove-orphans
```

## 2. Application Startup

### Option A: Core Stack (Lightweight - Para Frontend/Mobile Dev)
> [!TIP]
> Login, Productos, Stock, Notificaciones y WhatsApp.
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d auth-service subscription-service master-data-service inventory-service notification-service hcm-service whatsapp-gateway gateway
```

### Option B: Full Industrial Stack (Recomendado)
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

### Option C: Rebuild de un servicio específico
> [!WARNING]
> Al reconstruir servicios con `--build`, Nginx puede quedar con DNS stale.
> **Siempre reinicia el gateway después de un rebuild parcial:**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build <service-name>
docker compose -f infrastructure/docker/docker-compose.dev.yml restart gateway
```

### Option D: Async Workers (Opcional)
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml -f infrastructure/docker/docker-compose.workers.yml up -d
```

## 3. Database Migration & Initialization

> [!IMPORTANT]
> Los contenedores deben estar UP antes de correr migraciones.
```powershell
# Migraciones Alembic en todos los servicios activos
powershell -ExecutionPolicy Bypass -File infrastructure/docker/migrate_all.ps1

# Seed industrial (datos de empresa, usuarios, productos, almacenes)
docker run --rm --network docker_interno-network -v ${PWD}/backend:/backend -w /backend `
  --env-file .env `
  --env DATABASE_URL=postgresql+asyncpg://user:internocore_db_pass_2026@interno-db-dev:5432/dbname `
  --env CORE_DATABASE_URL=postgresql+asyncpg://user:internocore_db_pass_2026@interno-db-dev:5432/dbname `
  --env PYTHONPATH=/backend `
  interno-auth-service:latest python scripts/unified_industrial_seed.py
```

## 4. Verify Status

```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml ps
```

Contenedores esperados:

| Contenedor | Puerto host |
|---|---|
| interno-db-dev | 5433 |
| interno-redis-dev | 6379 |
| interno-auth-dev | 8001 |
| interno-subscription-dev | 8002 |
| interno-master-data-dev | 8003 |
| interno-inventory-dev | 8006 |
| interno-tickets-dev | 8008 |
| interno-notification-dev | 8009 |
| interno-hcm-dev | 8004 |
| interno-whatsapp-gateway-dev | 3011 |
| interno-gateway-dev | 8000 |

## 5. Ecosystem Validation

```powershell
powershell -ExecutionPolicy Bypass -File scripts/validate_ecosystem.ps1
```

## 6. WhatsApp Gateway — Sesión y Pruebas

> [!IMPORTANT]
> El contenedor `whatsapp-gateway` arranca en el Paso 2 (Option A y B).
> La sesión persiste en el volumen `docker_whatsapp_sessions_dev` entre reinicios.
> Si el contenedor se reconstruyó, al hacer "Iniciar" reconecta automáticamente
> con LocalAuth (sin re-escanear QR, si el volumen está intacto).

### 6.1 Verificar que el gateway está corriendo

```powershell
docker logs interno-whatsapp-gateway-dev --tail 5
# Esperado: 🚀 InternoCore WhatsApp Gateway running on port 3000
```

### 6.2 Vincular sesión WhatsApp (primera vez o sesión expirada)

1. Abre el portal Angular como `admin`
2. En el menú lateral: **Administración → WhatsApp Gateway** (drawer deslizable)
3. Haz clic en **"Iniciar y generar QR"**
4. En tu teléfono: **WhatsApp → Ajustes → Dispositivos vinculados → Vincular dispositivo**
5. Escanea el QR — estado pasa a **CONNECTED** en ~10 s

### 6.3 Probar envío de mensaje

```powershell
# Flow completo: login → status → test-send → logs del gateway
python backend/tickets_service/scripts/test_whatsapp_send.py

# Número específico o grupo
python backend/tickets_service/scripts/test_whatsapp_send.py --to +52XXXXXXXXXX
python backend/tickets_service/scripts/test_whatsapp_send.py --to "120363XXXXXX@g.us"
```

### 6.4 Descubrir JIDs de grupos y registrar mappings

```powershell
# Listar grupos disponibles en la sesión activa (con sus JIDs)
python backend/tickets_service/scripts/test_whatsapp_chats.py

# Registrar un grupo (usar el JID del output anterior)
python backend/tickets_service/scripts/test_whatsapp_chats.py `
  --register TECNICOS_PLANTA "120363XXXXXX@g.us" `
  --display-name "Técnicos de Planta"
```

### 6.5 Rutas Nginx → Notification Service → Gateway

```
GET|POST /api/v1/whatsapp/*  →  notification-service:8009  →  whatsapp-gateway:3000
```

How-To completo: `docs/howto/whatsapp_pairing_and_notifications.md`

## 7. Frontend Dev Server (Opcional)

```powershell
cd frontend
npm run start
# → http://localhost:4200
```

## 8. Mobile App (Interno POS — Flutter)

```powershell
cd src/interno_billing_app
flutter pub get
flutter run -d adb-ZL7324NDXD-e2sm8j._adb-tls-connect._tcp --debug
```

Configuración: Login Screen → URL `http://<IP_LOCAL>:8000` (Nginx Gateway)
