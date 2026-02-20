markdown
# AWS Resources Inventory - InternoCore v2.1

## 1. Networking & Security
*   **VPC**: InternoCore-VPC (Private & Public Subnets)
*   **Security Groups**:
    *   `sg-alb-public`: Allow 80/443 from 0.0.0.0/0
    *   `sg-backend-private`: Allow 8000 from `sg-alb-public`
    *   `sg-db-private`: Allow 5432 from `sg-backend-private`

## 2. Compute & Containerization (Backend)
*   **ECR Repository**: `interno-backend/auth-service`
    *   Lifecycle Policy: Expire untagged images > 7 days.
*   **ECS Cluster or App Runner**: `interno-core-cluster`
    *   Service: `auth-service`
    *   CPU: 1 vCPU / Memory: 2 GB
    *   Env Vars: Load from Secrets Manager.

## 3. Database (Persistence)
*   **RDS PostgreSQL**: `interno-core-db`
    *   Version: 15.4+
    *   Instance: db.t4g.micro (Free Tier/Dev) or db.t3.medium (Prod)
    *   Storage: 20GB Autoscaling

## 4. Frontend Hosting
*   **S3 Bucket**: `interno-frontend-assets` (Private Access)
*   **CloudFront Distribution**:
    *   Origin: `interno-frontend-assets.s3...`
    *   OAI/OAC: Restrict S3 access to CloudFront only.
    *   Error Pages: Redirect 403/404 to `/index.html` (SPA Support).

## 5. Secrets Management
*   **AWS Secrets Manager**: `nexosuite/auth-service/prod`
    *   Keys: `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET`