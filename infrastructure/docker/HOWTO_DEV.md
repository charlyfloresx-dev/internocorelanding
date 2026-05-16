# 🚀 Guía Práctica: Entorno de Desarrollo (docker-compose.dev.yml)

Esta guía detalla paso a paso cómo iniciar y operar el entorno de microservicios para desarrollo en InternoCore.

## 📌 Requisitos Previos
- Docker y Docker Compose instalados en tu máquina.
- Archivo `.env` correctamente configurado en la raíz (`c:\API\interno\.env`).
- Puertos libres: `5433` (Postgres), `6379` (Redis), `8001`, `8003`, `8006`, etc.

---

## 🛠️ 1. Levantar el Entorno (Paso a Paso)

### Opción A: Stack de Desarrollo Completo (Recomendado)
Levanta todos los microservicios, bases de datos y API Gateway.
Abre tu terminal (PowerShell) en la raíz del proyecto y ejecuta:
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d --build
```
> El flag `--build` asegura que Docker recompile las imágenes si hiciste cambios en los archivos de Python o Dockerfiles.

### Opción B: Iniciar solo Base de Datos y Caché
Si solo quieres levantar la BD para ejecutar scripts manuales:
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres-db redis
```

---

## 📂 2. Poblar la Base de Datos (Migraciones y Seed)

Una vez que los contenedores estén corriendo, debes inicializar el esquema y los datos básicos.

### Creación de Esquema (Base de datos)
Para que los microservicios creen las tablas requeridas (bypassing Alembic conflicts), ejecuta:
```powershell
docker run --rm --network docker_interno-network -v ${PWD}/backend:/backend -w /backend --env DATABASE_URL=postgresql+asyncpg://user:password@interno-db-dev:5432/dbname --env CORE_DATABASE_URL=postgresql+asyncpg://user:password@interno-db-dev:5432/dbname --env PYTHONPATH=/backend interno-auth-service:latest python scripts/create_all_tables.py
```

### Seed Industrial (Datos Base)
Para inyectar el usuario de pruebas ("Charly") y los permisos necesarios:
```powershell
docker run --rm --network docker_interno-network -v ${PWD}/backend:/backend -w /backend --env-file backend/.env interno-auth-service:latest python scripts/unified_industrial_seed.py
```

---

## 🔍 3. Monitoreo y Mantenimiento

**Ver estado de los contenedores:**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml ps
```

**Revisar logs en tiempo real de un servicio específico (ej. Auth):**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml logs -f auth-service
```

---

## 🛑 4. Detener y Limpiar el Entorno

**Detener los contenedores sin borrar la base de datos:**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml down
```

**🔥 Hard Reset (Borrar contenedores, base de datos y volver a empezar):**
```powershell
docker compose -f infrastructure/docker/docker-compose.dev.yml down -v --remove-orphans
```
> Úsalo si el esquema de la base de datos se corrompe o falla alguna migración.
