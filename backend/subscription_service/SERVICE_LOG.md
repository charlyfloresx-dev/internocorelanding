# Subscription Service – Log

## Overview
The Subscription Service (port **8002**) manages tenant lifecycle, plans, entitlements, and Stripe billing integration.

---

## Phase 74 – Controlled Service Degradation & SaaS Integrity ✅
**Status**: ✅ Completed · **Date**: 2026-04-30
- **L7 Enforcement**: Integration with global middleware to block restricted/unpaid tenants based on subscription state.
- **Motor de Degradación**: Implementación de un motor de bloqueo basado en el estado de la suscripción (`PAST_DUE`, `RESTRICTED`, `UNPAID`).
- **Paywall Reactivo**: Los inquilinos en estado `RESTRICTED` solo tienen acceso de lectura (`402 Payment Required` en escrituras), mientras que los `UNPAID` enfrentan un bloqueo total mediante un **Global Paywall Overlay** en Angular 19.
- **Entitlements API**: Implementation of `/internal/entitlements/{company_id}` for cross-service status resolution.
- **Webhook**: Handled `invoice.payment_failed` from Stripe with dev-bypass for sensorial validation.
- **Audit Logs**: Forensic tracking of all subscription status changes with `tenant_id` enforcement.

---

## Phase 36 – Multi-Tenant Data Consistency & Stabilization ✅
**Status**: ✅ Completed · **Date**: 2026-03-24
- **Homologation**: Unified subscription seeding for `Enterprise`, `Logistics`, and `Demo` across the entire ecosystem.
- **Bugfixes**: Resolved `ModuleNotFoundError` by correctly packaging `app.dependencies` and importing `ISubscriptionRepository` in `webhook_service.py`.
- **CORS**: Implemented permissive preflight checks (`allow_origins=["*"]`) with expanded headers for UI synchronization.

---

## Phase 20 – Operación Suscripción Blindada ✅
**Status**: ✅ Completed · **Date**: 2026-03-07
- **Architecture**: 100% Clean Architecture compliance achieved.
- **Patterns**: Implemented Repository Pattern (`ISubscriptionRepository`) and Adapter Pattern (`IPaymentProvider`).
- **Decoupling**: Total decoupling from Stripe SDK and SQLAlchemy ORM in the application layer.
- **Compliance**: Verified with Auditor v3 (0 errors, 100% compliance).

---

## Phase 18.5 – Structure Remediation & OpenAPI ✅
**Status**: ✅ Completed · **Date**: 2026-03-06
- **Structure**: Relocated `debug_settings.py` from root to `app/core/`.
- **OpenAPI**: Successfully extracted `subscription.json` spec.
- **Compliance**: Verified 0 "Structure Violations" in Code Graph.

## Phase 18 – SaaS Scale & Stripe Core
**Status**: ✅ Completed · **Date**: 2026-03-06

### Features
- **Stripe Integration**: `BillingService` and `StripeManager` handling embedded checkout sessions.
- **Webhook Handler**: Robust processing for `checkout.session.completed`.
- **Audit Trails**: Forensic logging of all subscription attempts and status changes.
- **Force Activation**: Backend capability to activate tenants manually if needed.

---

## Phase 10.6 – Notification Bridge
**Status**: ✅ Completed · **Date**: 2026-03-06

### Integration
- **Event Dispatch**: Bridge to `Notification Service` (8008) on successful payment.
- **Customer Context**: Capturing Name/Email from Stripe session for personalized welcome emails.

---

## Pending Backlog
- [x] Multi-tenant subscription management (Stripe Billing).
- [x] Implementation of `stripe_webhook` handler.
- [x] Audit for subscription events.
- [ ] Implement self-service plan upgrade (Frontend + Backend).
- [ ] Add support for coupon codes and discounts.
- [ ] Automated subscription cancellation flow.
