# Estrategia de Despliegue AWS para NexoSuite Auth Microservice

Este documento detalla la estrategia recomendada para el despliegue del microservicio de autenticación de NexoSuite en AWS, haciendo énfasis en el aislamiento de red y la seguridad.

## 1. Aislamiento de Red y Arquitectura VPC

El microservicio de Auth y la base de datos RDS residirán dentro de una Virtual Private Cloud (VPC) de AWS, garantizando un aislamiento completo del internet público, excepto por los puntos de acceso controlados.

*   **VPC**: Se utilizará una VPC dedicada o subredes privadas específicas dentro de una VPC existente para los recursos de producción.
*   **Subredes Privadas**: El microservicio de Auth (ej., contenedores ECS/EKS) se desplegará en **subredes privadas**. Estas subredes no tienen una ruta directa a Internet Gateway.
*   **AWS RDS**: La instancia de PostgreSQL de RDS también se desplegará en **subredes privadas** (idealmente en un DB Subnet Group que abarque múltiples Zonas de Disponibilidad para alta disponibilidad).

## 2. Puntos de Acceso Controlados

### 2.1 Balanceador de Carga de Aplicación (ALB)
*   Un Application Load Balancer (ALB) se desplegará en **subredes públicas** para recibir el tráfico de internet (HTTP/HTTPS).
*   El ALB redirigirá el tráfico al microservicio de Auth en las subredes privadas. Esto se logra configurando los Security Groups adecuadamente para permitir el tráfico desde el ALB al microservicio.

### 2.2 Conectividad a AWS Secrets Manager (VPC Endpoint)
*   Para que el microservicio pueda acceder a AWS Secrets Manager sin salir de la red AWS ni atravesar Internet Gateways, se configurará un **VPC Endpoint para el servicio `secretsmanager`**.
*   Este Endpoint tipo `Interface` mantendrá todo el tráfico de secretos dentro de la VPC, mejorando la seguridad y reduciendo la latencia.
*   El Security Group del VPC Endpoint debe permitir el tráfico de entrada en el puerto 443 desde el Security Group del microservicio de Auth.

## 3. Configuración de Security Groups

La clave para el aislamiento y la comunicación segura reside en la configuración granular de los Security Groups.

*   **Security Group del Microservicio de Auth (`auth-service-sg`)**:
    *   **Inbound**: Permitir tráfico en el puerto de la aplicación (ej., 8000) **SOLO** desde el Security Group del ALB.
    *   **Outbound**:
        *   Permitir tráfico en el puerto 5432 (PostgreSQL) **SOLO** hacia el Security Group de la instancia RDS.
        *   Permitir tráfico en el puerto 443 (HTTPS) **SOLO** hacia el Security Group del VPC Endpoint de Secrets Manager.
        *   Puede requerir outbound a un NAT Gateway para acceso a internet para actualizaciones de paquetes o logs si el contenedor lo requiere, pero se recomienda minimizar este acceso.

*   **Security Group de RDS (`rds-sg`)**:
    *   **Inbound**: Permitir tráfico en el puerto 5432 (PostgreSQL) **SOLO** desde el Security Group del microservicio de Auth (`auth-service-sg`).
    *   **Outbound**: Típicamente no requiere reglas de outbound específicas, o muy restringidas.

*   **Security Group del ALB (`alb-sg`)**:
    *   **Inbound**: Permitir tráfico en los puertos 80/443 desde `0.0.0.0/0` (internet) o IPs específicas si el acceso está restringido.
    *   **Outbound**: Permitir tráfico en el puerto de la aplicación (ej., 8000) **SOLO** hacia el Security Group del microservicio de Auth.

## 4. Roles de IAM (Identity and Access Management)

Se asignarán roles de IAM a los contenedores o tareas de ECS/EKS para gestionar sus permisos de acceso a los servicios de AWS.

*   **Rol IAM para el Microservicio de Auth**:
    *   Asociado a la Task Definition de ECS o al Service Account de EKS.
    *   **Permisos mínimos**:
        ```json
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret"
                    ],
                    "Resource": "arn:aws:secretsmanager:<region>:<account-id>:secret:nexosuite/auth-service/db-XXXXXX"
                }
            ]
        }
        ```
    *   Reemplazar `<region>`, `<account-id>` y `XXXXXX` con los valores correctos.
    *   Este rol asegura que el microservicio solo puede leer el secreto específico que necesita.

## 5. Configuración del Contenedor (Variables de Entorno)

Al desplegar el contenedor del microservicio de Auth, se inyectarán las siguientes variables de entorno:

*   **`ENV_MODE`**: Se establecerá a `aws` para activar la lógica de carga de secretos desde AWS Secrets Manager.
*   **`AWS_REGION`**: Se establecerá a `us-east-2` (o la región de despliegue).
*   **`AWS_SECRET_ID`**: Se establecerá a `nexosuite/auth-service/db` (el ARN completo del secreto si es posible, o el nombre si la política IAM ya restringe por nombre).

## 6. Proceso de Despliegue (Visión General)

1.  **Construir y Etiquetar Imagen Docker**: `docker build -t interno-backend-auth-service:latest .` (o usar ECR).
2.  **Push a Registro de Contenedores**: Push la imagen a Amazon ECR (Elastic Container Registry) u otro registro privado.
3.  **Definir Tarea/Pod**: Crear una definición de tarea de ECS o Pod de Kubernetes con la imagen del contenedor, variables de entorno (`ENV_MODE`, `AWS_REGION`, `AWS_SECRET_ID`), y el rol IAM apropiado.
4.  **Servicio/Deployment**: Crear un servicio de ECS o Deployment de Kubernetes para gestionar el despliegue y escalado de las tareas/pods.
5.  **Configurar ALB**: Registrar el servicio o los pods como targets del ALB.
6.  **Migraciones de DB**: Ejecutar migraciones de base de datos (usando Alembic) como parte del pipeline de CI/CD o manualmente antes del despliegue completo, asegurando que la base de datos RDS tenga el esquema más reciente.

Esta estrategia proporciona un marco seguro y escalable para el despliegue del microservicio de autenticación de NexoSuite en AWS.
