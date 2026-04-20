# 🧭 INTERNO CORE - MASTER INDEX (SSOT)

> **Status:** Active / Optimized entry point.
> **Last Updated:** 2026-04-18
> **Phase:** 56 - AWS Microservices Rollout (inventory_service)

Bienvenido al índice maestro de la documentación técnica y operativa de **InternoCore**. Este es el punto de entrada oficial (SSOT) para la navegación del repositorio.

---

## 🚀 ACCESO RÁPIDO (CORE)
1.  [README.md](file:///c:/API/interno/README.md) - **Visión General y Reglas de Negocio**.
2.  [REPO_LOG.md](file:///c:/API/interno/REPO_LOG.md) - **Memoria Histórica y Evolución**.
3.  [Guía de Arranque](file:///c:/API/interno/docs/01%20Local%20Setup/01%20Guia%20ArranqueLocal.MD) - **Configuración Local y Modos (ERP / Kiosk)**.
4.  [MANIFEST.md](file:///c:/API/interno/docs/internal/MANIFEST.md) - **Inventario de Activos y Servicios**.

---

## 📂 DOCUMENTACIÓN MAESTRA (`docs/`)

### 🏗️ Arquitectura e Infraestructura
*   [01_ARCHITECTURE.md](file:///c:/API/interno/docs/02%20Arquitecture/01_ARCHITECTURE.md): ADN Técnico, Stack y Clean Architecture.
*   [ARCHITECTURAL_LOG.md](file:///c:/API/interno/docs/architecture/ARCHITECTURAL_LOG.md): Historial de decisiones arquitectónicas.
*   [AWS_Deployment.md](file:///c:/API/interno/docs/infraestructura/AWS_Deployment_Strategy.md): Estrategia de nube y Fargate.
*   [02_BACKEND_DEPLOYMENT.md](file:///c:/API/interno/docs/infraestructura/02_BACKEND_DEPLOYMENT.md): Guía técnica de despliegue.
*   [aws_infrastructure_reference.md](file:///c:/API/interno/docs/infraestructura/aws_infrastructure_reference.md): **Referencia AWS validada** (IDs, endpoints, SGs, comandos).
*   [MICROSERVICE_DEPLOY_GUIDE.md](file:///c:/API/interno/docs/infraestructura/MICROSERVICE_DEPLOY_GUIDE.md): Guía de despliegue ECS/Fargate (Legacy).
*   [APP_RUNNER_DEPLOY_GUIDE.md](file:///c:/API/interno/docs/infraestructura/APP_RUNNER_DEPLOY_GUIDE.md): **Guía Low-Cost (App Runner)**.
*   [FRONTEND_DEPLOY_GUIDE.md](file:///c:/API/interno/docs/infraestructura/FRONTEND_DEPLOY_GUIDE.md): **Guía Frontend OAC + CloudFront**.

### 🔐 Especificaciones Operativas (`docs/specs/`)
*   [PHASE_SPECS.md](file:///c:/API/interno/docs/specs/PHASE_SPECS.md): Especificaciones de Fases y Criterios de Aceptación.
*   [BACKEND_SPECS.md](file:///c:/API/interno/docs/specs/BACKEND_SPECS.md): Estándares de desarrollo FastAPI.
*   [MES_CORE.md](file:///c:/API/interno/docs/specs/MES_CORE.md): Lógica de producción y OEE.
*   [PRICING_AND_CONTRACTS.md](file:///c:/API/interno/docs/specs/PRICING_AND_CONTRACTS.md): Lógica jerárquica de listas de precios y contratos B2B.
*   [Inter-Company API](file:///c:/API/interno/docs/specs/inter_company_api.md): Protocolos de transferencia entre tenants.
*   [ERP_EXPANSION_BLUEPRINT.md](file:///c:/API/interno/docs/specs/ERP_EXPANSION_BLUEPRINT.md): Arquitectura proyectada para Sales, Finance y Procurement.

### 📝 Tareas e Historial de Implementación (`docs/historial/`)
*   [Consolidated Tasks (Hoy 2026-04-20)](file:///c:/API/interno/docs/historial/tasks/consolidated_tasks20260420.md): **Presupuesto AWS (Pivot App Runner)**.
*   **[Implementation History (Hoy 2026-04-20)](file:///c:/API/interno/docs/historial/implementation/master_implementation_history20260420.md)**: Registro técnico del Pivot ALB -> App Runner.
*   [Consolidated Tasks (2026-04-18)](file:///c:/API/interno/docs/historial/tasks/consolidated_tasks20260418.md): **GIS & AWS Cloud Stability**.
*   [Implementation History (2026-04-18)](file:///c:/API/interno/docs/historial/implementation/master_implementation_history20260418.md): Registro técnico GIS & architecture.
*   [Lecciones Aprendidas AWS 2026-04-17](file:///c:/API/interno/docs/lecciones_aprendidas/aws_deployment_lessons_20260417.md): **7 lecciones (incluye Low-Cost Pivot)**.
*   [Archived - Tasks 20260417](file:///c:/API/interno/docs/historial/tasks/consolidated_tasks20260417.md): AWS Deployment Phase 55.
*   [Archived - History 20260417](file:///c:/API/interno/docs/historial/implementation/master_implementation_history20260417.md): AWS Deployment Record.
*   [Archived - Tasks 20260416](file:///c:/API/interno/docs/historial/tasks/consolidated_tasks20260416.md): Infraestructura y Media.

### 🛠️ Herramientas y Plantillas
*   [Plantilla Carga Precios Industrial](file:///c:/API/interno/docs/plantilla_carga_precios_industrial.csv): Plantilla CSV oficial para carga masiva de precios generales y acuerdos comerciales.

### 🛡️ Auditoría y Governance
*   [AUDITORIA_FRONTEND.md](file:///c:/API/interno/docs/audit/AUDITORIA_FRONTEND.md): Estado de calidad del cliente.
*   [Audit Reports](file:///c:/API/interno/docs/audit/): Directorio de hallazgos y saneamiento técnico.
*   [System Logs](file:///c:/API/interno/logs/): Archivos de salida y bitácoras de ejecución del sistema.

---

## 📂 MICROSERVICIOS (Backend Logs)
*   **Auth Service**: [SERVICE_LOG.md](file:///c:/API/interno/backend/auth_service/SERVICE_LOG.md) | [AWS Reference](file:///c:/API/interno/docs/infraestructura/aws_infrastructure_reference.md)
*   **WMS Service**: [ARCHITECTURAL_LOG.md](file:///c:/API/interno/docs/backend/wms_service/ARCHITECTURAL_LOG.md)
*   **Kiosk Service**: [SERVICE_LOG.md](file:///c:/API/interno/backend/kiosk_service/SERVICE_LOG.md)
*   **Subscription Service**: [README.md](file:///c:/API/interno/docs/backend/subscription_service/README.md)
*   **Master Data**: [AUDIT_SPECS.md](file:///c:/API/interno/docs/backend/master_data_service/AUDIT_SPECS.md)

---

## 🛡️ ESTÁNDARES & GOBERNANZA
*   **Protección de Datos**: Ver sección en [README.md](file:///c:/API/interno/README.md#gobernanza--reglas-de-oro).
*   **Zero Root Pollution**: Política de limpieza de raíz aplicada en la Fase 43.

---

## 📦 ARCHIVO HISTÓRICO (`docs/archive/`)
*   [Pricing Legacy](file:///c:/API/interno/docs/archive/pricing_logic.md): Lógica técnica heredada de precios.
*   [Profile](file:///c:/API/interno/docs/archive/Profile.txt): Registro de experiencia industrial.