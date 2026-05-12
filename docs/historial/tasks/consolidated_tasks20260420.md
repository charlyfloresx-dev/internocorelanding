# Consolidated Tasks: 2026-04-20
**Domain:** Infrastructure & GIS

## ✅ COMPLETED
- [x] **AWS Budget Audit**: Identified ALB and IPv4 charges.
- [x] **ALB Cleanup**: Deleted `InternoCore-ALB` and Target Groups.
- [x] **App Runner Config**: Created `apprunner.yaml` for `auth_service`.
- [x] **S3/CloudFront OAC**: Created private bucket and CloudFront distribution with OAC.
- [x] **Cache Invalidation**: Created scripts for instant frontend updates.
- [x] **Documentation Sync**: Updated guides for App Runner and Frontend OAC.
- [x] **GIS Finalization**: Documented Tijuana cadastral integration logic.
- [x] **Inventory Integrity Audit**: Executed locally, fixed 62 discrepancies where balances were missing.
- [x] **Density Guard Implementation**: Patched `receive_transfer` in `inventory_service` with capacity validation.
- [x] **FinOps Final Audit**: Verified RDS ($12.24) and Secrets ($0.40) are the only fixed costs.
- [x] **Recovery Infrastructure**: Created `rebuild_inventory_levels.py` for ledger-based recovery.
- [x] **Phase 60: Unified Secret Architecture**: Refactored all 13 microservices to use unified `InternoSettings` and standardized `load_aws_secrets()` lifecycle.
- [x] **CloudWatch FinOps**: Applied 3-day retention policy to all Log Groups via CLI.
- [x] **Phase 61: Fast-Track Async Reception**: Implemented `validation_status=PENDING` and BackgroundTasks for non-blocking WMS receiving.
- [x] **Architecture Verification**: Achieved 100% CLEAN status in Code Knowledge Graph Audit with support for Async Density Guard.
- [x] **Phase 62: Frontend Deployment (OAC)**: Built Angular production and synchronized to S3 with CloudFront OAC.
- [x] **FinOps & Compliance**: Confirmed CloudWatch 3-day retention and Secret Manager de-duplication.
- [x] **Phase 63: Zero-Cost Async**: Implementación de capa `Laissez-Faire` y migración del SSOT (`InventoryLocation`) liberando al frontend de la latencia.
- [x] **Phase 63: Alembic Migrations**: Despliegue de DB schema (`fe63_val_status`) para estados de validación silenciosos de inventarios.
- [x] **Phase 64: Density Stress-Test**: Validación E2E del disparo de eventos de desbordamiento (Capacity Violation Event) sin brokers costosos.
- [x] **Phase 65: AWS App Runner FinOps Pivot**: Ejecución de limpieza mitigante de recursos en error (`CREATE_FAILED` auth/master) para liberar la cuota de AWS de Sandbox limit=2.
- [x] **Phase 65: AST Code Graph Fix**: Parcheado script `generate_code_graph.py` para soportar asignación multi-espacio de DensityGuard en `validation_status`.
- [x] **Phase 65: VPC Connector Deployment**: Generado e inyectado puente VPC Serverless `InternoCore-VPC-Bridge` atado a la red de la RDS Postgres en AWS CLI. Despliegue de `auth-service` y `master-data` iniciado.

## 🚧 IN PROGRESS / BLOCKED
- [ ] **Auth Service Migration**: Code is ready for App Runner deployment but **BLOCKED** by AWS Quota sandbox (limit 2).
- [ ] **MES Service Migration**: Scheduled after Auth stabilization.
- [ ] **AWS Quota Unlock**: Reactivación de despliegue App Runner una vez completada la revisión humana por parte de AWS (Support Ticket `177671606300742`).

## 📅 PENDING
- [ ] **Migration of Secondary Services**: Apply App Runner pattern to `inventory` and `master_data`.
