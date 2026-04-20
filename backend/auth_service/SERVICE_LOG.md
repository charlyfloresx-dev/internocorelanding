# Auth Service - Service Log

## [2026-04-20] Phase 65: AWS App Runner FinOps Pivot
- **Deployment Strategy**: Migrado de ECS Fargate a App Runner nativo (ECR image) para aislar la facturación.
- **Limitación AWS**: Despliegue suspendido temporalmente por límite general de Sandbox (Max 2 servicios AWS). Contenedor fallido borrado preventivamente para ahorrar costos.

## [2026-04-18] AWS Cloud Stability & CORS Resolution
- **Lifecycle Bug Fix**: Inverted import sequence in `app/main.py`. Forced `load_aws_secrets` (via `app.core.config.settings`) to evaluate *before* `CORSMiddleware` locks memory origin list.
- **Secrets Fix**: Removed read-only properties (`env_mode`) from AWS Secrets JSON to prevent `AttributeError` crashing the iterative dynamic injection.
- **Deployment**: Automatic Docker registry push to `584094645491.dkr.ecr.us-east-2.amazonaws.com`.
- **ECS**: Zero-downtime rotation applied to `auth-service-prod`.

---

## [2026-04-17] Phase 55: AWS Industrial Deployment
- **ECS Fargate**: Servicio desplegado exitosamente en clúster Ohio.
- **ALB Connection**: Vinculación nativa con `Auth-Service-TG` en puerto 8000.
- **Secret Injection**: Implementado patrón `entrypoint.sh` para bypass de Pydantic initialization.
- **RDS Validated**: Conectividad verificada contra `interno-core-db` (.asyncpg).
- **Status**: ✅ PRODUCTION READY

**`entrypoint.sh` - Shell-Level Secret Injection (BREAKING CHANGE POSITIVO)**
- Se reemplazo la logica de carga de secretos desde Python a inyeccion directa en el shell
- Antes: Python cargaba secretos post-instanciacion (Pydantic los ignoraba)
- Ahora: `entrypoint.sh` extrae los secretos con `aws cli` y los exporta como env vars ANTES de que Python arranque
- Esto garantiza que Pydantic lea los valores correctos en tiempo de import

**`app/core/config.py` - Validacion Mejorada**
- Agregada condicion inteligente: solo se sincroniza si el valor de `common_settings` es distinto al default
- Agregado diagnostico de hostname con `flush=True` para CloudWatch

### Infraestructura AWS (Produccion Ohio us-east-2)

| Recurso | Valor |
|---|---|
| ECS Cluster | `nexosuite-production-cluster` |
| ECS Service | `auth-service-prod` |
| Task Role | `InternoCore-Auth-TaskRole` |
| ECR Image | `584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest` |
| RDS Endpoint | `interno-core-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432` |
| Secret ID | `interno-core/auth-service/prod` |
| Log Group | `/ecs/interno-core-auth` |
| ALB | `InternoCore-ALB-276451613.us-east-2.elb.amazonaws.com` |

### Variables de Entorno Requeridas en Task Definition ECS

```
CORE_ENV_MODE=aws
AWS_SECRET_ID=interno-core/auth-service/prod
AWS_REGION=us-east-2
```

### Lecciones Documentadas
Ver: `docs/lecciones_aprendidas/aws_deployment_lessons_20260417.md`

---

## [2026-04-17] Limpieza de Logs (compatibilidad Windows charmap)
- Eliminados todos los emojis y caracteres Unicode especiales de logs de arranque
- Reemplazados por texto ASCII puro para compatibilidad con codificacion charmap de PowerShell
- Afecta: `entrypoint.sh`, `app/core/config.py`, `common/config.py`

---

## [Versiones Anteriores]
Ver historial de Git o `docs/historial/` para versiones anteriores del service log.