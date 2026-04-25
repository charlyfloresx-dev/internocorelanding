FROM python:3.11-slim

WORKDIR /app/asset_manager_service

ENV PYTHONPATH="/app:/app/asset_manager_service"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY common/requirements.txt /app/common/requirements.txt
COPY asset_manager_service/requirements.txt .
RUN pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r requirements.txt

# Copy common layer
COPY common /app/common

# Copy service source
COPY asset_manager_service /app/asset_manager_service

EXPOSE 8006

CMD ["uvicorn", "asset_app.main:app", "--host", "0.0.0.0", "--port", "8006"]
