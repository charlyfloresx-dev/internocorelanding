# Guia de Despliegue AWS - Microservicios InternoCore
**Version**: 1.0 - Basada en lecciones de Phase 55 (auth_service)
**Fecha**: 2026-04-17

Esta guia es el SSOT para desplegar cualquier microservicio backend de InternoCore en AWS ECS Fargate + RDS Ohio.

---

## Prerequisitos por servicio

Antes de iniciar el despliegue de un nuevo microservicio, verificar:

- [ ] Imagen Docker construida y funcional localmente
- [ ] Repositorio ECR creado para el servicio
- [ ] Target Group en el ALB creado para el servicio
- [ ] Log Group en CloudWatch creado (`/ecs/interno-core-[servicio]`)
- [ ] Task Definition registrada con las 3 variables de entorno minimas
- [ ] IAM Task Role con permiso `secretsmanager:GetSecretValue`

---

## Paso 1: Crear el secreto en Secrets Manager

**Regla de oro**: SIEMPRE usar `file://`. NUNCA ingresar JSON complejo inline en PowerShell.

```powershell
# 1. Generar llaves seguras
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
$API_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# 2. Crear payload
$payload = @{
    database_url         = "postgresql+asyncpg://postgres:PASS_RDS@interno-core-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432/interno_db"
    secret_key           = $SECRET_KEY
    int_internal_api_key = $API_KEY
    env_mode             = "aws"
    aws_region           = "us-east-2"
}
$payload | ConvertTo-Json | Out-File -Encoding UTF8 secret_payload.json

# 3. Crear el secreto (nombre: interno-core/[SERVICIO]/prod)
aws secretsmanager create-secret `
    --name "interno-core/[SERVICIO]/prod" `
    --region us-east-2 `
    --secret-string file://secret_payload.json

# 4. BORRAR el archivo local
Remove-Item secret_payload.json
```

**Verificar que el JSON es valido antes de subir**:
```powershell
Get-Content secret_payload.json | python3 -c "import json,sys; json.load(sys.stdin); print('JSON valido')"
```

---

## Paso 2: Preparar el entrypoint.sh del servicio

Copiar el patron ya validado de `auth_service/entrypoint.sh`. Los puntos criticos:

```sh
#!/bin/sh
set -e

# PRE-BOOT: Inyectar secretos ANTES de que Python arranque
# Esto es critico: Pydantic lee env vars al instanciarse (import time).
if [ "$CORE_ENV_MODE" = "aws" ] || [ "$ENV_MODE" = "aws" ]; then
    SECRET_ID="${AWS_SECRET_ID:-interno-core/[SERVICIO]/prod}"
    
    SECRET_JSON=$(timeout 15 aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ID" \
        --region "${AWS_REGION:-us-east-2}" \
        --query 'SecretString' --output text 2>/dev/null) || true

    if [ -n "$SECRET_JSON" ]; then
        DB_URL=$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('database_url',''))" 2>/dev/null || echo "")
        [ -n "$DB_URL" ] && export DATABASE_URL="$DB_URL" && export CORE_DATABASE_URL="$DB_URL"
        echo "[BOOT] DATABASE_URL inyectada."
    else
        echo "[BOOT] WARNING: Timeout o error en Secrets Manager. Usando env vars de Task Definition."
    fi
fi

# Migraciones
python -m alembic upgrade head

# Seed (tolerante a fallos)
python scripts/seed.py || echo "Seed fallo o ya existe."

