# Especificaciones de Auditoría: Master Data Service

**Fecha:** 2026-02-14
**Versión:** 2.0
**Alcance:** Implementación de Trazabilidad (Quién, Cuándo, Qué)

## 1. Requisitos del Modelo (Auditoría Básica)

Todos los modelos principales (`Product`, `UM`, etc.) deben heredar de `AuditBase` (definido en `common`) para garantizar consistencia entre entornos On-Premise y AWS.

### Implementación de Referencia
```python
# common/models/audit_base.py
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuditBase(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True) # ID del usuario o email
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    updated_by = Column(String(100), nullable=True)
```

## 2. Especificaciones para la API (Contexto de Usuario)
Para poblar automáticamente `created_by` y `updated_by`, el backend debe extraer el contexto del usuario en cada petición.

- **Header:** Se requiere `X-User-Id` o el token JWT en todas las peticiones de escritura (`POST`, `PUT`, `PATCH`).
- **Inyección:** Utilizar `Depends` en FastAPI para inyectar el usuario en los Comandos (CQRS).

## 3. Log de Auditoría (Cambios de Datos)
Se debe implementar un registro detallado de cambios ("El precio pasó de 10 a 15") mediante una tabla de logs o servicio externo.

### Esquema de Tabla: `audit_logs`
| Campo | Tipo | Descripción |
|---|---|---|
| `id` | UUID/Int | Identificador único del evento |
| `table_name` | String | Nombre de la entidad afectada |
| `record_id` | String | ID del registro modificado |
| `action` | String | `INSERT`, `UPDATE`, `DELETE` |
| `old_value` | JSON | Estado anterior del registro |
| `new_value` | JSON | Nuevo estado del registro |
| `user_id` | String | Usuario responsable |
| `timestamp` | DateTime | Momento exacto del cambio |

**Regla CQRS:** Los `CommandHandlers` son responsables de registrar el cambio antes de confirmar la transacción.

## 4. Configuración del Entorno (Híbrido)
La configuración debe ser agnóstica a la infraestructura (AWS vs On-Premise).

- **Precios:** Deben auditarse utilizando el Value Object `Money`, siempre en el contexto de `company_id` y `warehouse_id`.
- **Conexión:** La `DATABASE_URL` debe ser inyectada exclusivamente vía variables de entorno.

## 7. Especificaciones de Autorreparación (Self-Healing)
**Objetivo:** Garantizar que el servicio sea construible y el seed ejecutable eliminando bloqueos de importación circular y archivos faltantes.

### 1. Acción: Limpieza de Inicializadores (Anti-Bloqueo)
El agente DEBE asegurar que los siguientes archivos estén **TOTALMENTE VACÍOS**. Si contienen código, el agente debe borrarlo para evitar `ModuleNotFoundError` durante el arranque de Uvicorn:
1. `backend/master_data_service/__init__.py`
2. `backend/master_data_service/app/__init__.py`
3. `backend/master_data_service/app/db/__init__.py`

### 2. Acción: Creación de Scripts de Infraestructura
Si el archivo `backend/master_data_service/init_db.py` no existe, el agente **DEBE CREARLO** con el contenido especificado en la sección de implementación para permitir la sincronización de tablas.

### 3. Acción: Verificación de Integridad del Dockerfile
El agente debe validar que el `Dockerfile` en `master_data_service` tenga las instrucciones `COPY` alineadas con los archivos creados:
```dockerfile
COPY master_data_service/init_db.py /app/init_db.py
COPY master_data_service/seed_master.py /app/seed_master.py
```

### 4. Criterio de Éxito
El agente considerará la tarea completada solo cuando:
1. El comando `docker compose build master-data-service` termine sin errores de "file not found".
2. El comando `docker compose exec master-data-service python init_db.py` devuelva el mensaje de éxito:
   > "✅ Base de datos sincronizada."