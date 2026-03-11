FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# 1. Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Instalación de dependencias Python
COPY common/requirements.txt /app/common/requirements.txt
COPY master_data_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de la estructura del servicio (Siguiendo el modelo de Auth)
COPY common /app/common
COPY master_data_service/app /app/app
COPY master_data_service/alembic /app/alembic
COPY master_data_service/alembic.ini /app/alembic.ini
COPY master_data_service/scripts /app/scripts

# 4. Ajuste de permisos
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# 5. Ejecución: Estandarizada como el Auth Service
# (Ajustado para usar seed_master_data.py dentro de scripts)
CMD ["sh", "-c", "python -m alembic upgrade head && python scripts/seed.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]