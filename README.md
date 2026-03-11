# 🚀 INTERNO CORE - Master Documentation (SSOT)

> **Proxima Tarea:** [Plan para Mañana (04-Marzo)](file:///C:/Users/flore/.gemini/antigravity/brain/2c4d224a-9e9e-4bec-8850-fdc7b435580d/plan_tomorrow_2026_03_04.md)

> **Last Updated:** 2026-03-03
> **Status:** Active / Optimized

---

## 🏛️ 1. Arquitectura & Stack Tecnológico

InternoCore se rige por los principios de **Clean Architecture** y **CQRS**, asegurando un desacoplamiento total entre dominios y una escalabilidad horizontal en entornos híbridos (On-Premise / AWS).

- **Frontend:** Angular 19 (Signals, Reactive UI, Standalone Components).
- **Backend:** FastAPI (Python 3.12+) con SQLAlchemy Asíncrono (`asyncpg`).
- **Seguridad:** OAuth2/OIDC enriquecido con Claims de Suscripción y RBAC.
- **Persistencia:** PostgreSQL (Puerto `5433` en Docker).
- **Trazabilidad:** Motor de Auditoría Pro (SSOT) con `correlation_id`, snapshots de datos (JSONB), y contexto de red (IP/User-Agent) para cada mutación.

---

## 💎 2. Identidad Financiera (La Triada)

En Interno Core, el valor y la existencia de un producto no son propiedades globales simples. Todo precio, costo o saldo se rige por la relación jerárquica:

> **Producto + Empresa (company_id) + Almacén (warehouse_id)**

- **Alcance Granular:** Si el `warehouse_id` es `NULL`, el valor es un estándar "Global" para la empresa. Si tiene un ID, es específico para esa ubicación (reflejando variaciones por logística, fletes o costos operativos locales).

---

## 💰 3. Valuación y Precios (SSOT)

El sistema distingue y registra obligatoriamente cuatro valores financieros fundamentales para cada producto/almacén:

| Tipo de Valor | Responsabilidad | Afectación |
| :--- | :--- | :--- |
| **Landed Cost** | Costo de adquisición + Gastos (Flete/Aduana) | Entrada de Mercancía |
| **CPP** | Costo Promedio Ponderado (Valor Contable) | Inventory Snapshot |
| **Transfer Price** | Precio pactado para movimientos Inter-Company | Venta/Compra Interna |
| **Kitting Cost** | Suma de CPP de componentes + Gastos de Labor | Orden de Ensamble |

### 🛡️ Flujo de Excepción de Precios (Auditoría Forense)
El sistema no es permisivo para garantizar la integridad financiera:
1.  **Trigger:** Consulta de precio en WMS retorna `None`.
2.  **Acción 1:** Registro inmediato en `AuditLog` del WMS con el `transaction_id` activo.
3.  **Acción 2 (Alerta):** Petición automática al `tickets_service` (Puerto `8004`) para crear un ticket de prioridad **ALTA**.
4.  **Resultado:** El cliente recibe un `HTTP 400` con el mensaje: **"Configuración Pendiente: Precio no definido"**.

---

## 📡 4. Infraestructura y Mapa de Puertos

| Microservicio | Puerto | Responsabilidad Core |
| :--- | :--- | :--- |
| **Auth Service** | `8001` | Identidad, Handshake T1/T2, RBAC y Onboarding. |
| **Subscription** | `8000/8002` | Módulos activos, Entitlements y Licenciamiento. |
| **Master Data** | `8003` | SSOT de Productos, UOM, Categorías y Marcas. |
| **Tickets** | `8004` | Gestión de Incidencias y Alertas Automáticas (Puerto 8004). |
| **Inventory** | `8006` | Ledger inmutable, Saldos (Snapshot) y Kardex. |
| **WMS** | `8007` | Sales Flow, Pricing, Dispatch y Warehouse Mgmt. |
| **MES** | `8008` | Inteligencia Operacional, OEE y Captura en Piso. |

---

## 🆔 5. Protocolos de Identidad (Identidad Triple)

---

## 🔐 6. Flujo de Autenticación (Handshake T1/T2)

1.  **Paso 1 (Login - T1):** `POST /auth/login` -> Retorna `selection_token` + Lista de Compañías.
2.  **Paso 2 (Selección - T2):** `POST /auth/select-company` -> Valida token y retorna JWT final con `company_id`, `modules` y `roles`.
3.  **Aislamiento Zero-Trust:** El `BaseRepository` captura el `company_id` directamente del JWT verificado. No se permite la inyección de Tenant ID desde el cliente para operaciones de escritura (Previene IDOR).

---

## 🛡️ 7. Gobernanza y Desarrollo

- **Zero Root Pollution:** Prohibida la creación de archivos (.py, .env, .txt) en la raíz. Solo se permiten archivos maestros de documentación.
- **AuditBase:** Todas las entidades deben heredar de `AuditBase` (`created_at`, `updated_at`, `created_by`, `updated_by`, `transaction_id`).
- **Auditoría Automática:** El sistema registra automáticamente todos los cambios (CREATE, UPDATE, DELETE) en un `AuditLog` centralizado, garantizando trazabilidad forense por defecto.
- **Protección de Memoria:** **PROHIBIDO** eliminar archivos `.md` con prefijos `LOG` o `SPECS`. Son la memoria operativa del sistema.
- **Especificaciones Maestras:** Consulta las [Especificaciones de Auditoría Consolidadas](file:///C:/Users/flore/.gemini/antigravity/brain/2c4d224a-9e9e-4bec-8850-fdc7b435580d/audit_specifications_consolidated.md) para criterios de cumplimiento.

---

## 📜 8. Historial de Consolidación

- **Marzo 2026:** Unificación de `MANIFEST.md`, `REPO_LOG.md` y `GOVERNANCE.MD`. Estabilización de la Triada Financiera y el flujo de Excepciones de Negocio (Ticketing automático).
- **Febrero 2026:** Implementación del Handshake T1/T2 y consolidación de la capa Common multi-tenant.
