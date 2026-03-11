#!/bin/bash
# scripts/init_db.sh - Initializes the project's databases
echo "🚀 Initializing Interno Core databases..."
docker-compose up -d postgres
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $(docker-compose ps -q postgres) pg_isready -U postgres; do
  sleep 1
done
echo "✅ PostgreSQL is ready."
