# 📦 INTERNO CORE - REPOSITORY MANIFEST

> **Status:** Active
> **Last Updated:** 2026-02-18

## ✅ ARCHIVOS ACTIVOS (SSOT)
Estos archivos representan la verdad actual del proyecto y deben ser consultados para desarrollo.

### Documentación Maestra (`docs/`)
*   `REPO_LOG.md`: (Raíz) Bitácora oficial de cambios y evolución del repositorio.
*   `00_MASTER_INDEX.md`: Índice Maestro y punto de entrada.
*   `01_ARCHITECTURE.md`: Arquitectura, Stack y Estrategia Híbrida.
*   `02_BACKEND_DEPLOYMENT.md`: Despliegue AWS, Auth Service y DR.
*   `PHASE_SPECS.md`: Especificaciones técnicas de fases pendientes.
*   `MES_CORE.md`: Definiciones del módulo MES.
*   `ARCHITECTURAL_LOG.md`: Registro de decisiones de arquitectura.

### Documentación Técnica (`docs/technical/`)
*   `FRONTEND_CONTEXT.md`: Guía de desarrollo Frontend (Angular 19).
*   `ENGINEERING_LOG.md`: Bitácora de ingeniería Frontend.

### Archivos Históricos (`docs/archive/`)
*   `Profile.txt`: Contexto de negocio original.
*   `INTERNAL_CLEANUP_LOG.md`: Registro de limpieza y normalización.

---

## 🕋 CÓDIGO FUENTE (BACKEND)
*   `backend/common/`: Librería compartida (Modelos base, Schemas, Middlewares).
*   `backend/auth_service/`: Microservicio de Autenticación y OIDC.
*   `backend/master_data_service/`: Microservicio de Datos Maestros (Productos, UOM, Categorías).
*   `backend/wms_service/`: Microservicio de Warehouse Management System.
*   `backend/mes_service/`: Microservicio de Manufacturing Execution System.
*   `backend/billing_service/`: Microservicio de Facturación, Notas de Crédito y Pagos.

## 📂 SERVICE DOCUMENTATION MAP (Anti-Hallucination)
*Regla Estricta:* Antes de modificar un servicio, se debe consultar su bitácora específica.

### 🔐 Auth Service
- **Contexto Técnico:** `backend/auth_service/CONTEXTO.md`
- **Bitácora de Cambios:** `backend/auth_service/SERVICE_LOG.md`
- **Historial de Versiones:** `backend/auth_service/CHANGELOG.md`
- **Estado Frontend:** ✅ **Estable (Final T2 Flow).** `auth.service.ts` y `auth.interceptor.ts`.

### 📦 Master Data Service
- **Contexto Técnico:** `backend/master_data_service/docs/CONTEXTO.md`
- **Estatus de Auditoría:** `ARCHITECTURAL_LOG.md#Phase19`

### 💳 Billing Service
- **Contexto Técnico:** `backend/billing_service/docs/CONTEXTO.md`
- **Bitácora de Cambios:** `backend/billing_service/SERVICE_LOG.md`
- **Modelos:** `Invoice`, `InvoiceItem`, `CreditNote`, `PaymentTerm`, `Payment`
- **Puerto:** `8001`

---

## ⛔ OBSOLETOS / IGNORAR
Estos archivos se mantienen solo por referencia histórica. **NO UTILIZAR** para nuevas implementaciones.

*   `TECH_STACK_RECOMMENDATION.md` (Reemplazado por `01_ARCHITECTURE.md`)
*   `TECH_STACK_RECOMMENDATION_INTERNOCORE.md` (Reemplazado por `01_ARCHITECTURE.md`)
*   `CONTEXT_UNIFICATION.md` (Integrado en `00_MASTER_INDEX.md` y `01_ARCHITECTURE.md`)
*   `AWS_Deployment_Strategy.md` (Reemplazado por `02_BACKEND_DEPLOYMENT.md`)
*   `DR_Manual_Auth_Microservice.md` (Reemplazado por `02_BACKEND_DEPLOYMENT.md`)


## 🏗️ ESTÁNDAR DE CREACIÓN DE MICROSERVICIOS

Para evitar la generación de archivos huérfanos en la raíz y mantener la Clean Architecture, todo nuevo microservicio DEBE seguir estrictamente estas reglas:

### 1. Ubicación y Prohibición de Raíz
- **PROHIBICIÓN:** No se permite crear archivos de lógica (.py), configuraciones (.env, .txt) o documentación técnica en la raíz del repositorio (`/`) ni en la raíz de `/backend`.
- **UBICACIÓN:** Todo nuevo servicio debe residir en `/backend/[nombre_del_servicio]_service/`.

### 2. Estructura Interna Obligatoria
Cada microservicio debe replicar exactamente la siguiente jerarquía de carpetas:

/backend/[servicio]_service/
├── alembic/                # Migraciones de base de datos
│   └── versions/           # Scripts de migración (UUID asíncronos)
├── app/
│   ├── api/v1/endpoints/   # Controladores y rutas FastAPI
│   ├── core/               # Enums, constantes y config específica
│   ├── models/             # Entidades SQLAlchemy (heredan de MultiTenantBase)
│   ├── services/           # Lógica de negocio y CQRS
│   ├── infrastructure/     # Database.py y clientes externos
│   ├── dependencies.py     # Inyección de dependencias (Auth/DB)
│   └── main.py             # Punto de entrada de la aplicación
├── Dockerfile              # Configuración multi-stage (Copia /common)
├── requirements.txt        # Dependencias específicas del servicio
└── README.md               # Documentación local del servicio

### 3. Reglas de Implementación para el Agente
- **Herencia de Tenancy:** Todos los modelos DEBEN importar y heredar de `common.models.MultiTenantBase`. El campo `company_id` es obligatorio.
- **Imports:** Usar siempre rutas relativas al paquete `app` (ej. `from app.models.product import Product`).
- **Contexto Global:** Para resolver imports de la carpeta `/common`, el Dockerfile debe configurar `ENV PYTHONPATH=/app` y el contexto de build debe ser la raíz `/backend`.
- **Respuestas:** Todas las respuestas de la API deben usar el esquema `ApiResponse` de `common.schemas`.
- **Internacionalización (i18n):** Todo modelo de catálogo o maestro debe incluir el campo `translation_key`. Los Enums en `common` deben implementar la propiedad `@property translation_key`.
- **Catálogos Híbridos:** Los maestros deben permitir `company_id` como `NULL` para registros globales y usar la lógica de consulta OR (`company_id IS NULL`, `company_id = :id`).

### 4. Reglas de Documentación (Zero Root Pollution)
- **UBICACIÓN:** Toda documentación nueva (.md, .txt, diagramas) DEBE ir en `docs/` o `docs/technical/`.
- **EXCEPCIONES:** Solo `README.md`, `MANIFEST.md` y `REPO_LOG.md` pueden existir en la raíz.
- **ACCIÓN CORRECTIVA:** Si un archivo `.py` aparece en la raíz (`C:\API\interno\`), debe ser eliminado inmediatamente y movido a la carpeta del servicio correspondiente.
- **REPORTING:** Los agentes o desarrolladores deben reportar cambios de archivos usando rutas absolutas.