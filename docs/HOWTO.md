# HOWTO.md - NexoSuite Auth Microservice Disaster Recovery Guide

Este documento detalla los procedimientos esenciales para la recuperación y validación del microservicio de autenticación de NexoSuite en un escenario de desastre, asumiendo la pérdida total de la configuración de infraestructura en AWS.

## 1. Arquitectura del Microservicio de Autenticación NexoSuite

El microservicio de autenticación de NexoSuite es una aplicación **FastAPI** desarrollada en Python, diseñada para ejecutarse eficientemente dentro de **contenedores Docker**.

*   **Entorno de Desarrollo (`ENV_MODE=local`)**: Utiliza una base de datos PostgreSQL local, generalmente desplegada también en Docker, para facilitar un ciclo de desarrollo ágil y aislado.
*   **Entorno de Producción (`ENV_MODE=aws`)**: Se integra con servicios gestionados de AWS para alta disponibilidad y escalabilidad:
    *   **Amazon RDS (PostgreSQL)**: Para la persistencia de datos críticos como usuarios, roles, empresas y permisos.
    *   **AWS Secrets Manager**: Para el almacenamiento seguro de credenciales de base de datos y claves secretas de la aplicación.

## 2. Configuración de AWS (Pasos de Recuperación)

Los siguientes pasos guían la recreación de los recursos AWS esenciales utilizando la AWS CLI. Asegúrese de tener la AWS CLI configurada y autenticada con los permisos necesarios.

### 2.1 Recuperación de AWS RDS (PostgreSQL)

**Detalles de la Instancia de RDS:**

| Parámetro       | Valor                                     |
| :-------------- | :---------------------------------------- |
| **Nombre**      | `nexosuite-auth-db`                       |
| **Región**      | `us-east-2` (Ohio)                        |
| **Endpoint**    | `nexosuite-auth-db.c920i68eetxr.us-east-2.rds.amazonaws.com` |
| **Usuario**     | `nexoadmin`                               |
| **Contraseña**  | `NexoPassword2026!`                       |
| **Puerto**      | `5432`                                    |
| **Engine**      | `postgres`                                |
| **Version**     | `15.4` (recomendada)                      |
| **Clase DB**    | `db.t3.micro` (mínimo para dev/test)      |
| **Almacenamiento** | `20 GB` (mínimo)                       |

**Comando Crítico para `aws rds create-db-instance`:**

```bash
aws rds create-db-instance \
    --db-instance-identifier nexosuite-auth-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --allocated-storage 20 \
    --master-username nexoadmin \
    --master-user-password NexoPassword2026! \
    --vpc-security-group-ids sg-XXXXXXXXXXXXXXX \
    --db-subnet-group-name nexosuite-db-subnet-group \
    --region us-east-2 \
    --tags Key=Project,Value=NexoSuite Key=Service,Value=Auth
```
**Nota**: Reemplace `sg-XXXXXXXXXXXXXXX` con el ID de un Security Group adecuado para su VPC y `nexosuite-db-subnet-group` con un DB Subnet Group preexistente.

### 2.2 Configuración de Seguridad para RDS

Para permitir la conectividad inicial de prueba (y con precaución en un entorno real), se puede abrir el puerto 5432.

**¡ADVERTENCIA!** Abrir el puerto 5432 a `0.0.0.0/0` es una práctica **ALTAMENTE INSEGURA** y solo debe hacerse para pruebas de emergencia y por un tiempo extremadamente limitado. **CIERRE ESTE ACCESO INMEDIATAMENTE DESPUÉS DE LAS PRUEBAS.**

**Comando Crítico para `aws ec2 authorize-security-group-ingress`:**

```bash
aws ec2 authorize-security-group-ingress \
    --group-id sg-XXXXXXXXXXXXXXX \
    --protocol tcp \
    --port 5432 \
    --cidr 0.0.0.0/0 \
    --region us-east-2
```
**Nota**: Reemplace `sg-XXXXXXXXXXXXXXX` con el ID del Security Group asociado a su instancia de `nexosuite-auth-db`.

