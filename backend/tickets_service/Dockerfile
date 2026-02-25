FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH="/app:/app/tickets_service"

WORKDIR /app

# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies
COPY common/requirements.txt /app/common/requirements.txt
COPY tickets_service/requirements.txt /app/tickets_service/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/common/requirements.txt && \
    pip install --no-cache-dir -r /app/tickets_service/requirements.txt

# 3. Copy service structure
COPY common /app/common
COPY tickets_service/app /app/tickets_service/app

# 4. Final Workdir
WORKDIR /app/tickets_service

# 5. Security - Non-root user
RUN addgroup --system app && adduser --system --group app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# 6. Execution
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
