# Guía de Despliegue en AWS App Runner (Low Cost)

Esta guía sustituye al despliegue en ECS + ALB para reducir costos en la fase de desarrollo de InternoCore.

## 1. Requisitos Previos

1. **GitHub Connection ARN**: Debes crear una conexión con GitHub en la consola de AWS App Runner (Service -> Settings -> Connections) y copiar el ARN.
2. **Secrets Manager**: El secreto `interno-core/auth-service/prod` debe existir con las credenciales de la DB.
3. **IAM Instance Role**: App Runner necesita un rol para leer de Secrets Manager.

## 2. Configuración de IAM (Acceso a Secretos)

Crea un rol llamado `InternoCore-AppRunner-Role` con la siguiente política de confianza:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "tasks.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Y asígnale permiso para leer el secreto:

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
      "Resource": "arn:aws:secretsmanager:us-east-2:584094645491:secret:interno-core/auth-service/*"
    }
  ]
}
```

## 3. Comando de Creación del Servicio

Sustituye `<GITHUB_CONNECTION_ARN>` y `<REPO_URL>` con tus valores:

```bash
aws apprunner create-service \
    --service-name interno-auth-service-dev \
    --source-configuration '{
        "CodeRepository": {
            "RepositoryUrl": "<REPO_URL>",
            "SourceCodeVersion": {
                "Type": "BRANCH",
                "Value": "main"
            },
            "CodeConfiguration": {
                "ConfigurationSource": "REPOSITORY"
            }
        },
        "AuthenticationConfiguration": {
            "ConnectionArn": "<GITHUB_CONNECTION_ARN>"
        }
    }' \
    --instance-configuration '{
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB",
        "InstanceRoleArn": "arn:aws:iam::584094645491:role/InternoCore-AppRunner-Role"
    }' \
    --health-check-configuration '{
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }'
```

## 4. Ventajas del Cambio
- **Costo Fijo:** $0.00 (vs ~$27.00 del ALB).
- **Costo Variable:** Solo pagas por la memoria RAM ($0.007/GB-hora) mientras el servicio esté "provisinado" pero sin tráfico.
- **SSL Automático:** AWS te da un dominio `.awsapprunner.com` con HTTPS válido.
