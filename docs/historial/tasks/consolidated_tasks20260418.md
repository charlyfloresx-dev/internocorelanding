# Consolidated Tasks - 2026-04-18

## AWS Cloud Infrastructure (Phase 55 - Complete)
- ✅ Fix CORS preflight logic in `CORSMiddleware` via code initialization ordering.
- ✅ Correctly map `int_backend_cors_origins` list in AWS Secrets Manager.
- ✅ Automate Docker Build, ECR Push, and ECS Task Force-Deployment from terminal.
- ✅ Validate End-to-End JWT authentication from CloudFront to Backend.

## Incoming Microservices Rollout (Phase 56 - Pending)
- ⏳ Deploy `inventory_service` to AWS ECR.
- ⏳ Deploy `master_data_service` to AWS ECR.
- ⏳ Provision ECS Fargate Task Definitions and Target Groups for the new services.
- ⏳ Configure ALB listener rules to route path `/api/v1/inventory/*` and `/api/v1/master-data/*`.

## Network Isolation (Pending Configuration)
- ⏳ Assign public DNS (Route 53) and ACM Certificate to the ALB for native HTTPS support.
- ⏳ Close `0.0.0.0/0` in RDS Security Groups and restrict to ECS SG.
