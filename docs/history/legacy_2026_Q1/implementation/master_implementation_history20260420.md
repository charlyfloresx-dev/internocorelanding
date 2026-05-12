# Implementation History: Budget Pivot, Density Guard & High Availability
**Date:** 2026-04-20
**Phases:** 
- 57: GIS Integration
- 58: AWS Budget Pivot (ALB to App Runner)
- 63: High Operational Availability (Laissez-Faire) & Density Guard
- 64: Visibility Stress-Test & Resilience
- 65: FinOps App Runner Isolation & AWS Service Quotas

## Technical Decisions
- **AWS Budget Pivot**: Identified Application Load Balancer (ALB) and public IPv4 charges as the main drivers for exceeding the $5.00 budget. Decided to eliminate the ALB and transition the `auth_service` to **AWS App Runner** (PaaS).
- **Frontend Security (OAC)**: Moved from S3 Static Website Hosting to **CloudFront with Origin Access Control (OAC)**. This allows the bucket to remain private while CloudFront handles traffic, taking advantage of the Free Tier for internal data transfer.
- **GIS Integration**: Finalized the scraping logic for Tijuana cadastral owners using a session-based approach to handle ASP.NET WebForms (`__VIEWSTATE`).

## Architectural Patterns
- **PaaS Adoption**: Using App Runner for microservices reduces networking complexity (no NAT Gateways or complex ALBs needed for dev).
- **Edge Deployment**: Using CloudFront OAC for SPA routing (403/404 redirects to `index.html`) ensures high availability and zero cost for dev traffic.
- **Microservices Laissez-Faire**: Refactorización del flujo WMS (`receive_transfer`) donde el frontend recibe instantáneamente un *202 Accepted* delegando validaciones pesadas (Density Guard) mediante `FastAPI BackgroundTasks`.
- **SSOT Migration (Single Source of Truth)**: `InventoryLocation` transferido del `inventory_service` hacia `master_data_service` permitiendo validación estructural unificada y centralizando la geografía de los almacenes.
- **Event-Driven Resilience**: Desacople usando el bus inter-service para disparar `CapacityViolationEvent` hacia el motor de notificaciones al saturar ubicaciones industriales.

## Blockers Resolved
- **Budget Breach**: Resolved the forecasted $6.64 breach by deleting resources that cost ~$27/mo.
- **SPA Routing**: Configured CloudFront error handlers to prevent 404s on direct URL access in Angular.
- **App Runner "Zombies"**: Eliminados exitosamente servicios en estado `CREATE_FAILED` (Auth, Master Data) liberando la cuota estricta (2) de la región.
- **App Runner VPC Bridge**: Identificado timeout de salud al faltar VPC Connectors en App Runner hacia los Security Groups del RDS. **(RESUELTO: Desplegado `InternoCore-VPC-Bridge` vía API, servicios redesplegados y en `OPERATION_IN_PROGRESS`)**.

## Summary of Changes
- **Infrastructure**: Deleted `InternoCore-ALB`. Created `apprunner.yaml`.
- **Frontend**: Created S3 bucket `interno-core-frontend-prod` and CloudFront distribution `E23YTJF59L1IKO` with OAC.
- **Data Integrity**: 
    - Executed `audit_inventory_integrity.py` and found 62 discrepancies.
    - Created and ran `rebuild_inventory_levels.py` to synchronize Stock (Balance) with Ledger (Transactions).
    - Patched `TransferCommandHandler.complete_transfer` in `inventory_service` with **Density Guard** validation.
- **Docs**: Created `APP_RUNNER_DEPLOY_GUIDE.md` and `FRONTEND_DEPLOY_GUIDE.md`.
- **Scripts**: Created `invalidate_cache.ps1`, `.sh`, and `rebuild_inventory_levels.py`.
