#!/bin/bash
# scripts/init_db.sh - Initializes the project's databases
echo "🚀 Initializing Interno Core databases..."
docker-compose up -d postgres-db redis
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker exec $(docker-compose ps -q postgres-db) pg_isready -U user -d dbname; do
  sleep 1
done
echo "✅ PostgreSQL is ready."
