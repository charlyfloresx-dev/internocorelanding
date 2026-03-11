markdown
# InternoCore - Sistema de Autenticación Multitenant (Backend)

Este repositorio contiene el microservicio de autenticación de **InternoCore**, diseñado bajo los principios de **Clean Architecture** y **CQRS**, con soporte nativo para múltiples empresas (Multitenancy).

## 🚀 Estado del Proyecto: Listo para Despliegue (AWS)

El sistema ha sido validado exitosamente en entorno local y la imagen base ya reside en la nube de Amazon Web Services.

### 📊 Infraestructura de AWS (Región: us-east-2)

#### 1. Amazon ECR (Elastic Container Registry)
- **Repositorio**: `interno-backend-auth-service`
- **URI de la Imagen**: `584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-backend-auth-service:demo-v1`
- **Digest**: `sha256:613f69a51083ec378736edef15b44efcdac4f71835ac6e18c9fce87f17fd10e1`
- **Descripción**: Contenedor Docker optimizado que incluye el servicio FastAPI, la carpeta `common` (Domain/Models) y dependencias de seguridad como Bcrypt 4.0.1.

#### 2. Amazon S3 (Almacenamiento de Activos)
- **Static Bucket**: `nexosuite-static-files-3709` (Almacena logos de empresas y assets públicos).
- **Log/Backup Bucket**: `nexosuite-logs-and-backups-3709` (Persistencia de logs de auditoría).
- **Política**: Acceso de lectura pública habilitado para la entrega de contenido multitenant.

---

## 🛠️ Guía de Recuperación y Despliegue Rápido

Si necesitas reconstruir, resubir o migrar la imagen durante la demostración, utiliza estos comandos en orden:

### A. Autenticación y Login
Es indispensable renovar el token de acceso de AWS antes de cualquier operación de Docker:
```powershell
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 584094645491.dkr.ecr.us-east-2.amazonaws.com
```

### B. Re-etiquetado (Tagging)
Si realizas cambios locales y necesitas subirlos como una nueva versión:

```powershell
# Ejemplo para v2
docker tag interno-backend-auth-service:latest 584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-backend-auth-service:demo-v2
```

### C. Subida de Emergencia (Push)
```powershell
docker push 584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-backend-auth-service:demo-v2
```

### D. Poblar Base de Datos (Seed)
Si la base de datos RDS en AWS está vacía, ejecuta el script de fábrica desde el contenedor:

```powershell
docker exec -it auth-service-api python /app/seed_db.py
```

### 🔑 Flujo de Autenticación Multitenant (Validado)
El API sigue un proceso de dos pasos para garantizar la seguridad y la correcta asignación de roles:

1. **POST /api/v1/auth/login**:
    - Valida credenciales de usuario.
    - Devuelve un `selection_token`.
    - Entrega lista de empresas autorizadas con sus respectivos logos y roles.

2. **POST /api/v1/auth/select-company**:
    - Recibe el `selection_token` y el `company_id`.
    - Genera el JWT final de sesión con el contexto de la empresa elegida.

---
*Desarrollado para: Demo InternoCore 2026.*