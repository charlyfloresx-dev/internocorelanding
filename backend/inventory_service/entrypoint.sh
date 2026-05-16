#!/bin/sh
set -e

echo "=========================================="
echo "  InternoCore Inventory-Service Bootstrap"
echo "=========================================="

# --- PASO 1: Migraciones Alembic (SIEMPRE PRIMERO) ---
echo ""
echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head || echo "⚠️ Alembic failed. Check logs."
echo "   ✅ Migraciones aplicadas."

# --- PASO 2: Seed (tolerante a fallos) ---
echo ""
echo ">> [2/3] Ejecutando seed de inventarios y almacenes..."
if python scripts/seed.py; then
    echo "   ✅ Seed de inventario completado."
else
    echo "   ⚠️  Seed falló o ya fue ejecutado. Continuando..."
fi

# --- PASO 3: Iniciar servidor ---
echo ""
echo ">> [3/3] Iniciando servidor Uvicorn..."
exec python -m uvicorn inventory_app.main:app --host 0.0.0.0 --port 8000
