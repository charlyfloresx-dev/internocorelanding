FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

# 1. System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Python dependencies
# Copy common requirements first to cache them
COPY common/requirements.txt /app/common/requirements.txt
COPY currency_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/requirements.txt

# 3. Copy project files
COPY common /app/common
COPY currency_service/app /app/app
# No common models needed here, we have our own in-service model
# for proper microservice isolation

EXPOSE 8000

# Standalone run command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
