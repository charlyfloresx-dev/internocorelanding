FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la carpeta common (el build context debe ser /backend)
COPY common /app/common

# Copiar el microservicio
COPY mes_service /app/mes_service

# Configurar el PYTHONPATH para que encuentre 'app' y 'common'
ENV PYTHONPATH=/app:/app/mes_service

# Puerto del servicio
EXPOSE 8003

# Comando para ejecutar el servicio
CMD ["uvicorn", "mes_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
