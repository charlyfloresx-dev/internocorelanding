# 🏗️ InternoCore Unified Monolith Dockerfile (Multi-Stage Build for AWS Fargate)
# -----------------------------------------------------------------------------

# ==========================================
# STAGE 1: BUILDER (Compilation & Dependencies)
# ==========================================
FROM python:3.11-slim-bullseye as builder

WORKDIR /app

# Instalar dependencias de sistema requeridas para compilar librerías (ej. asyncpg, bcrypt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Crear y activar entorno virtual (esto permite mover las dependencias compiladas fácilmente)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Actualizar pip
RUN pip install --no-cache-dir --upgrade pip

# Copiar archivos de requerimientos
COPY common/requirements.txt /app/common/requirements.txt
COPY auth_service/requirements.txt /app/auth_requirements.txt
COPY master_data_service/requirements.txt /app/master_data_requirements.txt
COPY inventory_service/requirements.txt /app/inventory_requirements.txt
COPY notification_service/requirements.txt /app/notification_requirements.txt
COPY tickets_service/requirements.txt /app/tickets_requirements.txt
COPY mes_service/requirements.txt /app/mes_requirements.txt
COPY subscription_service/requirements.txt /app/subscription_requirements.txt

# Instalar todas las dependencias en el entorno virtual
RUN pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/auth_requirements.txt && \
    pip install --no-cache-dir -r /app/master_data_requirements.txt || true && \
    pip install --no-cache-dir -r /app/inventory_requirements.txt || true && \
    pip install --no-cache-dir -r /app/notification_requirements.txt || true && \
    pip install --no-cache-dir -r /app/tickets_requirements.txt || true && \
    pip install --no-cache-dir -r /app/mes_requirements.txt || true && \
    pip install --no-cache-dir -r /app/subscription_requirements.txt || true


# ==========================================
# STAGE 2: FINAL (Production Runtime)
# ==========================================
FROM python:3.11-slim-bullseye as runner

WORKDIR /app

# Variables de entorno para Python y PYTHONPATH (Shared Kernel Support)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app:/app/auth_service:/app/master_data_service:/app/inventory_service:/app/notification_service:/app/tickets_service:/app/mes_service:/app/subscription_service"

# Instalar SÓLO las librerías en tiempo de ejecución (ej. libpq para interactuar con postgres)
# curl es necesario para el HEALTHCHECK nativo de Docker interactuando con el ALB
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copiar el entorno virtual compilado desde el Builder (libre de gcc y build-essential)
COPY --from=builder /opt/venv /opt/venv

# Copiar el código fuente (se excluyen archivos locales gracias a .dockerignore o copias específicas)
COPY . /app/

# Configurar el usuario no-root por seguridad en ECS Fargate
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app
USER app

# Exponer el puerto de la aplicación (El SG-ECS abrirá este puerto exclusivamente al SG-ALB)
EXPOSE 8000

# Healthcheck Activo: El ALB o ECS verificará este puerto. Si falla, ECS reemplazará el contenedor.
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Comando de arranque apuntando al Monolito (preparado para recibir SIGTERM de ECS)
CMD ["uvicorn", "main_monolith:app", "--host", "0.0.0.0", "--port", "8000"]
