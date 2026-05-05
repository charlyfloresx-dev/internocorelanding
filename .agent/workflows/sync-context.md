---
description: Synchronize Agent Context with Repository State
---

This workflow helps the AI agent update its mental model of the project by reading the latest logs, configurations, and service architectures.

### 1. Root Context Sync
- Read [REPO_LOG.md](file:///c:/API/interno/REPO_LOG.md) to understand the project history and current phase.
- Read [README.md](file:///c:/API/interno/README.md) for the high-level architecture.
- Read [docker-compose.yml](file:///c:/API/interno/docker-compose.yml) and [docker/docker-compose.monolith.yml](file:///c:/API/interno/docker/docker-compose.monolith.yml) to understand the deployment environment.

### 2. Microservice Deep-Dive
- For each directory in `backend/`:
    - Read `SERVICE_LOG.md` (if it exists).
    - Read `README.md` (if it exists).
    - Analyze the `app/models/` or `subscription_app/models/` to understand the domain.
    - Check `alembic/versions/` to verify the database state.

### 3. Identity & Security Audit (Phase 1 Focus)
- Verify `backend/common/security/subscription_guard.py`.
- Verify `backend/common/models/security_audit_log.py`.
- Check `backend/auth_service/auth_app/models/__init__.py`.

### 4. Status Report
- Use `/status-report` to generate a summary of the current state.
