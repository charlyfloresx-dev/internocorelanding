# Manual de Recuperación ante Desastres: NexoSuite Auth Microservice

## 1. Arquitectura del Microservicio de Auth

El microservicio de autenticación de NexoSuite se basa en una arquitectura de microservicios robusta y escalable, utilizando las siguientes tecnologías y servicios en la nube:

*   **FastAPI**: Framework web Python de alto rendimiento para la construcción de APIs.
*   **Docker**: Contenedores para empaquetar la aplicación y sus dependencias, asegurando un entorno consistente.
*   **AWS RDS (PostgreSQL)**: Base de datos relacional gestionada por AWS, utilizada para persistir los datos de usuarios, empresas, roles y permisos.
*   **AWS Secrets Manager**: Servicio para almacenar y gestionar de forma segura los secretos de la aplicación (credenciales de base de datos, claves de JWT, etc.).

## 2. Variables de Entorno Clave

La configuración del micro servicio se gestiona a través de variables de entorno, que pueden ser cargadas localmente (`.env`) o inyectadas por el entorno de despliegue (como ECS, Kubernetes o directamente desde AWS Secrets Manager).

*   **`ENV_MODE`**: Define el entorno de ejecución (`local`, `dev`, `prod`, `aws`). Este valor puede influir en el comportamiento de la aplicación (ej., modo debug, carga de secretos).
*   **`DATABASE_URL`**: URL de conexión a la base de datos PostgreSQL (ej., `postgresql+asyncpg://user:password@host:port/dbname`).
*   **`SECRET_KEY`**: Clave secreta utilizada para firmar los JSON Web Tokens (JWT). **CRÍTICA para la seguridad**.
*   **`AWS_REGION`**: Región de AWS donde se despliegan los recursos (ej., `us-east-1`). Utilizada por `boto3` para interactuar con AWS Secrets Manager.
*   **`AWS_SECRET_ID`**: ID o ARN del secreto en AWS Secrets Manager que contiene las variables críticas para el micro servicio (ej., `prod/auth-service`).

## 3. Pasos de Reconstrucción de Infraestructura (AWS CLI)

En caso de un desastre que requiera la recreación completa de la infraestructura de base de datos y secretos, siga estos pasos utilizando la AWS CLI. Asegúrese de tener la AWS CLI configurada con las credenciales adecuadas y los permisos necesarios.

### 3.1 Recreación de AWS RDS (PostgreSQL)

Este proceso asume que no existe un snapshot de recuperación y que se está creando una nueva instancia desde cero.

1.  **Crear un Security Group para RDS**: Este SG debe permitir el tráfico de entrada en el puerto 5432 desde las IPs de las instancias de aplicación (o el SG de las instancias de aplicación).
    ```bash
    aws ec2 create-security-group \
        --group-name NexoSuiteAuthRDS-SG \
        --description "Security group for NexoSuite Auth RDS instance" \
        --vpc-id <your-vpc-id>

    # (Opcional) Añadir regla de entrada para la IP de tu máquina de desarrollo (solo para pruebas)
    aws ec2 authorize-security-group-ingress \
        --group-id <sg-id-of-NexoSuiteAuthRDS-SG> \
        --protocol tcp \
        --port 5432 \
        --cidr <your-ip-address>/32

    # (Obligatorio) Añadir regla de entrada desde el Security Group de las instancias de aplicación
    aws ec2 authorize-security-group-ingress \
        --group-id <sg-id-of-NexoSuiteAuthRDS-SG> \
        --protocol tcp \
        --port 5432 \
        --source-group <sg-id-of-your-app-instances-sg>
    ```

2.  **Crear la instancia de RDS PostgreSQL**:
    ```bash
    aws rds create-db-instance \
        --db-instance-identifier nexosuite-auth-db \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 15.4 \
        --allocated-storage 20 \
        --master-username nexouser \
        --master-user-password <your-strong-password> \
        --vpc-security-group-ids <sg-id-of-NexoSuiteAuthRDS-SG> \
        --db-subnet-group-name <your-db-subnet-group> \
        --multi-az | true \
        --publicly-accessible | false \
        --backup-retention-period 7 \
        --preferred-backup-window "03:00-05:00" \
        --preferred-maintenance-window "sun:06:00-sun:07:00" \
        --tags Key=Project,Value=NexoSuite Key=Service,Value=Auth
    ```
    *   **`<your-strong-password>`**: Reemplazar con una contraseña segura.
    *   **`<your-vpc-id>`**: ID de tu VPC.
    *   **`<sg-id-of-NexoSuiteAuthRDS-SG>`**: ID del Security Group creado en el paso anterior.
    *   **`<your-ip-address>/32`**: Tu dirección IP pública para acceso temporal.
    *   **`<sg-id-of-your-app-instances-sg>`**: ID del Security Group de las instancias donde correrá tu aplicación.
    *   **`<your-db-subnet-group>`**: Un grupo de subredes de DB existente en tu VPC.

