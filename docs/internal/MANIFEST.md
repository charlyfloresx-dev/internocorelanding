# 📦 INTERNO CORE - REPOSITORY MANIFEST (High-Fidelity SSOT)

> **Status:** Active / SSOT Absolute
> **Last Updated:** 2026-03-03
> **Objective:** Control centralizado de todos los activos, reglas y servicios del repositorio InternoCore.

---

## ✅ ARCHIVOS ACTIVOS & SSOT (Estructura de Documentos)

### 📂 Raíz (Portal de Entrada)
*   [README.md](file:///c:/API/interno/README.md): **Portal Maestro**. Contiene la visión técnica, tabla de precios, flujo de excepciones y mapa de navegación rápido.
*   [REPO_LOG.md](file:///c:/API/interno/REPO_LOG.md): **Memoria Histórica**. Bitácora detallada de fases, microservicios y decisiones de arquitectura (SSOT cronológico).

### 📂 Auditoría y Logs (`docs/audit/`)
* [phase5_final_logs.md](file:///c:/API/interno/docs/audit/phase5_final_logs.md): Reporte final de integridad de la Fase 5.
* [code_graph.json](file:///c:/API/interno/docs/audit/code_graph.json): Mapa de dependencias del sistema tras la limpieza de raíz.

### 📂 Especificaciones Técnicas (`docs/technical/`)
* [GOD_MODE_GUIDE.md](file:///c:/API/interno/docs/technical/GOD_MODE_GUIDE.md): Protocolo de uso de la `INT_ADMIN_MASTER_KEY`.
* [INVENTORY_FLOW.md](file:///c:/API/interno/docs/technical/INVENTORY_FLOW.md): (Nuevo) Flujo de transacciones inmutables del Kardex.

### 📂 Backend Service Logs (`docs/backend/`)
Cada microservicio mantiene su propio rastro técnico detallado:
- **🔐 Auth**: [SERVICE_LOG.md](file:///c:/API/interno/backend/auth_service/SERVICE_LOG.md)
- **📦 WMS**: [ARCHITECTURAL_LOG.md](file:///c:/API/interno/backend/wms_service/ARCHITECTURAL_LOG.md)
- **💳 Subscription**: [README.md](file:///c:/API/interno/backend/subscription_service/README.md)
- **🏭 MES**: [SERVICE_LOG.md](file:///c:/API/interno/backend/mes_service/SERVICE_LOG.md)
- **🗂️ Master Data**: [SERVICE_LOG.md](file:///c:/API/interno/backend/master_data_service/SERVICE_LOG.md)
- **🎫 Tickets**: [README.md](file:///c:/API/interno/backend/tickets_service/README.md)
- **Inventory**: [README.md](file:///c:/API/interno/backend/inventory_service/README.md)

---

## 🕋 MAPA DE PUERTOS & SERVICIOS (Ecosistema Docker)

| Servicio | Puerto | Build Context | Responsabilidad |
| :--- | :--- | :--- | :--- |
| **Auth** | `8000` | `/backend` | Identidad, Tenants, JWT Handshake T1/T2. |
| **Subscription** | `8002` | `/backend` | Licenciamiento, Entitlements y Planes. |
| **Master Data** | `8003` | `/backend` | Catálogos Globales (Productos, UOM, Marcas). |
| **Tickets** | `8004` | `/backend` | Incidencias, Soporte y Alerta de Precios. |
| **Inventory** | `8006` | Ledger de existencias e inmutabilidad (Kardex). |
| **WMS** | `8007` | Operaciones logísticas avanzadas. |
| **MES** | `8008` | Manufactura, OEE, Downtime Tracker. |

---

## 🛡️ GOBERNANZA & REGLAS DE ORO

1.  **Zero Root Pollution**: Prohibida la creación de archivos `.py`, `.md` o temporales en la raíz. Todo debe residir en `backend/`, `frontend/` o `docs/`.
2.  **Identidad Triple**: Todo documento financiero u operativo DEBE tener `id` (UUID), `sequence_number` (Int) y `folio` (Str).
3.  **Protección de Memoria**: Los archivos con sufijo `LOG` o `SPECS` son intocables; su historial no debe truncarse ni simplificarse.
4.  **Zero Trust Tenancy**: El `company_id` se extrae exclusivamente del JWT. No se confía en parámetros de URL o payloads del cliente para filtrado de seguridad.

---

## ⛔ ARCHIVO & LEGADO
- Toda la documentación .NET y archivos históricos previos a la migración FastAPI residen en `docs/archive/`.
- [WMS_PRICING_LOGIC.md](file:///c:/API/interno/docs/archive/pricing_logic.md): Referencia técnica específica sobre la lógica de costos (Landed, CPP, etc).