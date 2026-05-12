# Implementation History - 2026-04-17
# Phase 55: AWS Industrial Deployment - auth_service
**ESTADO FINAL**: COMPLETADO Y VALIDADO EN PRODUCCION

---

## Objetivo
Desplegar `auth_service` en AWS ECS Fargate (us-east-2) con conectividad real a RDS PostgreSQL y 
flujo de autenticacion multi-tenant validado end-to-end a traves del Application Load Balancer.

---

## Arquitectura de Produccion Validada

```
Internet
   |
   v
ALB: InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com (puerto 80)
   |
   v (Target Group: Auth-Service-TG, puerto 8000)
ECS Fargate Task (subnet publica, IP: se renueva en cada deploy)
   |                                     |
   v                                     v
RDS PostgreSQL                   AWS Secrets Manager
interno-core-db                  interno-core/auth-service/prod
.c920i68eetxr                    (DATABASE_URL, SECRET_KEY, etc.)
.us-east-2.rds.amazonaws.com
```

---

## Decisiones Tecnicas (SSOT)

### 1. Shell-Level Secret Injection (PATRON DEFINITIVO)
**Decision**: Los secretos de AWS Secrets Manager se inyectan como variables de entorno del SHELL
en `entrypoint.sh` ANTES de que Python arranque.

**Razon**: Pydantic `BaseSettings` lee variables de entorno UNA SOLA VEZ al instanciarse la clase
(en tiempo de import del modulo). Las dependencias como `create_engine()` de SQLAlchemy se 
construyen con los valores del momento de import. Un `setattr()` posterior NO recalcula estas
dependencias — el engine ya fue construido con el valor previo.

**Patron establecido** (copiar en cada nuevo servicio):
```sh
# entrypoint.sh - ANTES de cualquier `python` command:
SECRET_JSON=$(timeout 15 aws secretsmanager get-secret-value \
    --secret-id "$AWS_SECRET_ID" --region "$AWS_REGION" \
    --query 'SecretString' --output text 2>/dev/null) || true

if [ -n "$SECRET_JSON" ]; then
    DB_URL=$(echo "$SECRET_JSON" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('database_url',''))" 2>/dev/null || echo "")
    [ -n "$DB_URL" ] && export DATABASE_URL="$DB_URL" && export CORE_DATABASE_URL="$DB_URL"
fi
# Ahora si: python -m alembic upgrade head
```

### 2. Multi-Environment Config
`common/config.py` acepta `CORE_ENV_MODE` en: `development | staging | aws | prod | production`.
La Task Definition usa `CORE_ENV_MODE=aws`.

### 3. ECS Service debe crearse CON ALB desde el inicio
ECS no permite modificar `loadBalancers` despues de crear el service. Si se crea sin LB,
hay que eliminar y recrear el service completo.

### 4. Health Check Grace Period = 120s
El `entrypoint.sh` ejecuta migraciones Alembic y seed antes de levantar uvicorn.
Esto tarda entre 60-90s. El ALB necesita 120s de grace period para no matar el contenedor
antes de que este listo.

---

## Cadena de Bloqueos Resueltos

### Bloqueo 1: JSON invalido en Secrets Manager
- **Causa**: CLI de PowerShell corrompe JSON con caracteres especiales al usarlo inline
- **Sintoma**: `json.loads()` falla silenciosamente, secretos no se cargan
- **Fix**: Crear secretos desde archivo `file://secret_payload.json` SIEMPRE
- **Archivo**: `backend/auth_service/secret_payload.json` (usar y borrar)

### Bloqueo 2: Entorno `aws` no reconocido
- **Causa**: `common/config.py` solo aceptaba `"production"` para cargar secretos
- **Sintoma**: Skip silencioso, `DATABASE_URL` permanecia como `db:5432` del default
- **Fix**: `if env not in ["production", "prod", "aws"]: return`
- **Archivo**: `backend/common/config.py` linea 226

### Bloqueo 3: `setattr()` en Pydantic post-instanciacion
- **Causa**: Pydantic `BaseSettings` construye dependencias (engines SQLAlchemy) en tiempo de import
- **Sintoma**: `setattr(settings, 'DATABASE_URL', value)` no propagaba al engine ya construido
- **Fix definitivo**: Shell-level injection en `entrypoint.sh` (ver Decision 1)
- **Confirmacion**: `DEBUG: Full URL length: 49` (longitud exacta del URL default `db:5432`)

### Bloqueo 4: `aws cli` sin timeout
- **Causa**: El comando `aws secretsmanager get-secret-value` colgaba indefinidamente
- **Sintoma**: Contenedor atascado en `[BOOT] AWS MODE: Cargando secretos...` por mas de 3 minutos
- **Fix**: `timeout 15 aws secretsmanager ...` + fallback graceful si falla
- **Archivo**: `backend/auth_service/entrypoint.sh`

