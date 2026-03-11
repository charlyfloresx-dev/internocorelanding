#!/bin/bash
# scripts/migrate.sh - Runs Alembic migrations for all microservices
echo "🔄 Running migrations for all services..."

services=("auth-service" "master-data-service" "subscription-service" "wms-service" "inventory-service" "tickets-service" "mes-service")

for service in "${services[@]}"; do
  echo "👉 Migrating $service..."
  docker-compose run --rm $service alembic upgrade head
done

echo "✅ All migrations completed."
