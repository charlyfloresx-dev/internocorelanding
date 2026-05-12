# 📋 Subscription Service

Motor de licencias SaaS de **InternoCore**. Controla qué empresas (tenants) tienen acceso, qué plan tienen contratado, y qué módulos del sistema pueden usar.

## Responsabilidades

- Gestión de **Planes** (Básico, Pro) y sus módulos incluidos
- Gestión de **Suscripciones** por empresa (TRIAL, ACTIVE, PAST_DUE, EXPIRED)
- Gestión de **Entitlements** — acceso efectivo por módulo para cada empresa
- **Endpoint interno** para que `auth_service` consulte módulos habilitados
- **Auditoría inmutable** de cambios de plan y estado

## NO hace

- Facturación B2B para clientes de los tenants → `billing_service`
- Autenticación de usuarios → `auth_service`

## Puerto

`8002` (host) → `8002` (container)

## Arquitectura y Auditoría
El servicio utiliza un enfoque de **Auditoría Inmutable**. Cada cambio en el estado de una suscripción o en los permisos (entitlements) genera un registro en `audit_subscription_logs` capturando el `before_state` y `after_state` en formato JSONB, incluyendo la IP y el usuario responsable.

## Fases de Implementación (MVP)
1. **Fase 0: Cleanup** - Depuración del antiguo `billing_service` y actualización del `MANIFEST.md`.
2. **Fase 1: Scaffolding** - Configuración de Clean Architecture, Docker y dependencias asíncronas.
3. **Fase 2: Domain Modeling** - Definición de modelos SQLAlchemy para Planes, Módulos y Entitlements.
4. **Fase 3: CQRS & Internal API** - Implementación de comandos para Trials y consultas optimizadas para Handshake.
5. **Fase 4: Auditing & Persistence** - Implementación del sistema de rastro forense e inmutabilidad.

## Endpoints

```
POST /api/v1/subscriptions/trial          # Inicia trial de 14 días
GET  /internal/entitlements/{company_id}  # Handshake para auth_service
```

## Quick Start (local)

```bash
# Desde /backend
cd subscription_service
alembic upgrade head
uvicorn app.main:app --reload --port 8002
```