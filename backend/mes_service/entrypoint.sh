#!/bin/sh
set -e

echo "========================================"
echo "  InternoCore MES-Service Bootstrap"
echo "========================================"

echo ""
echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head
echo "   ✅ Migraciones aplicadas correctamente."

echo ""
echo ">> [2/3] Ejecutando seed..."
if python scripts/seed.py; then
    echo "   ✅ Seed completado exitosamente."
else
    echo "   ⚠️  Seed falló o ya fue ejecutado. Continuando de todas formas..."
fi

echo ""
echo ">> [3/3] Iniciando servidor Uvicorn..."
exec python -m uvicorn mes_app.main:app --host 0.0.0.0 --port 8000 --reload
