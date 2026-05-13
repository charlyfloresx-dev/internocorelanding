#!/bin/sh
echo "========================================"
echo "  InternoCore Subscription-Service Bootstrap"
echo "========================================"

echo ">> [1/2] Ejecutando migraciones Alembic..."
python -m alembic upgrade head

echo ">> [2/2] Iniciando Uvicorn..."
exec uvicorn subscription_app.main:app --host 0.0.0.0 --port 8000 --reload
