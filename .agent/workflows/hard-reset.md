# Workflow: Hard Reset Industrial 🏗️🔥

Este workflow realiza una limpieza profunda del ecosistema InternoCore, eliminando volúmenes, cache y recreando bases de datos desde cero.

## Pasos del Proceso

### 1. Demolición y Limpieza de Volúmenes // turbo
Detiene todos los servicios y elimina volúmenes persistentes y orphans.
```powershell
docker-compose down -v --remove-orphans
```

### 2. Ignición de Servicios (Rebuild) // turbo
Levanta los contenedores reconstruyendo las imágenes para asegurar que no haya código "fantasma" en el cache.
```powershell
docker-compose up -d --build
```

### 3. Sincronización de Esquemas y Salud
Esperamos a que los microservicios terminen su `lifespan` (creación de tablas).
> [!NOTE]
> El Auth Service y el HR Service crean automáticamente sus tablas al iniciar.

### 4. Siembra de Datos Maestros (Seed) // turbo
Ejecuta ambos seeds en orden: primero Auth (usuarios + empresas) y luego HCM (colaboradores + RFIDs).
```powershell
python backend/auth_service/scripts/seed.py
```
```powershell
python backend/hcm_service/scripts/seed.py
```

### 5. Verificación de Autenticación // turbo
Valida que los canales Administrativo e Industrial estén operativos.
```powershell
python backend/auth_service/scripts/full_auth_flow.py
python backend/auth_service/scripts/kiosk_auth_flow.py
```

---
**Status:** ✅ Validated — Last successful run: 2026-04-14
