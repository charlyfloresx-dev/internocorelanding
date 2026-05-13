# Workflow: Hard Reset Monolítico Industrial 🏗️🔥

Este workflow realiza una limpieza profunda del ecosistema InternoCore Unificado, eliminando volúmenes, cache y recreando la base de datos maestra desde cero con trazabilidad forense.

## Pasos del Proceso

### 1. Sanitización de Archivos .env // turbo
Elimina BOM (Byte Order Mark) de archivos `.env` que PowerShell introduce y que corrompe `python-dotenv`.
```powershell
python -c "
for path in ['.env', 'backend/.env']:
    try:
        with open(path, 'rb') as f:
            data = f.read()
        if data.startswith(b'\xef\xbb\xbf'):
            with open(path, 'wb') as f:
                f.write(data[3:])
            print(f'BOM removed from {path}')
        else:
# Workflow: Hard Reset - InternoCore Clean Slate

Use this workflow to NUCLEARLY reset the environment. This deletes all data, images, and network configurations.

## 1. Stop and Remove All Environments
// turbo
```powershell
# Stop Dev Stack
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans

# Stop On-Prem Monolith
docker compose -f infrastructure/onprem/docker-compose.yml down -v --remove-orphans

# Stop any legacy root-level stack
docker compose down -v --remove-orphans
```

## 2. Forensic Image & Volume Purge
// turbo
> [!CAUTION]
> This will delete all unused images and volumes. It is non-reversible.
```powershell
docker system prune -a --volumes -f
```

## 3. Environment Variable Sanitization
// turbo
```powershell
# Remove BOM and hidden characters from .env
python -c "content = open('.env', 'rb').read().replace(b'\xef\xbb\xbf', b''); open('.env', 'wb').write(content)"
```

## 4. Re-Initialization
After this, follow the [initialize-dev.md](./initialize-dev.md) or [initialize-monolith.md](./initialize-monolith.md) workflows.
lifespan` (creación de tablas vía SQLAlchemy Metadata).
> [!NOTE]
> El Monolito Unificado crea automáticamente todas las tablas (auth, master, inv, tickets) al iniciar.
> Verificar con `docker logs interno-monolith --tail 5` que aparezca `Application startup complete`.

### 5. Siembra de Datos Maestros Auditada (Unified Seed) // turbo
Ejecuta el orquestador unificado que pobla Auth, Master Data y WMS Layout con logs de auditoría.
```powershell
docker exec interno-monolith python3 scripts/unified_industrial_seed.py
```

### 6. Verificación de Reporte de Auditoría // turbo
Valida que la inicialización haya generado el rastro forense obligatorio en la base de datos.
```powershell
docker exec interno-db psql -U user -d dbname -c "SELECT count(*) as total_audit_logs FROM audit_logs;"
```

---
**Status:** ✅ Unified Monolith Ready — Last updated: 2026-05-12
