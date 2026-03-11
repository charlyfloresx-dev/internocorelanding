FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app:/app/inventory_service

WORKDIR /app

# 1. Instalación de dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Instalación de dependencias Python
COPY common/requirements.txt /app/common/requirements.txt
COPY inventory_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de la estructura del servicio
COPY common /app/common
COPY inventory_service/app /app/app
COPY inventory_service/scripts /app/scripts
# alembic copying will go here if/when initialized

# 4. Ajuste de permisos
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# 5. Ejecución
CMD ["sh", "-c", "python scripts/seed.py && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"]
