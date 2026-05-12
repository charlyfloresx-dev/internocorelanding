# 🚀 Guía de Resurrección: Despliegue en Nueva Cuenta AWS

Este documento contiene la "Receta Maestra" para reconstruir el ecosistema de **InternoCore** en una cuenta de AWS completamente nueva, preservando la arquitectura industrial y el **Muro de Hierro**.

## 📋 Requisitos Previos
1. **Nueva Cuenta de AWS** activa.
2. **AWS CLI** configurado con un nuevo perfil (`aws configure --profile internocore-new`).
3. **Docker** corriendo localmente (para el push de imágenes).

## 🛠️ Fase 1: Identidad y Seguridad (IAM)
Antes de levantar servicios, debemos reconstruir el modelo de permisos.
1. Consultar `docs/infraestructura/backup_configs/iam_policies_export.json`.
2. Crear los roles necesarios:
   - `InternoCore-AppRunner-Role`: Con permisos para Secrets Manager y RDS.
   - `AppRunnerECRAccessRole`: Para que App Runner pueda leer de ECR.

## 🌐 Fase 2: Red Industrial (VPC)
No uses la VPC por defecto. Recrea la topología segura:
1. Crear una VPC con el bloque CIDR `10.0.0.0/16` (ver `vpc_topology_useast2.json`).
2. Crear 3 Subredes Privadas en diferentes AZs.
3. Crear un **Security Group** para los Interface Endpoints (Puerto 443).

## 📦 Fase 3: Persistencia y Secretos
1. **RDS:** Crear una instancia de Postgres (db.t3.micro es suficiente para dev).
2. **Secrets Manager:** Crear el secreto `interno-core/auth-service/prod` con las llaves del `.env` local.
3. **S3:** Crear el bucket de logs (ej: `internocore-logs-[random-suffix]`).

## 🚀 Fase 4: Despliegue Atómico
Usa el nuevo script universal:
```powershell
.\backend\scripts\deploy_to_new_aws_account.ps1 -AccountId "NUEVO_ID_CUENTA" -Region "us-east-2"
```

## 🔍 Notas de Arquitectura
- **OAC (Origin Access Control):** Usa `cloudfront_oac_config.json` para configurar el acceso seguro de CloudFront al bucket de Angular.
- **PrivateLink:** Asegúrate de que los VPC Endpoints para Secrets Manager y RDS estén activos en las subredes privadas.

---
**Estado:** Criogénico (Listo para Despliegue)
**Última Auditoría:** Mayo 2026
