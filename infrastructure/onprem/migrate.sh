#!/bin/bash
# scripts/migrate.sh - Runs Alembic migrations for all microservices
echo "🔄 Running migrations for all services..."

services=("auth_service" "master_data_service" "subscription_service" "wms_service" "inventory_service" "tickets_service" "mes_service")

for service in "${services[@]}"; do
  echo "👉 Migrating $service..."
  docker-compose exec -T interno-monolith bash -c "cd /app/$service && alembic upgrade head"
done

echo "✅ All migrations completed."
