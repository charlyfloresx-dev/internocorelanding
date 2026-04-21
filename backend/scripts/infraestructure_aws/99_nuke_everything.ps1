# 🧨 InternoCore Cloud Janitor: Script de Limpieza Total (Nuke to Zero)
# Región: us-east-2 | Objetivo: $0.00 en factura facturada

$REGION = "us-east-2"

Write-Host "--- 💣 Iniciando Operación Nuke to Zero ---" -ForegroundColor Red

# 1. Eliminar todos los servicios de App Runner
Write-Host "1/6 Eliminando servicios de App Runner..."
$services = aws apprunner list-services --region $REGION --query "ServiceSummaryList[*].ServiceArn" --output text
foreach ($arn in $services -split "\s+") {
    if ($arn) {
        Write-Host "Borrando: $arn"
        aws apprunner delete-service --service-arn $arn --region $REGION
    }
}

# 2. Eliminar VPC Endpoints
Write-Host "2/6 Eliminando VPC Endpoints..."
$endpoints = aws ec2 describe-vpc-endpoints --region $REGION --query "VpcEndpoints[*].VpcEndpointId" --output text
if ($endpoints) {
    aws ec2 delete-vpc-endpoints --vpc-endpoint-ids ($endpoints -split "\s+") --region $REGION
}

# 3. Eliminar VPC Connectors de App Runner
Write-Host "3/6 Eliminando VPC Connectors..."
$connectors = aws apprunner list-vpc-connectors --region $REGION --query "VpcConnectors[*].VpcConnectorArn" --output text
foreach ($arn in $connectors -split "\s+") {
    if ($arn) {
        aws apprunner delete-vpc-connector --vpc-connector-arn $arn --region $REGION
    }
}

# 4. Eliminar Instancia de RDS (Sin Snapshot Final)
Write-Host "4/6 Eliminando instancia de RDS (interno-core-db)..."
aws rds delete-db-instance --db-instance-identifier "interno-core-db" --skip-final-snapshot --region $REGION 2>$null

# 5. Vaciar y Borrar Buckets de S3 del Frontend
Write-Host "5/6 Borrando buckets de S3..."
aws s3 rb s3://interno-core-frontend-prod --force 2>$null
aws s3 rb s3://internocore-frontend-production-584094645491 --force 2>$null

# 6. Eliminar ECR Repositories
Write-Host "6/6 Borrando repositorios de ECR..."
aws ecr delete-repository --repository-name "interno-backend-auth-service" --force --region $REGION 2>$null
aws ecr delete-repository --repository-name "interno-core/auth-service" --force --region $REGION 2>$null

# 7. Liberar Elastic IPs Huérfanas
Write-Host "7/7 Liberando Elastic IPs sin usar..."
$eips = aws ec2 describe-addresses --region $REGION --query "Addresses[?InstanceId==null].AllocationId" --output text
foreach ($id in $eips -split "\s+") {
    if ($id) {
        Write-Host "Liberando IP: $id"
        aws ec2 release-address --allocation-id $id --region $REGION
    }
}

Write-Host "--- ✨ Limpieza completada. Revisa CloudFront y Snapshots Manuales ---" -ForegroundColor Yellow
