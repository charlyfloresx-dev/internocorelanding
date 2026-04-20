# Implementation History: Budget Pivot & GIS Finalization
**Date:** 2026-04-20
**Phase:** 58 - AWS Budget Pivot (ALB to App Runner) & 57 GIS Integration

## Technical Decisions
- **AWS Budget Pivot**: Identified Application Load Balancer (ALB) and public IPv4 charges as the main drivers for exceeding the $5.00 budget. Decided to eliminate the ALB and transition the `auth_service` to **AWS App Runner** (PaaS).
- **Frontend Security (OAC)**: Moved from S3 Static Website Hosting to **CloudFront with Origin Access Control (OAC)**. This allows the bucket to remain private while CloudFront handles traffic, taking advantage of the Free Tier for internal data transfer.
- **GIS Integration**: Finalized the scraping logic for Tijuana cadastral owners using a session-based approach to handle ASP.NET WebForms (`__VIEWSTATE`).

## Architectural Patterns
- **PaaS Adoption**: Using App Runner for microservices reduces networking complexity (no NAT Gateways or complex ALBs needed for dev).
- **Edge Deployment**: Using CloudFront OAC for SPA routing (403/404 redirects to `index.html`) ensures high availability and zero cost for dev traffic.

## Blockers Resolved
- **Budget Breach**: Resolved the forecasted $6.64 breach by deleting resources that cost ~$27/mo.
- **SPA Routing**: Configured CloudFront error handlers to prevent 404s on direct URL access in Angular.

## Summary of Changes
- **Infrastructure**: Deleted `InternoCore-ALB`. Created `apprunner.yaml`.
- **Frontend**: Created S3 bucket `interno-core-frontend-prod` and CloudFront distribution `E23YTJF59L1IKO` with OAC.
- **Data Integrity**: 
    - Executed `audit_inventory_integrity.py` and found 62 discrepancies.
    - Created and ran `rebuild_inventory_levels.py` to synchronize Stock (Balance) with Ledger (Transactions).
    - Patched `TransferCommandHandler.complete_transfer` in `inventory_service` with **Density Guard** validation.
- **Docs**: Created `APP_RUNNER_DEPLOY_GUIDE.md` and `FRONTEND_DEPLOY_GUIDE.md`.
- **Scripts**: Created `invalidate_cache.ps1`, `.sh`, and `rebuild_inventory_levels.py`.
