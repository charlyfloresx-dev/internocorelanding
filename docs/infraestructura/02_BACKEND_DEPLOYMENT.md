# 🚀 INTERNO CORE - ESPECIFICACIONES DE BACKEND Y DESPLIEGUE

> **Documento Unificado:** Consolida estrategias de despliegue, configuración de microservicios y recuperación ante desastres.
> **Fuentes:** AWS_Deployment_Strategy.md, DR_Manual_Auth_Microservice.md

## 1. Arquitectura de Despliegue AWS (Cloud)

### Aislamiento de Red (VPC)
El despliegue en nube prioriza la seguridad mediante aislamiento de red:
*   **Subredes Privadas:** Alojan los microservicios (ECS/EKS) y las bases de datos (RDS). Sin acceso directo a internet.
*   **Subredes Públicas:** Alojan únicamente el Application Load Balancer (ALB).
*   **VPC Endpoints:** Para acceso seguro a servicios AWS (Secrets Manager, S3, ECR) sin salir a la red pública.

### Security Groups (Firewall Virtual)
*   **ALB SG:** Inbound 80/443 (Internet) -> Outbound App Port (Auth SG).
*   **Auth Service SG:** Inbound App Port (Solo desde ALB SG) -> Outbound 5432 (RDS SG).
*   **RDS SG:** Inbound 5432 (Solo desde Auth Service SG).

---

## 2. Configuración del Microservicio (Auth-Service)

El microservicio de autenticación es el guardián de la identidad y debe configurarse con precisión.

### Variables de Entorno (Environment Variables)

| Variable | Descripción | Ejemplo / Valor |
| :--- | :--- | :--- |
| `ENV_MODE` | Entorno de ejecución | `aws`, `local`, `prod` |
| `DATABASE_URL` | Cadena de conexión DB | `postgresql+asyncpg://user:pass@host:5432/db` |
| `SECRET_KEY` | Firma de JWT (Crítico) | `[Cadena Aleatoria Segura]` |
| `AWS_REGION` | Región de despliegue | `us-east-2` |
| `AWS_SECRET_ID` | ID en Secrets Manager | `prod/auth-service` |
| `DB_POOL_SIZE` | Tamaño del pool SQL | `20` |
| `DB_MAX_OVERFLOW` | Conexiones extra | `10` |

### Gestión de Secretos
*   **AWS:** Uso de **AWS Secrets Manager**. El contenedor recibe `AWS_SECRET_ID` y recupera `DATABASE_URL` y `SECRET_KEY` al inicio.
*   **On-Premise:** Uso de archivo `.env` inyectado por Docker Compose.

---

## 3. Estrategia de Recuperación (Disaster Recovery)

En caso de pérdida total de infraestructura, seguir este procedimiento de "Tierra Quemada".

### Pasos Críticos (Resumen)
1.  **Recreación de RDS:**
    *   Crear instancia PostgreSQL (versión coincidente con producción).
    *   Asegurar Security Groups restrictivos (no acceso público).
2.  **Restauración de Secretos:**
    *   Crear entrada en AWS Secrets Manager con las nuevas credenciales de RDS.
3.  **Despliegue de Contenedores:**
    *   Lanzar tareas ECS con las nuevas variables de entorno apuntando al secreto.
4.  **Validación (Pruebas de Fuego):**
    *   Conectividad RDS (desde dentro de la VPC).
    *   Lectura de Secretos (Script de prueba).
    *   Health Check (`GET /health` -> 200 OK).

---

## 4. Roles IAM y Permisos

Principio de Mínimo Privilegio para los contenedores:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["secretsmanager:GetSecretValue"],
            "Resource": "arn:aws:secretsmanager:us-east-2:ACCOUNT:secret:prod/auth-service-*"
        }
    ]
}
```

---

## 5. Ciclo de Vida del Despliegue
1.  **Build:** `docker build -t interno-auth .`
2.  **Push:** `docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/interno-auth:latest`
3.  **Migrate:** Ejecutar contenedor efímero para `alembic upgrade head`.
4.  **Deploy:** Actualizar servicio ECS para usar la nueva imagen.