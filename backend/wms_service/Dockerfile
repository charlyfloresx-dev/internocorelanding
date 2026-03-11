FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- CONFIGURACIÓN DE RUTAS ---
# PYTHONPATH incluye /app (raíz del servicio) y /app/common (ADN compartido)
ENV PYTHONPATH=/app

WORKDIR /app

# 1. Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Instalación de dependencias (Common + Service)
# Se asume que el contexto de build es la carpeta /backend
COPY common/requirements.txt /app/common/requirements.txt
COPY wms_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de código y estructura de archivos
# Copiamos common para que esté disponible como módulo
COPY common /app/common

# Copiamos el código de la aplicación
COPY wms_service/app /app/app

# Copiamos archivos de configuración de base de datos
COPY wms_service/alembic /app/alembic
COPY wms_service/alembic.ini /app/alembic.ini

# --- CORRECCIÓN DE LA SEED ---
COPY wms_service/scripts /app/scripts

# 4. Ajuste de permisos para seguridad
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# 5. Ejecución: Migraciones -> Semillas -> Inicio de API
CMD ["sh", "-c", "python -m alembic upgrade head && python scripts/seed.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]