### 2.3 Recuperación de AWS Secrets Manager

**Detalles del Secreto:**

| Parámetro       | Valor                       |
| :-------------- | :-------------------------- |
| **Nombre**      | `nexosuite/config-3709`     |
| **Región**      | `us-east-2`                 |

**Comando Crítico para `aws secretsmanager put-secret-value`:**

Este comando cargará los valores esenciales para que el microservicio se conecte a la base de datos y funcione correctamente.

```bash
aws secretsmanager put-secret-value \
    --secret-id nexosuite/config-3709 \
    --secret-string '{ \
        "DATABASE_URL": "postgresql+asyncpg://nexoadmin:NexoPassword2026!@nexosuite-auth-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432/postgres", \
        "SECRET_KEY": "your-super-secret-jwt-key-for-nexo-auth-prod-2026", \
        "AWS_REGION": "us-east-2", \
        "AWS_SECRET_ID": "nexosuite/config-3709" \
    }' \
    --region us-east-2
```
**Nota**: Reemplace `"your-super-secret-jwt-key-for-nexo-auth-prod-2026"` con una clave secreta fuerte y única para su entorno de producción.

## 3. Checklist de Pruebas de Fuego

Una vez que los recursos de AWS han sido recreados y configurados, realice las siguientes "Pruebas de Fuego" para validar la operatividad del sistema.

*   **PF1: Conexión externa vía DBeaver exitosa.**
    *   Intente conectar a `nexosuite-auth-db.c920i68eetxr.us-east-2.rds.amazonaws.com:5432` con `nexoadmin` y `NexoPassword2026!` desde una herramienta como DBeaver o pgAdmin. Confirme que puede ver las tablas creadas por Alembic (ej., `users`, `companies`).
*   **PF2: Lectura de secretos vía AWS CLI exitosa.**
    *   Ejecute el siguiente comando para verificar que el secreto puede ser leído:
        ```bash
        aws secretsmanager get-secret-value \
            --secret-id nexosuite/config-3709 \
            --query SecretString \
            --output text \
            --region us-east-2
        ```
    *   Verifique que el JSON de salida contiene `DATABASE_URL` y `SECRET_KEY`.
*   **PF3: Health check de la API en `/` respondiendo 200 OK.**
    *   Despliegue el microservicio de Auth (Docker Compose o en su entorno de ejecución).
    *   Acceda al endpoint raíz (`GET /`) o un endpoint de salud (`GET /health` si existe) y confirme una respuesta `200 OK`.
        ```bash
        curl -v http://localhost:8000/
        ```
*   **PF4: Persistencia en la nube (Registro de usuario reflejado en el RDS de Ohio).**
    *   Utilice el endpoint de registro del microservicio (ej., `POST /auth/register-company`) para crear un nuevo usuario y empresa.
    *   Conéctese a la base de datos RDS con DBeaver y verifique que el nuevo usuario y empresa aparecen en las tablas `users` y `companies` respectivamente.

## 4. Plan de Contingencia

Si alguna de las Pruebas de Fuego falla, considere los siguientes puntos:

*   **Revisar IP en Security Groups**:
    *   Para problemas de conectividad a RDS (`PF1` fallido), verifique que el Security Group de RDS (`sg-XXXXXXXXXXXXXXX`) permite el tráfico entrante en el puerto 5432 desde la IP pública de su máquina de pruebas o desde el Security Group de sus instancias de aplicación.
    *   Si usó `0.0.0.0/0` temporalmente, asegúrese de que la regla esté activa.
*   **Verificar `ENV_MODE`**:
    *   Asegúrese de que el microservicio está configurado para `ENV_MODE=aws` si está intentando conectar a los recursos de AWS. Si está en `local`, intentará usar la configuración local.
    *   Confirme que las variables de entorno `AWS_REGION` y `AWS_SECRET_ID` están correctamente configuradas en el entorno de ejecución del microservicio.
    *   Verifique los logs del microservicio para mensajes de error relacionados con la conexión a la base de datos o la lectura de secretos.
