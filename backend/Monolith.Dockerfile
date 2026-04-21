# 🏗️ InternoCore Unified Monolith Dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /app

# Dependencias de OS
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Copiar requerimientos de todos los servicios involucrados
COPY common/requirements.txt /app/common/requirements.txt
COPY auth_service/requirements.txt /app/auth_requirements.txt
COPY master_data_service/requirements.txt /app/master_data_requirements.txt
COPY inventory_service/requirements.txt /app/inventory_requirements.txt

# Instalar todo en una sola capa
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/auth_requirements.txt && \
    pip install --no-cache-dir -r /app/master_data_requirements.txt || true && \
    pip install --no-cache-dir -r /app/inventory_requirements.txt || true

# Copiar TODO el código base del backend
# Esto incluye common, auth_service, master_data_service, inventory_service, etc.
COPY . /app/

# Configurar PYTHONPATH para que los servicios encuentren sus módulos internos
ENV PYTHONPATH=/app:/app/auth_service:/app/master_data_service:/app/inventory_service

# Puerto unificado
EXPOSE 8000

# Usuario no root para seguridad
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app
USER app

# Comando de arranque apuntando al Monolito
CMD ["uvicorn", "main_monolith:app", "--host", "0.0.0.0", "--port", "8000"]
