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
COPY mes_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copia de la estructura del servicio
COPY common /app/common
COPY mes_service/mes_app /app/mes_app
COPY mes_service/scripts /app/scripts
COPY mes_service/alembic /app/alembic
COPY mes_service/alembic.ini /app/alembic.ini
COPY mes_service/entrypoint.sh /app/entrypoint.sh

# 4. Ajuste de permisos
RUN addgroup --system app && adduser --system --group app && \
    chmod +x /app/entrypoint.sh && \
    chown -R app:app /app

USER app

EXPOSE 8000

CMD ["/bin/sh", "/app/entrypoint.sh"]
