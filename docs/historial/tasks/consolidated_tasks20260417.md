# Consolidated Tasks - 2026-04-17
# Phase 55: AWS Industrial Deployment & Frontend Connection

---

## 🛠 Backend (auth_service & infrastructure)
- [x] **Secret Injection Fix**: Implement architecture-level secret injection in `entrypoint.sh` to bypass Pydantic instantiation limits.
- [x] **RDS Connectivity**: Validate connectivity from ECS Task (Ohio) to RDS PostgreSQL.
- [x] **Environment Support**: Update `common/config.py` to recognize `aws` as a valid production-like environment.
- [x] **ALB Integration**: Associate ECS service with Application Load Balancer via Target Groups.
- [x] **E2E Validation**: Confirm full auth flow (handshake + login + selection) through the public DNS of the ALB.
- [x] **Security Sanitization**: Ensure Secrets Manager payloads are created from secure local files (`file://`).
- [ ] **Infrastructure Hardening**: Recreate NAT Gateway to move ECS tasks to private subnets (Current: Public Subnets).
- [ ] **DB Access Restriction**: Restrict RDS Security Group to only allow ingress from the ECS Security Group.

## 💻 Frontend (Angular)
- [x] **Prod Environment Connectivity**: Update `environment.prod.ts` with real ALB endpoints instead of localhost.
- [x] **Build Config Fix**: Update `angular.json` production configuration with missing `fileReplacements` for environments.
- [x] **Deployment**: Build and sync frontend to S3 bucket.
- [x] **CDN Invalidation**: Trigger CloudFront invalidation for the new build to propagate globally.
- [x] **Asset Path Fix**: Correct S3 sync logic to place files in the root instead of `/browser/`.
- [ ] **Login Validation**: Perform post-propagation login test (Waiting for CF TTL).

## 📄 Documentation & Governance
- [x] **Infrastructure Reference**: Update `docs/infraestructura/aws_infrastructure_reference.md` with accurate IDs and endpoints.
- [x] **Deploy Guide**: Create `docs/infraestructura/MICROSERVICE_DEPLOY_GUIDE.md` for team onboarding.
- [x] **Lessons Learned**: Document technical debt and resolved blockers in `docs/lecciones_aprendidas/aws_deployment_lessons_20260417.md`.
- [x] **History Log**: Update `docs/historial/implementation/master_implementation_history20260417.md`.
- [x] **Master Index**: Update global documentation links.

---

## 🔝 Next Session Priorities
1. **Deployment Scaling**: Deploy `inventory_service` and `master_data_service` using the new AWS pattern.
2. **ALB Routing**: Configure path-based routing in the ALB to handle multiple microservices behind the same DNS.
3. **Security**: Implement SSL/TLS (HTTPS) for the ALB using AWS Certificate Manager.
