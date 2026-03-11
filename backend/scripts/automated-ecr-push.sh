#!/bin/bash
# automated-ecr-push.sh
# Misión: Subir las imágenes de microservicios al Elastic Container Registry (AWS)

REGION="us-east-2"
ACCOUNT_ID="YOUR_AWS_ACCOUNT_ID" # 🔒 Reemplazar con secreto en CI o manual
PROJECT_PREFIX="interno"

# 1. Login a ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# 2. Servicios a subir
SERVICES=("auth_service" "inventory_service" "mes_service" "notification_service" "tickets_service")

for SERVICE in "${SERVICES[@]}"
do
    REPO_NAME="$PROJECT_PREFIX-$SERVICE"
    IMAGE_TAG="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:latest"

    echo "🚀 Procesando $SERVICE..."

    # Crear Repo si no existe
    aws ecr create-repository --repository-name $REPO_NAME --region $REGION || echo "Repo already exists"

    # Build (Contexto backend root)
    docker build -t $REPO_NAME -f $SERVICE/Dockerfile .

    # Tag & Push
    docker tag $REPO_NAME:latest $IMAGE_TAG
    docker push $IMAGE_TAG
    
    echo "✅ $SERVICE subido exitosamente."
done
