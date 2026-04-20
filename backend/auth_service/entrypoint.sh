#!/bin/sh
# InternoCore Auth-Service Entrypoint
# Shell-level AWS secret injection + Alembic + Uvicorn

echo "========================================"
echo "  InternoCore Auth-Service Bootstrap"
echo "========================================"

# --- PRE-BOOT: Inyectar secretos de AWS como variables de entorno reales ---
# Pydantic lee env vars al instanciarse. Inyectarlos aqui garantiza que el
# engine de SQLAlchemy se construya con el DATABASE_URL correcto desde el inicio.

if [ "$CORE_ENV_MODE" = "aws" ] || [ "$ENV_MODE" = "aws" ]; then
    SECRET_ID="${AWS_SECRET_ID:-interno-core/auth-service/prod}"
    AWS_REGION_LOAD="${AWS_REGION:-us-east-2}"
    
    echo "[BOOT] AWS MODE: Cargando secretos desde Secrets Manager (ID: $SECRET_ID, Region: $AWS_REGION_LOAD)..."
    
    # Descargamos el secreto con timeout de 10 segundos
    SECRET_JSON=$(timeout 15 aws secretsmanager get-secret-value \
        --secret-id "$SECRET_ID" \
        --region "$AWS_REGION_LOAD" \
        --query 'SecretString' \
        --output text 2>/dev/null) || true
    
    if [ -n "$SECRET_JSON" ]; then
        # Parseamos con Python3 que siempre esta disponible en la imagen
        DB_URL=$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('database_url',''))" 2>/dev/null || echo "")
        SK_VAL=$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('secret_key',''))" 2>/dev/null || echo "")
        IK_VAL=$(echo "$SECRET_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('int_internal_api_key',''))" 2>/dev/null || echo "")
        
        if [ -n "$DB_URL" ]; then
            export DATABASE_URL="$DB_URL"
            export CORE_DATABASE_URL="$DB_URL"
            echo "[BOOT] DATABASE_URL inyectada (host: $(echo $DB_URL | python3 -c 'import sys; u=sys.stdin.read(); print(u.split("@")[1].split(":")[0] if "@" in u else "unknown")'))"
        else
            echo "[BOOT] WARNING: database_url vacia en el secreto. Usando env var existente."
        fi
        
        [ -n "$SK_VAL" ] && export SECRET_KEY="$SK_VAL" && export CORE_SECRET_KEY="$SK_VAL" && echo "[BOOT] SECRET_KEY inyectada."
        [ -n "$IK_VAL" ] && export INTERNAL_API_KEY="$IK_VAL" && export CORE_INTERNAL_API_KEY="$IK_VAL" && echo "[BOOT] INTERNAL_API_KEY inyectada."
        
        echo "[BOOT] Inyeccion completada exitosamente."
    else
        echo "[BOOT] WARNING: timeout o error al obtener secreto '$SECRET_ID'. Fallback a env vars de Task Definition."
    fi
fi

# --- PASO 1: Migraciones Alembic ---
echo ""
echo ">> [1/3] Ejecutando migraciones Alembic..."
python -m alembic upgrade head
echo "   Migraciones aplicadas."

# --- PASO 2: Seed inicial (tolerante a fallos) ---
echo ""
echo ">> [2/3] Ejecutando seed de datos iniciales..."
if python scripts/seed.py; then
    echo "   Seed completado."
else
    echo "   Seed fallo o ya existe. Continuando..."
fi

# --- PASO 3: Servidor Uvicorn ---
echo ""
if [ "$ENV_MODE" = "aws" ] || [ "$CORE_ENV_MODE" = "aws" ]; then
    echo ">> [3/3] Iniciando Uvicorn (AWS MODE)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
else
    echo ">> [3/3] Iniciando Uvicorn (DEV MODE)..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
