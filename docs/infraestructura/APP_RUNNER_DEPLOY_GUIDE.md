# Guía de Despliegue en AWS App Runner (Low Cost)

Esta guía sustituye al despliegue en ECS + ALB para reducir costos en la fase de desarrollo de InternoCore.

## 1. Requisitos Previos

1. **Amazon ECR**: Una imagen de Docker válida debe estar subida a ECR (ej. `interno-core/auth-service:latest`).
2. **Secrets Manager**: El secreto `interno-core/auth-service/prod` debe existir con las credenciales de la DB y estar en la misma región (`us-east-2`).

## 2. Configuración de Despliegue (Vía AWS Console)

Dado que usar el AWS CLI requiere crear a mano roles de confianza bastante complejos (`build.apprunner.amazonaws.com` y `tasks.apprunner.amazonaws.com`), la **ruta más rápida y libre de errores (FinOps Approved)** es usar la Consola Web de AWS:

1. Ve a **AWS App Runner** -> **Create an App Runner service**.
2. **Source**: Selecciona `Amazon ECR`.
3. **Container image URI**: Localiza y selecciona tu imagen (ej. `interno-core/auth-service`).
4. **ECR access role**: Deja la opción en "Create new service role" (AWS automatizará el acceso ECR de manera transparente).
5. **Deployment settings**: "Manual" o "Automatic" (si quieres CI/CD con cada push a ECR).

## 3. Configuración de Entorno y Variables (Vital)

En la pantalla de *Configure service*, asegúrate de establecer estos parámetros para no superar el presupuesto de $5.00 a $20.00:

*   **Port**: `8000` (Debe hacer match con el `EXPOSE` del Dockerfile y Uvicorn).
*   **Virtual CPU & Memory**: `0.25 vCPU / 0.5 GB` (Lo mínimo indispensable).
*   **Environment Variables**:
    *   `CORE_ENV_MODE` = `aws`
    *   `CORE_AWS_SECRET_ID` = `interno-core/auth-service/prod`
*   **Security (Instance Role)**: Selecciona un rol IAM que tenga permisos sobre Secrets Manager (ej. `InternoCore-AppRunner-Role` o tu rol de ejecución de ECS) para que el servicio pueda extraer los Connection Strings.

Una vez creado, AWS te entregará el `Default domain` (con SSL/TLS automático) que puedes inyectar directamente en el Frontend o `environment.prod.ts`.

## 4. Ventajas del Cambio
- **Costo Fijo:** $0.00 (vs ~$27.00 del ALB).
- **Costo Variable:** Solo pagas por la memoria RAM ($0.007/GB-hora) mientras el servicio esté "provisinado" pero sin tráfico.
- **SSL Automático:** AWS te da un dominio `.awsapprunner.com` con HTTPS válido.

## 5. Configuración Crítica de Red (VPC Networking)

Si el servicio se despliega en una **subred privada** usando un *VPC Connector*, es obligatorio configurar **VPC Interface Endpoints** (PrivateLink). Sin esto, el contenedor no podrá resolver el API de Secrets Manager y fallará el Health Check.

**Endpoints Requeridos:**
- `com.amazonaws.us-east-2.secretsmanager`
- `com.amazonaws.us-east-2.rds` (Interface API)

**Security Group del Endpoint:** Debe permitir tráfico entrante en el puerto `443` desde el Security Group del servicio App Runner.

> [!CAUTION]
> No intentes desplegar sin estos endpoints si usas el modo `CORE_ENV_MODE=aws` en subredes privadas, o el servicio entrará en un ciclo de `CREATE_FAILED`.
