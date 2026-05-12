# Consolidated Tasks - 2026-05-08

## Overview
Phase 89 & 90 completadas. Blindaje de Triple Identidad, industrialización del acceso de proveedores, y evolución del audit script con exclusiones inteligentes. 14/14 microservicios al 100% compliance.

## Completed Tasks (Session 1 — AM)
- [x] **Triple Identity Schema**: Implementación de `external_assigned_at` y soporte para `Collaborator` / `ExternalContact`.
- [x] **Industrial Seed**: Sincronización de colaboradores y contactos externos en la base de datos industrial.
- [x] **Backend Validation Flows**: 
    - `flow_load_balancing.py`: Validado el balanceo y liberación de licencias.
    - `flow_token_expiration.py`: Validado el cumplimiento de SLA de 72h y bloqueo de tokens.
    - `flow_evidence_quota.py`: Validado el control de cuotas de almacenamiento por plan de suscripción.
- [x] **Frontend SSOT Integration**: Redirección de todo el tráfico a través del puerto 8000 (Monolito Gateway).

## Completed Tasks (Session 2 — PM)
- [x] **Alembic Migration**: Migración exitosa de `external_token` a la tabla de tickets.
- [x] **Seed Update**: Contacto externo Alicia Torres actualizado con `charly.flores.x@gmail.com`.
- [x] **Industrial Flows Simulator (v2)**: Tráfico HTTP real desde el frontend (POST /tickets, POST /triage).
- [x] **Ticket Creation via API**: Validación de `TKT-2026-0001` con trazabilidad forense.
- [x] **Tenant Filter Fix**: `get_by_external_token` documentado como bypass_tenant.
- [x] **Code Graph Audit v2**: Smart Tenant Exclusions + Public Data Leakage Guard.
- [x] **Compliance**: 14/14 microservicios al 100% — 0 errores.
- [x] **REPO_LOG**: Phase 90 registrada.

## Completed Tasks (Session 3 — Night) - Phase 91
- [x] **Industrial Mobile POS Integration**: Implementación del flujo de vinculación QR (Zero-Trust).
- [x] **Flutter Dynamic Networking**: Refactorización de la inyección de dependencias para soportar URLs de servidor dinámicas.
- [x] **Frontend POS Integration**: Drawer "Vincular POS" y generación de QR de aprovisionamiento en Angular.
- [x] **Backend POS Checkout**: Habilitación de endpoints atómicos de venta en `inventory_service`.
- [x] **Mobile Setup Mode**: Activador por *Long Press* en logo para re-aprovisionamiento de terminales.
- [x] **Documentation**: Creación de `docs/mobile/MOBILE_POS_PROVISIONING.md`.
- [x] **Compliance**: Auditoría del Code Graph al 100% (CLEAN).


## Architectural Decisions
- **bypass_tenant for External Tokens**: Acceso global por diseño — proveedores no conocen `company_id`.
- **Smart Audit Exclusions**: Patrones `external_token`, `escalation`, `public`, `global`, `cron`, `webhook`, `migration` excluidos automáticamente del tenant check.

---

## 📋 BACKLOG CONSOLIDADO (Pendientes Activos del Proyecto)

### 🔴 Prioridad Alta (Bloquean producción)
- [ ] **Frontend Manual Validation**: Ejecutar los 3 flujos de Triple Identidad desde la UI del navegador y verificar peticiones en Network tab.
- [ ] **Self-Service Checkout**: Redirigir tenants `UNPAID` a Stripe Checkout desde el Paywall.
- [ ] **Success Callback**: Restauración automática de servicio al recibir `checkout.session.completed`.
- [ ] **AWS ECR Push**: Crear repositorio ECR y subir primera imagen del backend.
- [ ] **S3 + CloudFront**: Configurar bucket S3 y distribución CloudFront para el frontend.

### 🟡 Prioridad Media (Funcionalidad industrial)
- [ ] **Invoice History**: Mostrar facturas históricas de Stripe en la pestaña de Billing.
- [ ] **Plan Management UI**: UI para upgrade/downgrade de tiers de suscripción.
- [ ] **CMMS Consume Endpoint**: `POST /consume` en `work_order_routes.py` para consumibles.
- [ ] **CMMS Domain Events**: Orquestación asíncrona de `ToolCheckout` y `ConsumableUsed` hacia `inventory_service`.
- [ ] **CMMS Frontend**: Kanban de Mantenimiento y Dashboard unificado.
- [ ] **Handheld UI**: Componentes de escaneo para terminal móvil (WMS).
- [ ] **Picking Optimization**: Lógica de sugerencia de rutas (S-Shape vs Largest Gap).

### 🟢 Prioridad Baja (Nice-to-have / Polish)
- [ ] **Tech Stack Section**: Añadir sección visual de stack tecnológico a la landing page.
- [ ] **Demo Video**: Crear o enlazar video profesional del sistema.
- [ ] **WhatsApp WABA**: Registrar número oficial en Twilio Console.
- [ ] **WhatsApp Frontend**: Exponer UI de mapeo de grupos en módulo Admin.
- [ ] **Volumetric Guard**: Completar dimensiones físicas de todos los productos en catálogo maestro.
- [ ] **Landed Cost Engine**: Motor de costeo para valorización real de inventarios.
