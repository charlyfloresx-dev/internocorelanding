#!/bin/bash
echo "=========== INITIALIZING AWS LOCALSTACK ==========="

# Configurando AWS CLI to use LocalStack (no real credentials needed)
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="us-east-1"
export LOCALSTACK_URL="http://localhost:4566"

# 1. Crear Buckets S3
echo "Creando bucket S3: kiosk-events..."
awslocal s3 mb s3://kiosk-events

echo "Creando bucket S3: momentos-assets..."
awslocal s3 mb s3://momentos-assets

# Configurar CORS (opcional pero útil para pruebas de subida directa desde el frontend)
echo "------------------------------------------------"
echo '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedHeaders": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
      "MaxAgeSeconds": 3000
    }
  ]
}' > /tmp/cors.json

awslocal s3api put-bucket-cors --bucket kiosk-events --cors-configuration file:///tmp/cors.json
awslocal s3api put-bucket-cors --bucket momentos-assets --cors-configuration file:///tmp/cors.json
echo "CORS configurado para buckets: kiosk-events, momentos-assets"

# 2. Configurar la estructura de Parameter Store base para SSM
echo "------------------------------------------------"
echo "Configurando SSM Parameter Store Global..."

awslocal ssm put-parameter \
  --name "/interno-core/global/database_url" \
  --value "postgresql+asyncpg://user:password@interno-db:5432/interno_db" \
  --type "String" \
  --overwrite

awslocal ssm put-parameter \
  --name "/interno-core/global/secret_key" \
  --value "CHANGEME_SECRET_KEY_FOR_LOCALSTACK" \
  --type "String" \
  --overwrite

echo "=========== AWS LOCALSTACK STARTUP COMPLETE ==========="
