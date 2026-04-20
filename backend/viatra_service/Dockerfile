FROM python:3.11-slim

WORKDIR /app/viatra_service

ENV PYTHONPATH=/app:/app/viatra_service

COPY viatra_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY common /app/common
COPY viatra_service /app/viatra_service

# Ensure entrypoint is executable
RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]


