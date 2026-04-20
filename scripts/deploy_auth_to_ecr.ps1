# scripts/deploy_auth_to_ecr.ps1
# Automatizacion de despliegue de InternoCore Auth-Service a Amazon ECR

$AWS_ACCOUNT_ID = "584094645491"
$AWS_REGION = "us-east-2"
$ECR_REPO_NAME = "interno-core/auth-service"
$IMAGE_TAG = "latest"
$ECR_URL = "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "--- Iniciando despliegue de Auth-Service a ECR ---"

# 1. Autenticacion en ECR
Write-Host "1. Autenticando con AWS ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL
if ($LASTEXITCODE -ne 0) { Write-Error "FAILED: Autenticacion en ECR"; exit 1 }

# 2. Asegurar que el repositorio exista
Write-Host "2. Verificando repositorio: $ECR_REPO_NAME"
$repoExits = aws ecr describe-repositories --repository-names $ECR_REPO_NAME 2>$null
if (-not $repoExits) {
    Write-Host "INFO: Creando repositorio ECR..."
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION
}

# 3. Construir la imagen
Write-Host "3. Construyendo imagen (Contexto: backend/)..."
docker build -t $ECR_REPO_NAME -f backend/auth_service/Dockerfile backend/
if ($LASTEXITCODE -ne 0) { Write-Error "FAILED: Docker Build"; exit 1 }

# 4. Taggear para ECR
Write-Host "4. Taggeando imagen..."
docker tag ($ECR_REPO_NAME + ":latest") ($ECR_URL + "/" + $ECR_REPO_NAME + ":" + $IMAGE_TAG)

# 5. Push a ECR
Write-Host "5. Subiendo imagen a Amazon ECR..."
docker push ($ECR_URL + "/" + $ECR_REPO_NAME + ":" + $IMAGE_TAG)
if ($LASTEXITCODE -ne 0) { Write-Error "FAILED: Docker Push"; exit 1 }

Write-Host "SUCCESS: Despliegue completado!"
Write-Host ("URL: " + $ECR_URL + "/" + $ECR_REPO_NAME + ":" + $IMAGE_TAG)
