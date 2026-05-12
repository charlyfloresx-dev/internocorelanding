# 🚀 InternoCore: Script de Despliegue Universal (Nueva Cuenta)
# Uso: .\deploy_to_new_aws_account.ps1 -AccountId "123456789012" -Region "us-east-2"

param (
    [Parameter(Mandatory=$true)]
    [string]$AccountId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-2",
    
    [Parameter(Mandatory=$false)]
    [string]$VpcId,
    
    [Parameter(Mandatory=$false)]
    [string[]]$Subnets
)

Write-Host "--- 🏗️ Iniciando Despliegue en Nueva Cuenta ($AccountId) ---" -ForegroundColor Cyan

# 1. Configuración de Roles
$APPRUNNER_ROLE = "arn:aws:iam::$AccountId:role/InternoCore-AppRunner-Role"
$ECR_ROLE = "arn:aws:iam::$AccountId:role/AppRunnerECRAccessRole"

# 2. Verificar o Crear ECR
Write-Host "1/3 Verificando repositorio ECR..."
$REPO_EXISTS = aws ecr describe-repositories --repository-names "interno-core/auth-service" --region $Region 2>$null
if (-not $REPO_EXISTS) {
    aws ecr create-repository --repository-name "interno-core/auth-service" --region $Region
}

# 3. Login y Push (Simulado - Requiere Docker)
Write-Host "2/3 Autenticando Docker con ECR..."
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

# 4. Desplegar App Runner
Write-Host "3/3 Lanzando servicio en App Runner..."
aws apprunner create-service `
    --service-name "auth-service-prod" `
    --source-configuration "{
        \"ImageRepository\": {
            \"ImageIdentifier\": \"$AccountId.dkr.ecr.$Region.amazonaws.com/interno-core/auth-service:latest\",
            \"ImageConfiguration\": {
                \"Port\": \"8000\",
                \"RuntimeEnvironmentVariables\": {
                    \"CORE_ENV_MODE\": \"aws\",
                    \"CORE_AWS_SECRET_ID\": \"interno-core/auth-service/prod\"
                }
            },
            \"ImageRepositoryType\": \"ECR\"
        },
        \"AuthenticationConfiguration\": {
            \"AccessRoleArn\": \"$ECR_ROLE\"
        }
    }" `
    --instance-configuration "{
        \"Cpu\": \"256\",
        \"Memory\": \"512\",
        \"InstanceRoleArn\": \"$APPRUNNER_ROLE\"
    }" --region $Region

Write-Host "--- 🎉 Despliegue iniciado exitosamente ---" -ForegroundColor Green
