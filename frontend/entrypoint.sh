#!/bin/sh

# Ruta donde Nginx sirve los archivos
CONFIG_PATH="/usr/share/nginx/html/assets/config.json"

if [ ! -z "$API_URL" ]; then
  echo "Inyectando API_URL: $API_URL"
  # Creamos el JSON desde cero para evitar conflictos de formato
  echo "{\"apiUrl\": \"$API_URL\", \"environment\": \"production\", \"enableLogging\": true, \"version\": \"1.0.0\"}" > $CONFIG_PATH
fi

# Iniciar Nginx
nginx -g "daemon off;"