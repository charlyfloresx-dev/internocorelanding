# Master Implementation History — 2026-05-12

## Phase 104: Microservices Isolation & Cross-Service Import Eradication

### Objetivo
Eliminar todas las dependencias de importación directa entre microservicios, estabilizar el API Gateway (Nginx), y crear herramientas automatizadas de gobernanza arquitectónica.

### Decisiones Arquitectónicas

1. **Inter-Service Communication = HTTP Only**
   - Los microservicios NUNCA deben importar módulos de otros servicios.
   - Toda comunicación inter-servicio se realiza vía HTTP events (fire-and-forget con `httpx`).
   - El fallo de una notificación no debe bloquear la transacción principal del servicio emisor.

2. **Shared DB Queries = Raw SQL Text**
   - Cuando un servicio necesita consultar tablas de otro servicio (misma BD en dev), usa `sqlalchemy.text()` en lugar de importar modelos ORM ajenos.
   - Ejemplo: `notification_service` consulta `users`/`roles` sin importar `auth_app.models`.

3. **Nginx Gateway = Fail-Fast on Missing Upstreams**
   - Nginx verifica TODOS los upstreams al arrancar. Si uno falla, todo el Gateway muere.
   - Solución: comentar upstreams de servicios no desplegados (`wms-service`).

4. **Alembic Isolation = Unique Version Tables**
   - Cada servicio tiene su propia tabla de versiones: `alembic_version_{suffix}`.
   - Esto permite que múltiples servicios compartan la misma BD de Postgres sin colisiones de migración.

### Archivos Modificados

| Archivo | Cambio |
|---|---|
| `common/requirements.txt` | +`redis==5.0.1` |
| `hcm_service/Dockerfile` | `COPY hcm_service/hcm_app` (fix) |
| `inventory_service/.../density_guard_audit.py` | Import → HTTP dispatch |
| `inventory_service/.../transactions.py` | Import → HTTP dispatch |
| `notification_service/.../notification_service.py` | ORM import → `text()` query |
| `infrastructure/docker/nginx.conf` | +HCM, +Notification, -WMS |
| `infrastructure/docker/docker-compose.dev.yml` | +HCM, +Notification services |
| `backend/scripts/generate_code_graph.py` | +CROSS_SERVICE_IMPORT_VIOLATION rule |
| `scripts/validate_ecosystem.ps1` | New: Gateway ping validator |
| `backend/README.md` | New: Gold Standard documentation |
| `README.md` | +Section 9: Gold Standard |

### Resultado del Code Graph
```
TOTAL ERRORS: 2 (Warnings only — ENV_ACCESS in inventory, acceptable)
CRITICAL: 0
CROSS_SERVICE_IMPORT_VIOLATION: 0
INTER-SERVICE DEPENDENCIES: (empty — fully isolated)
```
