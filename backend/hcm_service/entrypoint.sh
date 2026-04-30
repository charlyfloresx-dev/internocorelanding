#!/bin/sh
set -e

echo "========================================"
echo "  InternoCore HR-Service Bootstrap"
echo "========================================"

# --- PASO 1: Ejecutar migraciones de Alembic ---
echo ""
echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head
echo "   ✅ Migraciones aplicadas correctamente."

# --- PASO 2: Ejecutar Seed (tolerante a fallos) ---
echo ""
echo ">> [2/3] Ejecutando seed de colaboradores..."
if python scripts/seed.py; then
    echo "   ✅ Seed completado exitosamente."
else
    echo "   ⚠️  Seed falló o ya fue ejecutado. Continuando de todas formas..."
fi

# --- PASO 3: Iniciar el servidor ---
echo ""
echo ">> [3/3] Iniciando servidor Uvicorn..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
