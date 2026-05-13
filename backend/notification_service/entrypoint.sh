#!/bin/sh
echo "=========================================="
echo "  InternoCore Notification-Service Bootstrap"
echo "=========================================="

echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head || echo "⚠️ Alembic falló. Continuando..."

echo ">> [2/3] Ejecutando seed de datos (si existe)..."
if [ -f "scripts/seed.py" ]; then
    python scripts/seed.py || echo "⚠️ Seed falló. Continuando..."
else
    echo "ℹ️ No se encontró script de seed para notificaciones."
fi

echo ">> [3/3] Iniciando Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