# Servidor
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
```

**Por que esto funciona**: Cuando Python inicia, Pydantic `BaseSettings` lee variables de entorno al instanciarse. Si `DATABASE_URL` ya esta en el environment del shell, la toma correctamente desde el primer import.

---

## Paso 3: Verificar common/config.py

El `load_aws_secrets()` de `common/config.py` acepta los modos: `aws`, `prod`, `production`.
Asegurarse de que la Task Definition use `CORE_ENV_MODE=aws`.

**Mapeo de secretos a atributos Pydantic**:
| Clave en secreto | Atributo en Settings |
|---|---|
| `database_url` | `DATABASE_URL` |
| `secret_key` | `SECRET_KEY` |
| `int_internal_api_key` | `int_internal_api_key` |

---

## Paso 4: Task Definition

Estructura minima obligatoria:

```json
{
  "family": "interno-[servicio]-task",
  "taskRoleArn": "arn:aws:iam::584094645491:role/InternoCore-Auth-TaskRole",
  "executionRoleArn": "arn:aws:iam::584094645491:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [{
    "name": "[servicio]",
    "image": "584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/[servicio]:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "CORE_ENV_MODE", "value": "aws"},
      {"name": "AWS_SECRET_ID",  "value": "interno-core/[servicio]/prod"},
      {"name": "AWS_REGION",     "value": "us-east-2"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/interno-core-[servicio]",
        "awslogs-region": "us-east-2",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

---

## Paso 5: Crear ECS Service CON ALB desde el inicio

**NO crear el service sin ALB y agregarlo despues** — ECS no permite modificar `loadBalancers` en caliente.

```powershell
aws ecs create-service `
    --cluster nexosuite-production-cluster `
    --service-name [servicio]-prod `
    --task-definition interno-[servicio]-task:1 `
    --desired-count 1 `
    --launch-type FARGATE `
    --network-configuration "awsvpcConfiguration={subnets=[subnet-0a2c4c76bac25294b,subnet-0db91c91053baa0b1,subnet-0a3999973a997b0e6],securityGroups=[sg-045b7479d82ab9af5],assignPublicIp=ENABLED}" `
    --load-balancers "targetGroupArn=TG_ARN,containerName=[servicio],containerPort=8000" `
    --health-check-grace-period-seconds 120 `
    --region us-east-2
```

`health-check-grace-period-seconds 120`: necesario porque el `entrypoint.sh` tarda ~60-90s en ejecutar migraciones y seed antes de levantar uvicorn.

---

## Paso 6: Verificar el despliegue

```powershell
# 1. Ver que el contenedor arranco
aws ecs describe-services `
    --cluster nexosuite-production-cluster `
    --services [servicio]-prod `
    --region us-east-2 `
    --query "services[0].{Status:status,Running:runningCount}"

# 2. Ver logs de arranque (buscar DATABASE_URL inyectada)
$STREAM = aws logs describe-log-streams `
    --log-group-name /ecs/interno-core-[servicio] `
    --order-by LastEventTime --descending --limit 1 `
    --region us-east-2 --query "logStreams[0].logStreamName" --output text
aws logs filter-log-events `
    --log-group-name /ecs/interno-core-[servicio] `
    --log-stream-names $STREAM `
    --filter-pattern "DATABASE_URL" --region us-east-2

# 3. Ver salud del ALB
aws elbv2 describe-target-health --target-group-arn TG_ARN --region us-east-2

# 4. Test del health endpoint
Invoke-WebRequest -Uri "http://InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com/[PREFIX]/" `
    -Method GET -UseBasicParsing | Select-Object StatusCode, Content
```

---

## Checklist de Seguridad Post-Despliegue

- [ ] El secreto `secret_payload.json` local fue eliminado
- [ ] RDS SG restringido a ECS SG (no `0.0.0.0/0`)
- [ ] Los logs de CloudWatch no exponen passwords ni secret keys
- [ ] Las variables sensibles NO estan como env vars en la Task Definition (solo las 3 de configuracion)
- [ ] El Task Role solo tiene permisos al secreto del servicio, no a todos

---

## Nota sobre Passwords en Seeds

Los seeds de testing usan passwords hardcodeadas (`charly123`, `ops123`, etc.).
En produccion real, considerar:
- Generar passwords aleatorias en el seed y registrarlas en Secrets Manager
- O deshabilitar el seed en produccion y crear usuarios via API con passwords rotadas

Para InternoCore en su estado actual, los seeds son datos de configuracion inicial del sistema 
(no usuarios finales), por lo que el riesgo es manejable si el RDS no es accesible publicamente.

---

## Historial de Despliegues

| Fecha | Servicio | Estado | Notas |
|---|---|---|---|
| 2026-04-17 | auth_service | COMPLETADO | Phase 55, E2E validado via ALB |
| Pendiente | inventory_service | - | Siguiente fase |
| Pendiente | master_data_service | - | - |
| Pendiente | hr_service | - | - |