### Bloqueo 5: ECS Service sin LB asociado
- **Causa**: Service fue creado inicialmente sin `--load-balancers`
- **Sintoma**: Target Group vacio, ALB no routeaba al contenedor
- **Fix**: Eliminar service y recrear con `--load-balancers` y `--health-check-grace-period-seconds 120`

### Bloqueo 6: NAT Gateway en `blackhole`
- **Causa**: NAT Gateway fue eliminado pero las rutas de subnets privadas persistieron
- **Sintoma**: Cualquier trafico de salida desde subnets privadas era descartado
- **Fix temporal**: ECS en subnets PUBLICAS con `assignPublicIp=ENABLED`
- **Fix permanente pendiente**: Recrear NAT o configurar VPC Endpoints

---

## Validacion E2E Realizada

### Tests ejecutados contra produccion:
```
GET  http://InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com/
-> 200 OK | service: auth-service | version: 2.1.0

POST /api/v1/auth/login {"email":"charly@interno.com","password":"charly123"}
-> 200 OK | 4 companies | selection_token generado | latencia: 1.23s

POST /api/v1/auth/select-company {"company_id":"9cd9986b-..."}
-> 200 OK | role: admin | scopes: ["*"] | access_token + refresh_token | latencia: 0.17s
```

### JWT Claims verificados:
- `typ`: "access" (correcto)
- `company_id`: UUID de Interno Enterprise
- `roles`: ["admin"]
- `scopes`: ["*"] (wildcard admin)
- `modules`: ["auth_core", "inventory_core"]
- `readonly`: false

---

## Archivos Modificados en Phase 55

| Archivo | Cambio |
|---|---|
| `backend/auth_service/entrypoint.sh` | Shell-level secret injection + timeout |
| `backend/auth_service/app/core/config.py` | Validacion inteligente de override AWS |
| `backend/common/config.py` | Multi-env support + debug logging |
| `docs/infraestructura/aws_infrastructure_reference.md` | Reescrito con valores validados |
| `docs/infraestructura/MICROSERVICE_DEPLOY_GUIDE.md` | NUEVO - guia para futuros servicios |
| `docs/lecciones_aprendidas/aws_deployment_lessons_20260417.md` | NUEVO - 6 lecciones |
| `backend/auth_service/SERVICE_LOG.md` | Actualizado Phase 55 |
| `REPO_LOG.md` | Entrada Phase 55 COMPLETADO |
| `docs/00_MASTER_INDEX.md` | Links actualizados a Phase 55 |

---

## Estado de Produccion al Cierre de Sesion

| Componente | Estado | Detalle |
|---|---|---|
| ECS Service `auth-service-prod` | ACTIVE, Running: 1 | Con ALB nativo |
| ALB Target `10.0.0.197:8000` | healthy | Nuevo task con LB |
| RDS `interno-core-db` Ohio | Conectado | Queries SQLAlchemy confirmados |
| Secrets Manager | Sincronizado | 3 secretos mapeados correctamente |
| Alembic Migraciones | Aplicadas | Tablas multi-tenant en RDS |
| Seed de datos | Completado | Charly + 4 empresas + RBAC |
| ALB DNS | Accesible publicamente | Puerto 80 HTTP |
| Health Check ALB | healthy | Grace period 120s respetado |

---

## Pendientes para Proxima Sesion

### Seguridad
- [ ] Restringir RDS Security Group a solo ECS SG (quitar `0.0.0.0/0` en puerto 5432)
- [ ] Recrear NAT Gateway y mover ECS a subnets privadas
- [ ] HTTPS en el ALB (certificado ACM para el dominio de produccion)
- [ ] Evaluar passwords del seed: actualmente hardcodeadas (`charly123`, `ops123`, `super123`)

### Escalabilidad
- [ ] Desplegar `inventory_service` usando `MICROSERVICE_DEPLOY_GUIDE.md`
- [ ] Desplegar `master_data_service`
- [ ] Desplegar `hr_service`
- [ ] Configurar Listener Rules en ALB para routear por path prefix a cada servicio
  - `/api/v1/auth/*` -> Auth-Service-TG
  - `/api/v1/inventory/*` -> Inventory-Service-TG
  - etc.

### Frontend
- [ ] Actualizar `environment.prod.ts` con URL del ALB
- [ ] Configurar CORS en `auth_service` para el dominio de CloudFront
- [ ] Probar login completo desde la app Angular en CloudFront

### Observabilidad
- [ ] Configurar CloudWatch Alarms para CPU/Memory del servicio ECS
- [ ] Configurar alarma de health check failures en el ALB target group
