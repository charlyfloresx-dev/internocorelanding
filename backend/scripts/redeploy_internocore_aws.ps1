# 🚀 InternoCore Industrial: Script de Re-Ensamblaje AWS (FinOps & Secure Architecture)
# Región: us-east-2 | Perfil: Industrial ERP

$REGION = "us-east-2"
$VPC_ID = "vpc-0be05235bbfedf785"
# Subredes privadas de la VPC NexoSuite-Production-VPC
$SUBNETS = "subnet-04e7fcf2d855dbb96","subnet-0611bd3d756934140","subnet-0fab7c07f6e31e1c7"
# Roles de IAM (Deben existir previamente)
$APPRUNNER_ROLE = "arn:aws:iam::584094645491:role/InternoCore-AppRunner-Role"
$ECR_ROLE = "arn:aws:iam::584094645491:role/AppRunnerECRAccessRole"

Write-Host "--- 🏗️ Iniciando Re-Ensamblaje de InternoCore ---" -ForegroundColor Cyan

# 1. Crear Security Group para los Interface Endpoints
Write-Host "1/4 Creando Security Group para Endpoints..."
$SG_VPCE_ID = (aws ec2 create-security-group --group-name "InternoCore-VPCEndpoint-SG-v3" --description "SG para Interfaces Privadas (PrivateLink)" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $SG_VPCE_ID --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION # Permitir tráfico interno al endpoint

# 2. Re-conectar los túneles PrivateLink (VPC Endpoints)
Write-Host "2/4 Levantando Túneles PrivateLink (SecretsManager & RDS API)..."
aws ec2 create-vpc-endpoint --vpc-id $VPC_ID --service-name com.amazonaws.$REGION.secretsmanager --vpc-endpoint-type Interface --subnet-ids $SUBNETS --security-group-ids $SG_VPCE_ID --private-dns-enabled --region $REGION
aws ec2 create-vpc-endpoint --vpc-id $VPC_ID --service-name com.amazonaws.$REGION.rds --vpc-endpoint-type Interface --subnet-ids $SUBNETS --security-group-ids $SG_VPCE_ID --private-dns-enabled --region $REGION

# 3. Crear App Runner VPC Connector (El Puente)
Write-Host "3/4 Creando VPC Connector para App Runner..."
$VPC_CONNECTOR_ARN = (aws apprunner create-vpc-connector --vpc-connector-name "InternoCore-VPC-Bridge-v3" --subnets $SUBNETS --security-groups $SG_VPCE_ID --region $REGION --query 'VpcConnector.VpcConnectorArn' --output text)

# 4. Desplegar Microservicios (Ejemplo: Auth-Service)
Write-Host "4/4 Desplegando Auth-Service en App Runner..."
aws apprunner create-service `
    --service-name "auth-service-prod" `
    --source-configuration "{
        \"ImageRepository\": {
            \"ImageIdentifier\": \"584094645491.dkr.ecr.us-east-2.amazonaws.com/interno-core/auth-service:latest\",
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
    }" `
    --network-configuration "{
        \"EgressConfiguration\": {
            \"EgressType\": \"VPC\",
            \"VpcConnectorArn\": \"$VPC_CONNECTOR_ARN\"
        }
    }" --region $REGION

Write-Host "--- 🎉 Operación completada. Servicios en provisionamiento ---" -ForegroundColor Green
