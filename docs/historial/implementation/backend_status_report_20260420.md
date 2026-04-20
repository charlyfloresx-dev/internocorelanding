# Backend Status Report - InternoCore Ecosistema
**Fecha:** 2026-04-20
**Estrategia Actual:** FinOps PaaS App Runner (Despliegue ECR Native)

## 1. Completitud por Microservicio

| Microservicio | Puerto | Completitud | Estado | Descripción Corta |
| :--- | :---: | :---: | :---: | :--- |
| `auth_service` | 8001 | 100% | ✅ | Autenticación Segura, multi-tenant. Migrado a App Runner. |
| `master_data_service` | 8003 | 100% | ✅ | SSOT para Ubicaciones (InventoryLocation), Productos, UOM, Precios B2B. |
| `inventory_service` | 8006 | 98% | ✅ | Control absoluto, Laissez-Faire Async, validación de Density Guard en transferencias. |
| `notification_service` | 8008 | 90% | 🟡 | Motor de alertas en tiempo real vía WebSocket (CapacityViolations activas). |
| `wms_service` | 8007 | 85% | 🟡 | Receiving, Picking, Cycle Count y Validación Cross-Border en rampa. |
| `currency_service` | 8011 | 100% | ✅ | Integración Banxico y caching de divisas (USD/MXN). |
| `subscription_service` | 8005 | 80% | 🟡 | Modelado de pagos de cuotas para Viatra vía Stripe. Faltan SLAs. |
| `kiosk_service` | 8020 | 100% | ✅ | Soporte offline de escaneo para entradas. |
| `hr_service` | 8009 | 10% | 🔴 | Entidades de seguridad (Visa, Sentry, RFC) integradas en dominio logístico, pero faltan ABMs. |
| `mes_service` | 8002 | 10% | 🔴 | Core Operativo Industrial. Esqueleto listo, sin lógica de recetas/BOMs. |
| `tickets_service` | 8004 | 5% | 🔴 | Esquema y DB inicial, faltan SLAs de mesa de ayuda y motor de escalación. |
| `common` | N/A | 100% | ✅ | Configuración limpia de Entorno AWS env-vars, Dependencias Seguras, Event Bus. |

## 2. ¿Qué le falta a cada servicio?
- **`auth/master_data/inventory`**: Cero dependencias funcionales; solo levantamiento del Quota Sandbox (Limit de AWS). 
- **`notification_service`**: Acoplar validaciones push masivas (Push API para PWA Angular) en móviles nativos.
- **`wms_service`**: Stress Testing de transacciones Inter-Company bajo carga inestable simulada.
- **`hr_service`**: ABM completo para el control de `Collaborator` y flujo de aprobaciones de Visas y Gafetes.
- **`mes_service`**: Construir el ciclo completo de órdenes de manufactura y deducción de materias primas (Backflushing).
- **`tickets_service`**: Subida de cobertura de test al menos del 70%.

## 3. Cobertura Funcional del Ecosistema

| Capacidad | Nivel de Cobertura |
| :--- | :---: |
| Autenticación & Autorización (RBAC) | 100% |
| Catálogos Industriales (SSOT) | 100% |
| Tolerancia a Fallos Lógicos (Zero-Cost Async) | 100% |
| Auditoría Inmutable (Alembic Ledger) | 100% |
| Telemetría & Alertas E2E | 90% |
| Control Físico de Capacidad (Density Guard) | 100% |
| Integración Gubernamental/Catastro | 100% |

## 4. Bloqueos Principales

| Prioridad | Bloqueo | Impacto / Servicio | Resolución |
| :---: | :--- | :--- | :--- |
| 🔴 **MAX** | **AWS Service Quota Sandbox** | Clúster Completo. App Runner limitado a 2 instancias (`auth` y `master-data` ocupados y fallando). | Support Ticket `#177671606300742` solicitado para 5 instancias. Esperando revisión humana. |
| 🔴 **ALTO** | **VPC Connectors** | App Runner Services (Todos). Containers en estado `CREATE_FAILED` por Timeout 8000 al no conectar a subred RDS. | Añadir la configuración VPC a la CLI en el momento que AWS otorgue la cuota. |
| 🟡 **MED** | Despliegue de Inventory Service | WMS / Inventory. | Condicionado a la liberación del Sandbox de AWS. |

--- 
**Completitud Global del Backend Re-Estimada:** ~75%
**Fecha de Corte:** 2026-04-20
