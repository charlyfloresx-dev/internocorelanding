# 🚀 InternoCore: On-Premise Deployment Guide

Esta guía documenta el procedimiento estándar operativo (SOP) para levantar la arquitectura del **Monolito Unificado InternoCore** en entornos On-Premise (Servidores Locales, Edge Computing en Almacenes, o Ambientes de Desarrollo).

---

## 📋 Prerrequisitos

- Docker y Docker Compose (V2+) instalados en el servidor.
- Git Bash, WSL (Windows Subsystem for Linux) o cualquier terminal compatible con Bash.
- Archivo `.env` configurado en la raíz del proyecto (`c:\API\interno\.env`).

---

## 🛠️ Procedimiento de Arranque (Día Zero)

El arranque del ecosistema consta de tres pasos lógicos y secuenciales. Se debe ejecutar cada paso desde este directorio (`infrastructure/onprem`).

### Paso 1: Inicialización de la Red y Bases de Datos
Arranca el motor de Postgres, la caché de Redis y el contenedor principal del Monolito.

```bash
./init_db.sh
```
> **Nota:** Este script esperará pasivamente mediante un *healthcheck* de `pg_isready` hasta que la base de datos esté al 100% receptiva antes de liberar la terminal. No lo interrumpas.

### Paso 2: Ejecución de Migraciones (Alembic)
El monolito unificado sigue respetando la segregación física de los esquemas. Ejecuta el script de migración para inyectar todas las tablas en la base de datos recién creada:

```bash
./migrate.sh
```
> **Qué hace:** Este script entra al contenedor del monolito (`interno-monolith`) e itera sobre todos los módulos (`auth_service`, `inventory_service`, `wms_service`, etc.), forzando un `alembic upgrade head` en cada uno.

### Paso 3: Sembrado de Datos Industriales (Opcional pero Recomendado)
Si estás levantando el ecosistema desde cero, necesitarás datos maestros (Usuarios Administradores, Unidades de Medida, Roles base). Ejecuta el seed industrial unificado:

```bash
docker-compose exec interno-monolith python backend/scripts/unified_industrial_seed.py
```

---

## 🕹️ Comandos Útiles de Mantenimiento

**Ver logs en tiempo real:**
```bash
docker-compose logs -f interno-monolith
```

**Apagar la infraestructura (sin borrar datos):**
```bash
docker-compose stop
```

**Destruir la infraestructura (BOMBARDEO TÁCTICO):**
*Advertencia: Esto borrará los volúmenes de Postgres y Redis irremediablemente.*
```bash
docker-compose down -v
```

## 🏗️ Topología del On-Premise
Este entorno orquesta:
1. `interno-db`: PostgreSQL 15.
2. `interno-redis`: Redis 7 Alpine.
3. `interno-monolith`: Contenedor principal de Uvicorn orquestando los 14 servicios en memoria.
4. `tickets-unified-worker`: Contenedor "Sidecar" procesador asíncrono para Escalaciones de Tickets (SLA).
