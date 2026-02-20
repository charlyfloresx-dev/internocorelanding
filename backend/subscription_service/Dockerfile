FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# 1. Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Dependencias Python
COPY common/requirements.txt /app/common/requirements.txt
COPY subscription_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de la estructura del servicio
COPY common /app/common
COPY subscription_service/app /app/app
COPY subscription_service/alembic /app/alembic
COPY subscription_service/alembic.ini /app/alembic.ini

# 4. Ajuste de permisos
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8005

# 5. Ejecución: Migraciones -> API
CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005"]
