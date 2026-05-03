# Workflow: Hard Reset Monolítico Industrial 🏗️🔥

Este workflow realiza una limpieza profunda del ecosistema InternoCore Unificado, eliminando volúmenes, cache y recreando la base de datos maestra desde cero con trazabilidad forense.

## Pasos del Proceso

### 1. Demolición y Limpieza de Volúmenes // turbo
Detiene todos los servicios del monolito y elimina volúmenes persistentes.
```powershell
docker compose -f docker/docker-compose.monolith.yml down -v --remove-orphans
```

### 2. Ignición de Servicios (Rebuild) // turbo
Levanta los contenedores reconstruyendo las imágenes para asegurar la integridad del código.
```powershell
docker compose -f docker/docker-compose.monolith.yml up -d --build
```

### 3. Sincronización de Esquemas y Salud
Esperamos a que el monolito termine su `lifespan` (creación de tablas vía SQLAlchemy Metadata).
> [!NOTE]
> El Monolito Unificado crea automáticamente todas las tablas (auth, master, inv, tickets) al iniciar.

### 4. Siembra de Datos Maestros Auditada (Unified Seed) // turbo
Ejecuta el orquestador unificado que pobla Auth, Master Data y WMS Layout con logs de auditoría.
```powershell
docker exec interno-monolith python3 scripts/unified_industrial_seed.py
```

### 5. Verificación de Reporte de Auditoría // turbo
Valida que la inicialización haya generado el rastro forense obligatorio en la base de datos.
```powershell
docker exec interno-db psql -U user -d dbname -c "SELECT count(*) as total_audit_logs FROM audit_logs;"
```

---
**Status:** ✅ Unified Monolith Ready — Last updated: 2026-05-03
