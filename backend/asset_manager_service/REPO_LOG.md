# REPO LOG — Interno Assets CRM

Bitácora de desarrollo del microservicio Asset Manager.

---

### [2026-04-25] Sprint 1: Bootstrap & Financial Engine
- **Inception**: Creación del servicio bajo Clean Architecture.
- **Financial Engine**: Implementación de `OpportunityEvaluator` con lógica ROI + Risk Buffer.
- **Integración GIS**: Conexión asíncrona con el Master Data Service via BackgroundTasks.
- **Dockerización**: Configuración de `Dockerfile` multi-etapa con inyección de secretos AWS.
- **Data Schema**: Modelos `Opportunity`, `ZoneConfig` y `AuditLog` inicializados.
- **Bug Fix**: Corrección de `ModuleNotFoundError: boto3` mediante la inclusión de `common/requirements.txt` en el build.
- **Bug Fix**: Corrección de `AttributeError: DB_USER` migrando a `settings.DATABASE_URL` SSOT.
- **Status**: ✅ Up and Running. DB Created. Pending final migration verification.

### [2026-04-23] Hallazgos GIS (from Status Report)
- **Bloqueo RPPC**: El API `obtenerLotes` devuelve `[]` para claves válidas (ej. `PK020119`). Se requiere pivotar a sesión persistente o portal de pagos municipal.
- **Inconsistencia WMS**: Los polígonos de unidades individuales (Incisos A, B, C) no existen en la capa pública; el mapa devuelve el predio padre (ej. 6315 vs 6319-C).
- **Herramienta de Diagnóstico**: Se mantiene `scratch_run_gis.py` para validación rápida de nuevas estrategias de scraping.

---
*(Fin del log)*
