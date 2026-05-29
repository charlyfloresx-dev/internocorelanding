# 🚀 INTERNO CORE - Master Documentation (SSOT)

> **FASE ACTUAL:** `Fase 98 - Cloud Decommissioning & Unified Monolith Stabilization`
> **Last Updated:** 2026-05-12
> **Status:** ✅ PROD-READY (Local-First) / Infrastructure Extracted & Unified Monolith Operational

**Hitos Recientes:**
- ✅ **[2026-05-12] Phase 98 - Cloud Decommissioning:** Desmantelamiento total de AWS para alcanzar un estado de $0.00. Extracción del ADN técnico (VPC, IAM, OAC) y creación de la Guía de Resurrección para despliegues agnósticos en nuevas cuentas.
- ✅ **[2026-05-11] Phase 97 - Mobile Handshake:** Estabilización del handshake T1/T2 para la aplicación móvil (Flutter) mediante delegación de tokens Zero-Trust (QR).
- ✅ **[2026-05-10] Phase 96 - DB Integrity:** Limpieza forense de registros duplicados en `product_prices` y endurecimiento de la lógica de resolución de precios.

---

## 🏛️ 1. Arquitectura & Stack Tecnológico

InternoCore opera bajo una **Arquitectura Híbrida Evolutiva**:
- **Monolito Unificado (Modo Actual):** Para eficiencia de costos y simplicidad operativa local, los servicios corren bajo un orquestador unificado compartiendo red interna.
- **Microservicios Independientes (Cloud-Ready):** El código mantiene un desacoplamiento estricto (Bases de datos independientes y lógica aislada). Mediante los scripts de redespacho (`scripts/deploy_*`), cualquier módulo puede ser extraído y desplegado como un servicio independiente en AWS (ECS/App Runner) en minutos.

Principios: **Clean Architecture** y **CQRS**, asegurando un desacoplamiento total entre dominios y una escalabilidad horizontal en entornos híbridos (Local / Cloud).

- **Frontend:** Angular 19 (Signals, Reactive UI, Standalone Components).
- **Backend:** FastAPI (Python 3.12+) con SQLAlchemy Asíncrono (`asyncpg`).
- **Seguridad:** OAuth2/OIDC enriquecido con Claims de Suscripción y RBAC.
- **Persistencia:** PostgreSQL (Puerto `5433` en Docker).
- **Trazabilidad:** Motor de Auditoría Pro (SSOT) con `correlation_id`, snapshots de datos (JSONB), y contexto de red (IP/User-Agent) para cada mutación.

---

## 🏭 2. Propuesta de Valor — Los 4 Pilares Industriales

Mientras las empresas de manufactura tradicionales sufren integrando un ERP, un MES y un WMS de marcas distintas, **Interno Core unifica los tres** en una arquitectura multi-tenant nativa.

### 1. Núcleo de Planificación (ERP)
Interno Core asume el rol del ERP para la gestión del negocio a alto nivel:
- Estructura jerárquica multiempresa (acceso controlado por `company_id`).
- Catálogos maestros globales: proveedores, clientes, productos, monedas.
- Generación de Work Orders globales basadas en la demanda.

### 2. Núcleo de Ejecución en Planta (MES)
El módulo MES toma las Work Orders del ERP de forma nativa, sin integraciones propensas a fallos:
- **Monitoreo en piso:** Estaciones de trabajo (`Resource`), operadores y tiempos.
- **Captura rápida:** Integración con hardware industrial (QR/barcodes, terminales Zebra/Honeywell) para registrar avance de producción y Quality Inspection sin fricción.
- **Gráfica hora×hora:** `ResourceGraphicService` — portado del legacy .NET — calcula Meta/Real/Faltante/Excedente por turno en tiempo real.

> **Estrategia BOM/PLM:** No se implementa un módulo PLM propio (Teamcenter, Windchill, etc. son software masivo). En su lugar, Interno Core mantiene un maestro de **BOMs y Rutas de Producción** en el ERP/MES como combustible para las Work Orders. La arquitectura es abierta: si un cliente usa un PLM externo, puede inyectar la BOM directamente vía API. Ver deuda técnica: `Rout` model en MES.

