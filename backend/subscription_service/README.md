# 📋 Subscription Service

Motor de licencias SaaS de **InternoCore**. Controla qué empresas (tenants) tienen acceso, qué plan tienen contratado, y qué módulos del sistema pueden usar.

## Responsabilidades

- Gestión de **Planes** (Free, Basic, Pro) y sus módulos incluidos
- Gestión de **Suscripciones** por empresa (TRIAL, ACTIVE, PAST_DUE, EXPIRED)
- Gestión de **Entitlements** — acceso efectivo por módulo para cada empresa
- **Endpoint interno** para que `auth_service` consulte módulos habilitados
- **Auditoría inmutable** de cambios de plan y estado

## NO hace

- Facturación B2B para clientes de los tenants → `billing_service`
- Autenticación de usuarios → `auth_service`

## Puerto

`8005` (host) → `8005` (container)

## Base de Datos

`subscription_db` en PostgreSQL compartido

## Endpoints

```
POST /api/v1/subscriptions/trial          # Inicia trial de 14 días
GET  /internal/entitlements/{company_id}  # Solo para auth_service (sin JWT en MVP)
```

## Quick Start (local)

```bash
# Desde /backend
cd subscription_service
alembic upgrade head
uvicorn app.main:app --reload --port 8005
```
