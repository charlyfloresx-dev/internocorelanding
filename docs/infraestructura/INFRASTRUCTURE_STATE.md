# 🌐 InternoCore: Estado de la Infraestructura Cloud (POST-NUKE)

## 📊 Estatus Actual: **LOCAL ONLY ($0.00 AWS Cost)**
A partir del **2026-04-21**, toda la infraestructura en la nube ha sido desmantelada para evitar costos de desarrollo. El Source of Truth (SSOT) del código y la base de datos reside ahora exclusivamente en el entorno local.

### 🛑 Lo que se eliminó (Nuke to Zero):
- **App Runner:** Todos los servicios borrados (Auth, Master Data).
- **Red:** VPC Endpoints (PrivateLink) eliminados para evitar cargos por hora.
- **Base de Datos:** Instancia RDS `interno-core-db` borrada (sin snapshots).
- **Storage:** Buckets S3 de frontend borrados.
- **Registro:** Repositorios ECR purgados.

---

## 🏗️ Guía de Recuperación (Redeploy)
Cuando se decida volver a producción/staging en AWS, no se debe hacer manualmente. Se han creado scripts de orquestación para asegurar que la arquitectura de red (VPC-Bridge) sea correcta:

### 1. Preparación Local
Asegúrate de que tus imágenes de Docker estén listas:
```powershell
# Ejemplo para push manual (si el script no lo hace)
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin [ACCOUNT_ID].dkr.ecr.us-east-2.amazonaws.com
docker push [ACCOUNT_ID].dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest
```

### 2. Ejecución del Orchestrator
Ejecuta el script de re-ensamblaje que crea la red privada, los VPC Endpoints y los servicios de App Runner:
```powershell
.\backend\scripts\redeploy_internocore_aws.ps1
```

### 3. Scripts de Mantenimiento
- **Redespliegue:** `backend/scripts/redeploy_internocore_aws.ps1`
- **Limpieza Total:** `backend/scripts/aws_full_nuke.ps1`

---

## 🏛️ Referencia de Red (VPC)
- **VPC ID:** `vpc-0be05235bbfedf785` (NexoSuite-Production-VPC)
- **Subredes:** `subnet-04e7fcf2d855dbb96`, `subnet-0611bd3d756934140`, `subnet-0fab7c07f6e31e1c7`
- **Security Groups:** 
  - `sg-0a151d7b5d8e8bcf0` (RDS/App Runner Default)
  - `sg-0ea0c22fd4462c731` (VPC Endpoints SG)

## ⚠️ Lección Aprendida (Fase 65)
**NUNCA** desplegar App Runner en subredes privadas sin **Interface Endpoints** para `secretsmanager`. El freeze del bootstrap se debió al aislamiento del contenedor intentando resolver el API público de AWS sin ruta de salida.