### 3. Eslabón de Suministro (WMS / Inventarios)
El módulo WMS/Inventory gestiona el flujo de materiales entre ERP y MES:
- Existencias por almacén y empresa con aislamiento estricto de tenant.
- **Material Issuance:** surtido a líneas de producción con validación móvil en tiempo real.
- **Goods Receipt:** entrada de producto terminado desde MES con Density Guard.

### 4. Fuerza Laboral (HCM)
El módulo HCM conecta la gestión de personas directamente con el piso de planta:
- Turnos, roles, asistencia y habilidades de operadores vinculadas a `Resource`.
- Identidad física (RFID/PIN) para autorización en estaciones MES.
- Cross-Border Eligibility: validación de credenciales para despachos binacionales MX↔US.

### Flujo de datos integrado

```
[ Interno Core: ERP ] ──(Work Order multi-tenant)──► [ Interno Core: MES ]
        ▲                                                      │
        │ (Reporte de consumo e inventario terminado)          │ (Asignación a estación
        │                                                      │  + escaneo QR/Zebra)
        ▼                                                      ▼
[ Interno Core: WMS ] ◄────────────────────────────────────────┘
        ▲
        │ (Identidad física del operador autorizado)
[ Interno Core: HCM ]
```

Un cambio de estado en producción afecta al inventario y a la contabilidad de la empresa de forma **inmediata, segura y aislada por tenant**. Esta integración nativa elimina las fricciones que existen cuando el ERP, el MES y el WMS son de marcas distintas.

---

## 💎 3. Identidad Financiera (La Triada)

En Interno Core, el valor y la existencia de un producto no son propiedades globales simples. Todo precio, costo o saldo se rige por la relación jerárquica:

> **Producto + Empresa (company_id) + Almacén (warehouse_id)**

- **Alcance Granular:** Si el `warehouse_id` es `NULL`, el valor es un estándar "Global" para la empresa. Si tiene un ID, es específico para esa ubicación (reflejando variaciones por logística, fletes o costos operativos locales).

---

## 💰 4. Valuación y Precios (SSOT)

El sistema distingue y registra obligatoriamente cuatro valores financieros fundamentales para cada producto/almacén:

| Tipo de Valor | Responsabilidad | Afectación |
| :--- | :--- | :--- |
| **Landed Cost** | Costo de adquisición + Gastos (Flete/Aduana) | Entrada de Mercancía |
| **CPP / WAC** | Costo Promedio Ponderado (Valor Contable) | Inventory Snapshot |
| **Transfer Price** | Precio pactado para movimientos Inter-Company **sellado al despacho** | Venta interna de A → Costo de compra de B |
| **Kitting Cost** | Suma de CPP de componentes + Gastos de Labor | Orden de Ensamble |

### 🔄 Flujo de Precio Inter-Company (Transfer Price)

El `Transfer Price` es el **contrato financiero sellado** al momento que la Empresa A despacha:

| Campo | Empresa A (Origen) | Empresa B (Destino) |
|-------|--------------------|---------------------|
| `unit_price_at_dispatch` | Precio de venta a B | Costo de compra de A |
| `wac_at_dispatch` | Costo interno real | N/A |
| `transfer_revenue_a` | Ingreso interno = qty × price | N/A |
| `acquisition_cost_b` | N/A | Costo entrada = qty_recibida × price |
| `transfer_margin_a` | Margen = revenue_a − (qty × wac_a) | N/A |

**Resolución de precio (3 niveles de fallback):**
1. `EXPLICIT` — Precio provisto explícitamente por el despachador ✅
2. `WAC_FALLBACK` — No hay precio → usa WAC de A (vende a costo, sin margen) ⚠️
3. `DEFAULT_FALLBACK` — WAC=0 → usa $1.00 mínimo para proteger WAC de B 🚨

### 🛡️ Flujo de Excepción de Precios (Auditoría Forense)
El sistema no es permisivo para garantizar la integridad financiera:
1.  **Trigger:** Consulta de precio en WMS retorna `None`.
2.  **Acción 1:** Registro inmediato en `AuditLog` del WMS con el `transaction_id` activo.
3.  **Acción 2 (Alerta):** Petición automática al `tickets_service` (Puerto `8004`) para crear un ticket de prioridad **ALTA**.
4.  **Resultado:** El cliente recibe un `HTTP 400` con el mensaje: **"Configuración Pendiente: Precio no definido"**.