3.  **Obtener el Endpoint de la DB**: Una vez creada (puede tardar varios minutos), obtén el endpoint.
    ```bash
    aws rds describe-db-instances \
        --db-instance-identifier nexosuite-auth-db \
        --query "DBInstances[0].Endpoint.Address" \
        --output text
    ```

### 3.2 Recreación de AWS Secrets Manager

Este paso recrea el secreto que contiene las configuraciones críticas.

1.  **Crear el secreto en AWS Secrets Manager**:
    ```bash
    # Primero, crea el string JSON con tus secretos.
    # Reemplaza <db-endpoint-from-rds>, <your-strong-password> y <your-secret-key>
    SECRET_STRING='{"DATABASE_URL": "postgresql+asyncpg://nexouser:<your-strong-password>@<db-endpoint-from-rds>:5432/postgres", "SECRET_KEY": "<your-secret-key>"}'

    aws secretsmanager create-secret \
        --name prod/auth-service \
        --description "Critical secrets for NexoSuite Auth microservice" \
        --secret-string "$SECRET_STRING" \
        --tags Key=Project,Value=NexoSuite Key=Service,Value=Auth
    ```
    *   **`<db-endpoint-from-rds>`**: Reemplazar con el endpoint obtenido del paso 3.1.3.
    *   **`<your-strong-password>`**: La misma contraseña utilizada para RDS.
    *   **`<your-secret-key>`**: Una clave secreta fuerte y única para JWT.

## 4. Pruebas de Conectividad y Acceso

Una vez recreados los recursos, es crucial verificar la conectividad.

### 4.1 Verificación de Conectividad a RDS (Puerto 5432)

Asegúrate de que el Security Group de tu RDS permite el tráfico desde la máquina donde ejecutas estas pruebas.

*   **Desde Windows (PowerShell)**:
    ```powershell
    Test-NetConnection -ComputerName <db-endpoint-from-rds> -Port 5432
    # Deberías ver TcpTestSucceeded : True
    ```
*   **Desde Linux/macOS (Telnet)**:
    ```bash
    telnet <db-endpoint-from-rds> 5432
    # Si la conexión es exitosa, verás una pantalla en blanco o un mensaje de conexión.
    # Presiona Ctrl+] y luego 'quit' para salir.
    ```

### 4.2 Verificación de Lectura de Secretos (Python Script)

Crea un archivo Python (ej., `test_secrets.py`) y ejecútalo para verificar que el micro servicio puede leer el secreto.

```python
import boto3
import json
import os

# Configura tus variables de entorno o reemplaza directamente
# os.environ["AWS_REGION"] = "us-east-1"
# os.environ["AWS_SECRET_ID"] = "prod/auth-service"

secret_name = os.getenv("AWS_SECRET_ID", "prod/auth-service")
region_name = os.getenv("AWS_REGION", "us-east-1") # Asegúrate de que esta sea la región correcta

print(f"Intentando leer secreto '{secret_name}' en la región '{region_name}'...")

try:
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        secret_dict = json.loads(secret)
        print("✅ Secreto leído exitosamente. Contenido (parcial, sin valores):")
        for k, v in secret_dict.items():
            if k in ["DATABASE_URL", "SECRET_KEY"]:
                print(f"   - {k}: {'*' * (len(v) - 5)}{v[-5:]}") # Muestra solo los últimos 5 caracteres
            else:
                print(f"   - {k}: {v}")
    else:
        print("⚠️ El secreto no contiene 'SecretString'. Puede ser binario o nulo.")
        
except Exception as e:
    print(f"❌ Error al leer el secreto: {e}")
    print("Asegúrate de que tus credenciales de AWS CLI estén configuradas correctamente y que el Secret ID y la Región sean correctos.")

```
Guarda este script como `test_secrets.py` y ejecútalo con `python test_secrets.py`.

## 5. Políticas de Seguridad Post-Recuperación

Una vez que la conectividad a la base de datos y la lectura de secretos han sido validadas, es **CRÍTICO** revisar y ajustar los Security Groups de AWS.

*   **Cierre de Acceso Público**: Si se abrió el puerto 5432 de RDS a IPs públicas (ej., tu IP de desarrollo) para realizar pruebas, **DEBE** cerrarse inmediatamente. El acceso a RDS debe estar restringido **únicamente** a los Security Groups de las instancias de aplicación (ECS Tasks, EC2 instances, etc.) que necesiten conectar.
*   **Principio de Mínimo Privilegio**: Asegúrese de que los Security Groups y las políticas de IAM apliquen el principio de mínimo privilegio.

```bash
# Ejemplo: Eliminar regla de entrada pública para 5432
aws ec2 revoke-security-group-ingress \
    --group-id <sg-id-of-NexoSuiteAuthRDS-SG> \
    --protocol tcp \
    --port 5432 \
    --cidr <your-ip-address>/32
```
La seguridad de la infraestructura es primordial para proteger los datos sensibles del micro servicio de autenticación.
