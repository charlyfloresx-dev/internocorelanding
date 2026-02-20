FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# --- CORRECCIÓN CLAVE ---
# PYTHONPATH debe incluir ambos directorios para encontrar módulos en la raíz y en common
ENV PYTHONPATH=/app:/app/common

WORKDIR /app

# 1. Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Instalación de dependencias (Common + Service)
# Nota: Ajustado para copiar desde el contexto correcto (./backend)
COPY common/requirements.txt /app/common/requirements.txt
COPY wms_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de código y archivos de Alembic
COPY common /app/common
COPY wms_service/app /app/app
COPY wms_service/alembic /app/alembic
COPY wms_service/alembic.ini /app/alembic.ini
# --- AÑADIDO PARA LA SEED ---
COPY wms_service/seed_wms.py /app/seed_wms.py

# 4. Ajuste de permisos
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# 5. Ejecución: Migraciones -> Semillas -> API
CMD ["sh", "-c", "python -m alembic upgrade head && python seed_wms.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]