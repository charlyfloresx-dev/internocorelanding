# AWS Infrastructure Reference - InternoCore Production
**Region**: us-east-2 (Ohio)
**Account**: 584094645491
**Ultima Validacion**: 2026-04-17 (Phase 55 - auth_service E2E confirmado)

---

## Estado del Despliegue

| Microservicio | Estado | URL |
|---|---|---|
| auth_service | ACTIVE - Running | via ALB puerto 80 |
| inventory_service | Pendiente | - |
| master_data_service | Pendiente | - |
| hr_service | Pendiente | - |

**ALB DNS Publico**: `InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com`
**CloudFront (Frontend)**: `https://d36af6ioy7l4ga.cloudfront.net`

---

## Red (VPC)

| Recurso | ID | CIDR |
|---|---|---|
| VPC | `vpc-0be05235bbfedf785` | `10.0.0.0/16` |
| Nombre | `NexoSuite-Production-VPC-vpc` | - |

### Subredes Publicas (ALB + ECS actualmente)
| Subnet | AZ | CIDR |
|---|---|---|
| `subnet-0db91c91053baa0b1` | us-east-2a | `10.0.0.0/20` |
| `subnet-0a2c4c76bac25294b` | us-east-2b | `10.0.16.0/20` |
| `subnet-0a3999973a997b0e6` | us-east-2c | `10.0.32.0/20` |

### Subredes Privadas (RDS - para ECS cuando se repare NAT)
| Subnet | AZ | CIDR |
|---|---|---|
| `subnet-04e7fcf2d855dbb96` | us-east-2a | `10.0.128.0/20` |
| `subnet-0611bd3d756934140` | us-east-2b | `10.0.144.0/20` |
| `subnet-0fab7c07f6e31e1c7` | us-east-2c | `10.0.160.0/20` |

> **NOTA**: ECS corre actualmente en subredes PUBLICAS con `assignPublicIp=ENABLED`.
> El NAT Gateway tiene estado `blackhole`. Pendiente: recrear NAT o crear VPC Endpoints
> para mover ECS a subredes privadas (mejora de seguridad).

---

## Security Groups

| SG | ID | Uso |
|---|---|---|
| InternoCore-Auth-Service-SG | `sg-045b7479d82ab9af5` | Contenedores ECS |
| InternoCore-ALB-SG | `sg-013db8949977135a7` | Load Balancer |
| nexosuite-rds-sg | `sg-0a151d7b5d8e8bcf0` | RDS PostgreSQL |

### Reglas criticas:
- ECS SG **Ingress**: Puerto 8000 solo desde ALB SG (`sg-013db8949977135a7`)
- ECS SG **Egress**: Todo trafico habilitado (0.0.0.0/0) — necesario para AWS APIs
- RDS SG **Ingress**: Puerto 5432 desde ECS SG
  - ADVERTENCIA: Actualmente abierto a `0.0.0.0/0`. Restringir a ECS SG post-estabilizacion.

---

## Base de Datos (RDS PostgreSQL)

| Campo | Valor |
|---|---|
| Identifier | `interno-core-db` |
| Endpoint | `interno-core-db.c920i68eetxr.us-east-2.rds.amazonaws.com` |
| Puerto | `5432` |
| Database | `interno_db` |
| Usuario | `postgres` |
| SG | `sg-0a151d7b5d8e8bcf0` |
| Region | `us-east-2` |

> La password del RDS esta en AWS Secrets Manager. Ver seccion de Secretos.

---

## Secrets Manager

| Secret ID | Descripcion |
|---|---|
| `interno-core/auth-service/prod` | Credenciales auth_service produccion |

### Estructura del secreto (campos requeridos):
```json
{
    "database_url": "postgresql+asyncpg://USER:PASS@RDS_ENDPOINT:5432/interno_db",
    "secret_key": "<JWT signing key - 64 chars alfanumericos>",
    "int_internal_api_key": "<clave inter-microservicio>",
    "env_mode": "aws",
    "aws_region": "us-east-2"
}
```

