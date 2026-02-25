# 🎫 Tickets Microservice - Interno Core

Microservicio de gestión de incidencias, solicitudes y tareas operativas para el ecosistema InternoCore/NexoSuite.

## Características
- **Arquitectura Limpia**: Separación de capas y cumplimiento de patrones CQRS.
- **Multitenancy**: Aislamiento estricto por `company_id`. Cada consulta y comando valida el contexto del tenant a través del JWT y el middleware de identidad.
- **Trazabilidad Total**: Historial de cambios y comentarios por ticket, heredando de `AuditBase` y `BaseEntity`.
- **Identidad Triple**: 
  - **UUID**: Identificador técnico único global.
  - **Secuencia**: Contador numérico por empresa para auditoría interna.
  - **Reference Code**: Código amigable al usuario (ej: `TKT-2026-0001`).

## Infraestructura y Despliegue
Este microservicio es compatible con despliegues en **AWS (EKS/ECS)** y **On-Premise**.

### Docker Build
Para construir la imagen desde la raíz del proyecto (`/backend`):
```bash
docker build -t tickets-service -f tickets_service/Dockerfile .
```

### Variables de Entorno Requeridas
| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DATABASE_URL` | URL de conexión SQL (MySQL/Postgres) | `mysql+aiomysql://user:pass@host:3306/db` |
| `SECRET_KEY` | Clave secreta para validación de JWT | `tu_super_secret_key` |
| `ALGORITHM` | Algoritmo de cifrado JWT | `HS256` |
| `ENV_MODE` | Modo de entorno | `local` / `production` |

## Endpoints Principales
...
- `POST /api/v1/tickets/`: Crear un nuevo ticket.
- `GET /api/v1/tickets/`: Listar tickets de la compañía actual.
- `GET /api/v1/tickets/{id}`: Detalle de un ticket.
- `PATCH /api/v1/tickets/{id}`: Actualizar estado, prioridad o asignación.
- `POST /api/v1/tickets/{id}/comments`: Agregar un comentario al hilo.

## Estructura de Datos
- **Status**: Nuevo, En revisión, Asignado, En progreso, En espera, Resuelto, Cerrado, Cancelado.
- **Priority**: Baja, Media, Alta, Crítica.
- **Type**: Soporte, Incidencia, Mejora, Queja, Tarea.
