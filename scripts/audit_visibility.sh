#!/bin/bash
# 1. Login (Handshake)
LOGIN_RESP=$(curl -s -X POST "http://localhost:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "charly@interno.com", "password": "charly123"}')

HANDSHAKE_TOKEN=$(echo $LOGIN_RESP | grep -oP '"handshakeToken":"\K[^"]+')

if [ -z "$HANDSHAKE_TOKEN" ]; then
    echo "❌ Error en Handshake. Respuesta: $LOGIN_RESP"
    exit 1
fi

echo "✅ Handshake Token: ${HANDSHAKE_TOKEN:0:10}..."

# 2. Selección de Empresa (Demo)
COMPANY_ID="203e03c9-5d65-43ff-9e83-864ef605426c"
SELECT_RESP=$(curl -s -X POST "http://localhost:8001/api/v1/auth/select-company" \
  -H "Content-Type: application/json" \
  -d "{\"handshakeToken\": \"$HANDSHAKE_TOKEN\", \"tenant_id\": \"$COMPANY_ID\"}")

ACCESS_TOKEN=$(echo $SELECT_RESP | grep -oP '"access_token":"\K[^"]+')

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Error en Selección de Empresa. Respuesta: $SELECT_RESP"
    exit 1
fi

echo "✅ Access Token obtenido."

# 3. Visibility Check (Inventory Summary)
echo "[*] Ejecutando Visibility Check (Summary)..."
curl -s -X GET "http://localhost:8006/api/v1/inventory/summary" \
  -H "X-Company-ID: $COMPANY_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