### Para crear/actualizar un secreto SIEMPRE usar archivo:
```powershell
# 1. Crear payload en un archivo (NUNCA inline en PowerShell)
$payload = @{
    database_url = "postgresql+asyncpg://postgres:PASS@interno-core-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432/interno_db"
    secret_key   = "TU_KEY_AQUI"
    int_internal_api_key = "TU_API_KEY_AQUI"
    env_mode     = "aws"
    aws_region   = "us-east-2"
}
$payload | ConvertTo-Json | Out-File -Encoding UTF8 secret_payload.json

# 2. Crear o actualizar
aws secretsmanager put-secret-value `
    --secret-id "interno-core/[SERVICE]/prod" `
    --secret-string file://secret_payload.json `
    --region us-east-2

# 3. BORRAR el archivo local inmediatamente
Remove-Item secret_payload.json
```

---

## ECS Fargate

| Campo | Valor |
|---|---|
| Cluster | `nexosuite-production-cluster` |
| Task Definition | `interno-auth-service-task:1` |
| IAM Task Role | `InternoCore-Auth-TaskRole` |
| IAM Exec Role | `ecsTaskExecutionRole` |

### Permisos minimos del Task Role:
- `secretsmanager:GetSecretValue` para el ARN del secreto del servicio
- `ecr:GetAuthorizationToken`, `ecr:BatchGetImage` (via execution role)
- `logs:CreateLogStream`, `logs:PutLogEvents` al log group del servicio

### Variables de entorno OBLIGATORIAS en la Task Definition:
```
CORE_ENV_MODE    = aws
AWS_SECRET_ID    = interno-core/[SERVICE]/prod
AWS_REGION       = us-east-2
```

> Estas 3 variables son suficientes. El secreto en Secrets Manager provee el resto.

---

## Application Load Balancer

| Campo | Valor |
|---|---|
| Nombre | `InternoCore-ALB` |
| ARN | `arn:aws:elasticloadbalancing:us-east-2:584094645491:loadbalancer/app/InternoCore-ALB/60e561c290856316` |
| DNS Publico | `InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com` |
| Estado | `active` |
| Listener | Puerto 80 HTTP |
| SG | `sg-013db8949977135a7` |

### Target Groups:
| Nombre | ARN | Puerto | Health Path |
|---|---|---|---|
| Auth-Service-TG | `arn:aws:elasticloadbalancing:us-east-2:584094645491:targetgroup/Auth-Service-TG/9ed954d5a6a24826` | 8000 | `/` |

---

## ECR Registry

| Servicio | URI |
|---|---|
| auth_service | `584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service` |

### Autenticar Docker con ECR:
```powershell
aws ecr get-login-password --region us-east-2 | `
    docker login --username AWS --password-stdin `
    584094645491.dkr.ecr.us-east-2.amazonaws.com
```

---

## Frontend (S3 + CloudFront)

| Campo | Valor |
|---|---|
| S3 Bucket | `internocore-frontend-production-584094645491` |
| CloudFront URL | `https://d36af6ioy7l4ga.cloudfront.net` |
| Config | SPA: errors 403/404 redirigen a index.html |

---

## Comandos de diagnostico rapido

```powershell
# Ver estado del ECS service
aws ecs describe-services --cluster nexosuite-production-cluster --services auth-service-prod --region us-east-2 --query "services[0].{Status:status,Running:runningCount}"

# Ver logs en tiempo real (ultimo stream)
$STREAM = aws logs describe-log-streams --log-group-name /ecs/interno-core-auth --order-by LastEventTime --descending --limit 1 --region us-east-2 --query "logStreams[0].logStreamName" --output text
aws logs get-log-events --log-group-name /ecs/interno-core-auth --log-stream-name $STREAM --region us-east-2 --start-from-head

# Ver salud del ALB target group
aws elbv2 describe-target-health --target-group-arn "arn:aws:elasticloadbalancing:us-east-2:584094645491:targetgroup/Auth-Service-TG/9ed954d5a6a24826" --region us-east-2

# Test rapido del servicio
Invoke-WebRequest -Uri "http://InternoCore-ALB-437730134.us-east-2.elb.amazonaws.com/" -Method GET -UseBasicParsing | Select-Object StatusCode, Content
```
