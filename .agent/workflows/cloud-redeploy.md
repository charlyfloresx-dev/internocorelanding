---
description: Cloud Orchestrator — Full Redeploy (VPC Bridge + Services)
---

Este workflow re-ensambla la infraestructura industrial en AWS us-east-2 después de un `cloud-nuke`.

### 1. Preparar Imágenes en ECR // turbo
Asegúrate de que la imagen del monolito esté actualizada en el registro de AWS.
```powershell
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 584094645491.dkr.ecr.us-east-2.amazonaws.com
docker build -t interno-monolith -f backend/Monolith.Dockerfile ./backend
docker tag interno-monolith:latest 584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest
docker push 584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest
```

### 2. Ejecutar Orquestador de Infraestructura // turbo
Crea Security Groups, VPC Endpoints, VPC Connectors y despliega los servicios en App Runner.
```powershell
powershell -ExecutionPolicy Bypass -File backend/scripts/infraestructure_aws/01_deploy_full_stack.ps1
```

### 3. Verificar Conectividad PrivateLink
Una vez que el servicio esté `Running`, verifica que puede alcanzar Secrets Manager sin salida a internet (aislamiento industrial).
- Revisa los logs en CloudWatch: `/aws/apprunner/auth-service-prod/...`

### 4. Sincronizar Documentación
Actualiza el estado en [INFRASTRUCTURE_STATE.md](file:///c:/API/interno/docs/infraestructura/INFRASTRUCTURE_STATE.md) a **CLOUD ACTIVE**.

Notes:
- El script utiliza la VPC `vpc-0be05235bbfedf785` (NexoSuite-Production).
- Se requiere que el usuario `carlos.flores` tenga las Access Keys configuradas.
