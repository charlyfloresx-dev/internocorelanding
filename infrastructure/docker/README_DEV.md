# 🛠️ InternoCore: Microservices Development Guide

Esta guía documenta el estándar operativo para trabajar con la arquitectura de **Microservicios** de InternoCore en la carpeta `infrastructure/docker`. Este modo es el preferido para el desarrollo granular, escalabilidad en la nube (AWS) y cuando se requiere aislar servicios específicos.

---

## 📋 Estructura de Orquestación

- **`docker-compose.dev.yml`**: Stack principal de desarrollo con hot-reload habilitado para todos los servicios.
- **`docker-compose.kiosk.yml`**: Configuración especializada para el módulo de Kiosco (Fotografía y Eventos).
- **`docker-compose.prod.yml`**: Configuración base para despliegues escalables (sin volúmenes de desarrollo).
- **`docker-compose.workers.yml`**: Orquestador de procesadores asíncronos (Redis/Celery/Unified Workers).

---

## 🛠️ Procedimiento de Inicio (Modo Dev)

### 1. Limpieza de Entorno
Antes de iniciar un cambio de modo (de Monolito a Microservicios), asegúrate de limpiar los volúmenes para evitar conflictos de esquemas:

```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans
```

### 2. Arranque del Stack Core
Levanta los servicios esenciales necesarios para que el frontend funcione:

```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres-db redis auth-service master-data-service inventory-service
```

### 3. Siembra de Datos (Industrial Seed)
Una vez que los contenedores estén en estado `Healthy`, inyecta los datos maestros obligatorios:

```powershell
docker exec interno-auth-dev python scripts/unified_industrial_seed.py
```

---

## 📡 Topología y Puertos

| Servicio | Contenedor | Puerto (Host) | Uso |
| :--- | :--- | :--- | :--- |
| **Auth** | `interno-auth-dev` | `8001` | Identidad, Tenants y Roles |
| **Master Data** | `interno-master-data-dev` | `8003` | Catálogos y Productos |
| **Inventory** | `interno-inventory-dev` | `8006` | Kardex y Stock |
| **WMS** | `interno-wms-service-dev` | `8007` | Bodegas y Movimientos |
| **Postgres** | `interno-db-dev` | `5433` | Base de Datos persistente |
| **Redis** | `interno-redis-dev` | `6379` | Caché y Rate Limiting |

---

## 🕹️ Comandos de Mantenimiento

**Ver logs de un servicio específico:**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f auth-service
```

**Reconstruir un solo servicio (tras cambios en el Dockerfile):**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build inventory-service
```

---

> [!NOTE]
> Recuerda que el **Contexto de Build** siempre debe ser la raíz del backend (`../../backend`). Todos los archivos de esta carpeta ya están pre-configurados para manejar esta profundidad de directorio.