---

## 📡 5. Infraestructura y Mapa de Puertos

| Microservicio | Puerto | Responsabilidad Core |
| :--- | :--- | :--- |
| **Unified Monolith** | `8000` | Gateway Maestro, Agregación de Rutas y Orquestación. |
| **Auth Service** | `8001` | Identidad Central, Handshake T1/T2, Emisión y Rotación de JWT. |
| **Subscription** | `8002` | Módulos activos, Entitlements y Licenciamiento. |
| **Master Data** | `8003` | SSOT de Productos, UOM, Categorías y Marcas. |
| **HR Service** | `8004` | Motor de HCM, Identidad Física (RFID/PIN) y Escalaciones. |
| **Tickets** | `8005` | Gestión de Incidencias y Alertas Automáticas. |
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
4.  **God Mode:** Estado volátil de privilegio elevado para soporte técnico. Bloqueo físico (**Fail-Closed**) si no hay llave configurada. Trazabilidad forense obligatoria.

## 🏢 8. Estándar de Configuración Empresarial

Se ha definido un protocolo estricto para el alta y configuración de empresas en `docs/architecture/01_ARCHITECTURE.md`:
- **Identidad:** `CompanyID`, `CompanyStatus` y `CompanyAccessDto`.
- **Aislamiento:** Uso mandatorio de `MultiTenantBase` y Headers `X-Company-ID`.
- **Operación:** Vinculación estricta de Almacenes y Listas de Precios por Tenant.

---

## 🏗️ 9. Estándar de Construcción de Microservicios (Gold Standard)

Para garantizar consistencia, resiliencia y evitar colisiones en la base de datos unificada, TODO nuevo microservicio debe seguir esta topología estricta:

```text
backend/<module>_service/
├── Dockerfile          # Debe invocar entrypoint.sh vía CMD ["/bin/sh", "/app/entrypoint.sh"]
├── entrypoint.sh       # Secuencia obligatoria: Migrate -> Seed -> Serve
├── requirements.txt    # Dependencias aisladas del servicio
├── alembic.ini         # Configuración de migraciones
├── alembic/            
│   └── env.py          # CRÍTICO: Debe definir un 'version_table' único (ej. alembic_version_auth)
├── scripts/            
│   └── seed.py         # Opcional: Inyección de datos maestros
└── <module>_app/       # CRÍTICO: Nombrado explícito (No usar la palabra genérica 'app')
    ├── main.py         # Instancia FastAPI
    ├── core/           # Configuración (Pydantic Settings)
    ├── models/         # Modelos SQLAlchemy (Heredan de MultiTenantBase)
    ├── routers/        # Controladores API (Endpoints)
    ├── schemas/        # Validadores Pydantic (DTOs)
    └── services/       # Lógica de negocio pura
```
**Reglas de Oro:**
1. **Zero-Collision DB:** En modo Monolito Unificado (misma BD), cada servicio DEBE aislar su historial de Alembic usando `version_table="alembic_version_<suffix>"` en `env.py`.
2. **Auto-Bootstrap:** El contenedor debe ser 100% autónomo. Al arrancar, el `entrypoint.sh` se encarga de crear sus tablas y poblar sus catálogos base antes de exponer el puerto `8000`.

---

## 🛡️ 7. Gobernanza y Estructura
- **Ecosistema `src/`:** Carpeta central para aplicaciones satélite (Móvil, Kioscos, Trainers). Cada proyecto en `src/` debe ser una entidad independiente que consume las APIs del núcleo.
- **Seguridad Vault:** La carpeta `docs/infraestructura/vault/` es el único lugar permitido para credenciales sensibles. Está estrictamente excluida de Git.
- **Zero Root Pollution:** Prohibida la creación de archivos (.py, .env, .txt) en la raíz. Solo se permiten archivos maestros de documentación.
- **AuditBase:** Todas las entidades deben heredar de `AuditBase` (`created_at`, `updated_at`, `created_by`, `updated_by`, `transaction_id`).
- **Auditoría Automática:** El sistema registra automáticamente todos los cambios en un `AuditLog` centralizado.
- **Protección de Memoria:** **PROHIBIDO** eliminar archivos `.md` con prefijos `LOG` o `SPECS`. Son la memoria operativa del sistema.

