# 🚀 Guía de Resurrección: Despliegue en Nueva Cuenta AWS

Este documento contiene la "Receta Maestra" para reconstruir el ecosistema de **InternoCore** en una cuenta de AWS completamente nueva, preservando la arquitectura industrial y el **Muro de Hierro**.

## 📋 Requisitos Previos
1. **Nueva Cuenta de AWS** activa y acceso root inicial.
2. **AWS CLI** configurado con un nuevo perfil (`aws configure --profile internocore-new`).
3. **Docker Desktop** instalado y funcionando.
4. Las "Recetas" JSON en `docs/infrastructure/recipes/` deben estar intactas.

## 🛠️ Fase 1: Cimentación (IAM & KMS)
Antes de levantar servicios, debemos reconstruir el modelo de confianza.
1. **KMS:** Crear una llave maestra (CMK) para cifrar los secretos de Secrets Manager y las bases de datos RDS.
2. **IAM Roles:** Usar `docs/infrastructure/recipes/ecs-trust-policy.json` para crear los roles:
   - `InternoCore-ExecutionRole`: Para que ECS/AppRunner pueda descargar imágenes y logs.
   - `InternoCore-TaskRole`: Para acceso en tiempo de ejecución a S3 y Secrets Manager.

## 🌐 Fase 2: El Búnker de Red (VPC & Endpoints)
No uses la VPC por defecto. Recrea la topología aislada:
1. **VPC:** Crear una VPC `10.0.0.0/16` siguiendo `vpc_topology_useast2.json`.
2. **Subnets:** Dividir en 3 públicas (para CloudFront/ALB) y 3 privadas (para servicios y DB).
3. **Interface Endpoints:** Crear VPC Endpoints para `secretsmanager`, `ecr.api`, `ecr.dkr` y `s3` en las subredes privadas. Esto garantiza que el tráfico nunca salga a internet.

## 📦 Fase 3: Persistencia de Datos
1. **Secrets Manager:** Crear el secreto `interno-core/auth-service/prod`. Importar las llaves desde tu `vault/` local.
2. **RDS:** Desplegar una instancia Aurora Postgres en las subredes privadas. Usar el Security Group `rds-sg` que solo permita tráfico desde el `app-sg`.

## 🚀 Fase 4: Despliegue de Servicios (App Runner)
1. **ECR:** Crear un repositorio para cada servicio (auth, inventory, etc.).
2. **Script de Orquestación:** Ejecutar el script maestro:
   ```powershell
   .\docs\infrastructure\guides\deploy_to_new_aws_account.ps1 -AccountId "NUEVO_ID_CUENTA" -Region "us-east-2"
   ```
3. **CloudFront OAC:** Configurar la distribución usando `cloudfront-config-oac.json`. Asegurarse de que el bucket S3 solo acepte tráfico desde el `Origin Access Control`.

## ✅ Verificación de Vida
1. Realizar el **Handshake T1** contra el nuevo endpoint de App Runner.
2. Verificar en CloudWatch que no hay errores de conexión a la base de datos.
3. Ejecutar `python backend/scripts/generate_code_graph.py` para asegurar que la nueva red cumple los invariantes.

---
**Estado de Disponibilidad:** 🧊 Criogénico / ⚡ Listo para Activación Inmediata.