---

## 📜 8. Historial de Consolidación

- **Abril 2026 (Phase 44):** Convergencia de Infraestructura & Media Assets. Implementación del `StorageProvider` universal (S3/LocalStorage) multi-tenant con URLs pre-firmadas. Migración deduplicada de secretos a AWS SSM Parameter Store vía LocalStack. Modernización del microservicio de RH para soporte de fotos de colaboradores con carga asíncrona y fail-safe. En el frontend, implementación de interceptores de normalización de activos y pipes de seguridad para visualización dinámica.
- **Abril 2026 (Phase 49):** Ecosistema de Handhelds Industriales & Compliance Outbound. Implementación del flujo de "Embarques" con validación de credenciales (Fase 50 Bridge). Estabilización de UI/UX táctil (Zebra/iPad) siguiendo el sistema de tokens "Surface" (Light/Dark mode dinámico). Integración de Auditoría Spot y generación de Audit Sheets (CSV) con Anexo 24. Acondicionamiento de flujos de Put-away y Entrada Manual para resiliencia offline.
- **Abril 2026 (Phase 46):** Escalabilidad Industrial y Cumplimiento Anexo 24. Implementación de paginación servidor-nativa y búsqueda global en el motor de inventarios para soportar catálogos de 10,000+ SKUs. Estabilización de la UI para dispositivos Handheld, resolución de errores de compilación ESBuild y estandarización del modelo de respuesta `ApiResponse` con metadatos de paginación industrial.
- **Abril 2026 (Phase 45):** Estabilización Industrial de Catálogos e Identidad. Rediseño del Pricing Matrix UI (Flexbox constraints) e implementación atómica en WMS para B2B. Sincronización del Single Source of Truth para Scopes entre Backend y Frontend (Roles Mapping dinámico). Refinamiento del Discovery-First Authentication y Zero-Trust Profile Resolving para entornos Kiosk.
- **Marzo 2026 (Phase 37):** Diseño y estabilización arquitectónica del **Módulo de Colaboradores (HCM)** alojado en `hr_service` (puerto `8004`). Introducción de _Identidad Física Distribuida_ mediante RFID (SHA-256) y PIN (Bcrypt). Integración del modelo `Phantom Link` (`collaborator_id` nulo) en el ledger inmutable de Inventarios.
- **Marzo 2026 (Phase 36.5):** Hardening de tokens en `auth_service` con política estricta de jerarquía (`typ` payload), rotación de `refresh_token` con persistencia _hash_ en BD para mitigación de Replay Attacks. Aprobación inmutable del patrón _Sealed Price_ para transferencias Intra-Compañia logrando retención financiera transparente.
- **Marzo 2026 (Phase 36):** Estabilización Multi-Tenant y Conectividad CORS. Homologación de IDs de empresas (`Enterprise`, `Logistics`, `Demo`) y estandarización de UUIDs de productos (v5) en todo el ecosistema. Creación del script `master_seed.py` para sembrado atómico multi-servicio. Resolución de bloqueos de preflight (OPTIONS) mediante configuración permisiva de CORS y expansión de headers permitidos (`X-Selection-Token`, `X-Trace-Id`).
- **Marzo 2026 (Phase 33):** Implementación del flujo Inter-Company Transfer (Trusted Broker). Arquitectura de 4 movimientos atómicos de Kardex garantizando integridad de inventario en transferencias cross-tenant. Transfer Price como contrato financiero sellado: `unit_price_at_dispatch` (precio de venta de A = costo de compra de B), `wac_at_dispatch`, `transfer_revenue_a`, `acquisition_cost_b`. 6 endpoints RESTful bajo `/api/v1/inventory/transfers/inter-company`. Seguridad Zero-Trust por capas en recepción.
- **Marzo 2026 (Phase 32):** Estabilización del Dashboard Mission Control con datos de alta fidelidad y trazabilidad forense. Unificación de `MANIFEST.md`, `REPO_LOG.md` y `GOVERNANCE.MD`. Implementación de la Triada Financiera y el flujo de Excepciones de Negocio (Ticketing automático). Hardening de seguridad en middleware y corrección de bug crítico en ruta `/admin/`.
- **Febrero 2026:** Implementación del Handshake T1/T2 y consolidación de la capa Common multi-tenant.
