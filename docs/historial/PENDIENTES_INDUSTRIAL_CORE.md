# 🚩 Pendientes Activos: InternoCore Industrial

> [!IMPORTANT]
> **RECORDATORIO**: El usuario necesita reiniciar el ordenador. Al retomar, priorizar el mazo de **Put-away** para cerrar el ciclo operativo de almacén.

Este documento centraliza los bloqueos y tareas críticas para el núcleo industrial, ignorando el ecosistema de eventos.

## 🏭 MES Cold-Start: Configuración Inicial Completa (Phase 156 Plan)

> **Por qué:** `ResourceMonitorComponent` ya consume la API real, pero el monitor muestra "Sin datos" porque `mes_db` está vacía de configuración operacional. Se necesitan 4 capas de datos antes de que la gráfica hora×hora tenga algo que mostrar.

### Capas de Datos (orden obligatorio)

```
Capa 1 — Infraestructura Física (admin, setup único)
  Facility → ProductionArea → Resource (+ warehouse_id soft FK)
  Shift + ShiftBreak

Capa 2 — Planificación Diaria (supervisor, cada turno)
  WorkOrder (desde ERP) → ProductionRun (WO + Resource + Shift + Date)

Capa 3 — Tiempo Estándar (ing. industrial, por ítem)
  StandardTime (item_code, set_time_hours) — habilita goal exacto vs fallback

Capa 4 — Datos en tiempo real (automático, por scanner)
  HourlyProductionSnapshot → actualizado por ScannerService
  ManufacturingLedger → scan entries inmutables
```

---

### Parte A — Seed de Configuración MES (`seed_mes_config.py`) ← CREAR

**Archivo:** `backend/mes_service/scripts/seed_mes_config.py`
Usar UUIDs deterministas `uuid.uuid5(NAMESPACE_DNS, ...)` alineados con `unified_industrial_seed.py`.

| Entidad | Registros a crear |
|---|---|
| `Facility` | 1 por empresa (3 total): "Planta Tijuana" (ENT), "Planta TJ Logística" (MX), "Plant San Diego" (US) |
| `ProductionArea` | 3 por empresa: "Líneas de Ensamble", "Área de Calidad", "Almacén WIP" |
| `Resource` | 4 por empresa: `CELDA-58D`, `CELDA-59A`, `TURRET-01`, `PRENSA-01` — resource_type: CELL/CELL/MACHINE/MACHINE |
| `Shift` | 3 por empresa (sin resource_id = company-wide): Matutino 06:00-14:00, Vespertino 14:00-22:00, Nocturno 22:00-06:00 |
| `ShiftBreak` | 2 por turno: Primer descanso (30 min), Comida (30 min) con horarios reales |
| `StandardTime` | 5 por empresa — ítems de los productos del seed (set_time_hours calculados del legacy) |

**Cómo integrar al stack:**
Agregar llamada en `entrypoint.sh` del mes_service O como step separado en `migrate_all.ps1`.

---

### Parte B — Admin Angular: CRUD de Configuración MES ← CREAR

**Ruta propuesta:** `/production/config` (ya existe `/production/item-config` como patrón)

Componentes a crear:

| Componente | Ruta | Endpoints backend |
|---|---|---|
| `FacilityConfigComponent` | `/production/config/facilities` | `GET/POST /mes/facilities`, `PATCH /mes/facilities/{id}` |
| `ProductionAreaConfigComponent` | `/production/config/areas` | `GET/POST /mes/production-areas` |
| `ResourceConfigComponent` | `/production/config/resources` | `GET/POST/PATCH /mes/resources/{code}` |
| `ShiftConfigComponent` | `/production/config/shifts` | `GET/POST/PATCH /mes/shifts` (endpoint faltante — ver Parte C) |
| `ShiftBreakConfigComponent` | Dentro de ShiftConfig | `GET/POST /mes/shifts/{id}/breaks` (faltante — ver Parte C) |
| `StandardTimeConfigComponent` | `/production/item-config` | Ya existe parcialmente (scan patterns), extender |

**Patrón de diseño:** seguir `MesItemConfigComponent` — campo de búsqueda + tabla de resultados + formulario lateral.

---

### Parte C — Backend MES: Endpoints faltantes ← CREAR

Los modelos `Shift` y `ShiftBreak` existen en DB pero no tienen endpoints HTTP expuestos:

```
GET  /api/v1/mes/shifts                         → lista turnos activos de la empresa
POST /api/v1/mes/shifts                         → crear turno
PATCH /api/v1/mes/shifts/{id}                   → editar turno (start/end/name)
DELETE /api/v1/mes/shifts/{id}                  → desactivar

GET  /api/v1/mes/shifts/{shift_id}/breaks       → lista descansos del turno
POST /api/v1/mes/shifts/{shift_id}/breaks       → crear descanso
DELETE /api/v1/mes/shifts/{shift_id}/breaks/{id} → eliminar descanso

GET  /api/v1/mes/standard-times                 → lista por empresa
POST /api/v1/mes/standard-times                 → crear (item_code, operation_name, set_time_hours)
DELETE /api/v1/mes/standard-times/{id}          → eliminar
```

---

### Parte D — Planificación Diaria: WorkOrder + ProductionRun UI ← CREAR

Para que el graphic tenga datos, supervisor debe poder:
1. Crear/importar `WorkOrder` (order_number, item_code, order_quantity, due_date)
2. Asignar a un recurso y turno como `ProductionRun` para la fecha de hoy

**Endpoints ya existen** (`/mes/work-orders`, `/mes/production-runs` — verificar).
**UI pendiente:**
- `WorkOrderFormComponent` — formulario de creación rápida de WO
- `DailyPlanningComponent` — arrastrar WO a un recurso/turno para el día (tabla Gantt simple)

---

### Checkboxes de seguimiento Phase 156

- [x] **A.1** `seed_mes_config.py`: Facility + ProductionArea + Resource + Shift + ShiftBreak ✅ Phase 156-A (2026-05-29)
- [x] **A.2** Integrar `seed_mes_config.py` en `entrypoint.sh` via `scripts/seed.py` ✅ Phase 156-A
- [x] **A.3** `unified_industrial_seed.py` no llama MES directamente; `entrypoint.sh` del contenedor lo hace ✅
- [x] **B.1** `ResourceConfigComponent` (`/production/config/resources`) + `ResourceFormComponent` (drawer) + CSV bulk ✅ Phase 156-B
- [x] **B.2** `ShiftConfigComponent` (`/production/config/shifts`) + `ShiftFormComponent` con breaks inline ✅ Phase 156-B
- [x] **B.3** `ProductionAreaFormComponent` — Facilidades + Áreas vía drawer "Áreas/Plantas" ✅ Phase 156-B (2026-05-29)
- [x] **C.1** Endpoints REST Shift: GET/POST/PATCH/DELETE + ShiftBreak sub-resource ✅ Phase 156-C
- [ ] **C.2** Endpoints REST para `StandardTime` — CRUD completo (seed existe, falta UI + endpoints)
- [x] **D.1** `WorkOrderFormComponent` + `DailyPlanningComponent` (`/production/planning`) ✅ Phase 156-D
- [x] **D.2** `POST /mes/planning/runs` corregido (field bugs, tenant_id, new GET+DELETE) ✅ Phase 156-D
- [x] **D.3** Flujo de surtido de material separado — `POST /mes/orders/{n}/issue-material` ✅ Phase 156-D (2026-05-29)
- [x] **D.4** WO types catalog desde API (`GET /mes/orders/types`) — no hardcodeado ✅ Phase 156-D

---

## 🆕 Phase 157 — Pendientes Descubiertos en Phase 156 (2026-05-29)

### Alta Prioridad

| Item | Descripción |
|---|---|
| **HCM BreakGroups** | Grupos de descanso basados en capacidad de áreas comunes (baños, cafetería). Pertenecen a HCM, no a MES. `Resource.break_group_id` soft FK ya existe. Requiere: entidad `BreakGroup` en HCM + endpoint `/hcm/break-groups` + `ResourceGraphicService` consume HCM vía HTTP cuando `break_group_id != NULL` |
| **StandardTime CRUD** | Endpoints REST `GET/POST/DELETE /mes/standard-times` + `StandardTimeFormComponent` (drawer) integrado en `MesItemConfigComponent` |
| **Material Badge en Monitor** | `ResourceMonitorComponent` debe mostrar badge "⚠️ Material sin surtir" si la WO activa tiene `material_status=PENDING_ISSUE` |
| **Menú: agregar link Planificación** | `navigation.service.ts` tiene `prod-planning` → `/production/planning` pero falta verificar que el icono `assignment` esté disponible en Material Icons |

### Media Prioridad

| Item | Descripción |
|---|---|
| **WO bulk import CSV** | Equivalente al bulk de recursos pero para WOs — `WorkOrderBulkFormComponent` para importar desde ERP |
| **DailyPlanning — mini Gantt** | Visualización tipo Gantt horizontal por recurso/turno (actualmente tabla plana) |
| **StandardTime import Excel** | Bulk load de tiempos estándar desde Excel (deuda técnica ya registrada en CLAUDE.md) |
| **`.github/agents/*.agent.md`** | Archivos de agentes en `.github/agents/` referencian "NexoSuite" (nombre antiguo). Actualizar a "InternoCore" |
| **Validar checkout POS** | `POST /api/v1/pos/checkout` — validación end-to-end con flows de prueba |

---

## 🏭 Phase 154 — Monitor de Recurso: MES ↔ Frontend (PENDIENTE)

> **Contexto:** `ResourceMonitorComponent` (`/monitor/resources`) tiene UI completa pero **100% hardcodeada** en signals estáticos. El `mes_service` ya corre en puerto 8005 y está expuesto por Nginx. Necesita conectarse.

### Decisión arquitectónica clave (del legacy `Resource.cs`)
En el .NET legacy `Resource : Warehouse` — un recurso de producción **hereda directamente** de Almacén, compartiendo `Code (PK, max 13)`, `Name`, `Description`, `Type/TypeId`, `Capacity`, `Unit`, `Group`, `Active`. El recurso agrega `BreakGroupId` y `ProductionArea`.

En Python (multi-servicio), no podemos herencia cross-service. **Decisión**: `Resource` en `mes_service` tendrá `warehouse_id: Optional[UUID]` como soft FK hacia `inventory_service.warehouses` — sin FK de BD (Iron Wall). El `code` permanece como la clave de negocio (ej. `CELDA-58D`).

### Jerarquía del dominio (portada del legacy)
```
Facility  (planta física: código, nombre, ubicación)
  └── ProductionArea  (zona dentro de la planta — hereda de HumanResource.Area)
       └── Resource  (celda/máquina/línea — hereda Warehouse en legacy, soft-FK en Python)
            ├── BreakGroup → Breaks[]  (horarios de descanso del turno)
            └── Result (sesión de producción del día: shift + date + WOs)
                 ├── HourByHour[]  (→ HourlyProductionSnapshot en Python)
                 ├── Labor[]
                 ├── Downtime[]
                 └── Tracking[]
```

### Parte 1 — Backend MES: Modelos + Migrations
**Archivos a crear en `backend/mes_service/mes_app/models/`:**

- **`facility.py`** — `Facility(MultiTenantBase)`: `code VARCHAR(25)`, `name VARCHAR(100)`, `location_description VARCHAR(250) NULL`
- **`production_area.py`** — `ProductionArea(MultiTenantBase)`: `name VARCHAR(100)`, `description VARCHAR(250) NULL`, `facility_id UUID FK → facilities`
- **`resource.py`** — `Resource(MultiTenantBase)`:
  ```python
  code: Mapped[str]          # max 13 chars — clave de negocio (ej. "CELDA-58D")
  name: Mapped[str]          # max 100
  description: Mapped[Optional[str]]
  resource_type: Mapped[str] # CELL | MACHINE | AREA | LINE  (Enum)
  capacity: Mapped[Optional[Decimal]]
  warehouse_id: Mapped[Optional[uuid.UUID]]  # soft FK → inventory_service.warehouses (NO FK BD)
  production_area_id: Mapped[Optional[uuid.UUID]]  # FK → production_areas
  is_active: Mapped[bool] = True
  # UniqueConstraint("company_id", "code")
  ```
- **`resource_support_member.py`** — tabla pivote: `resource_id`, `collaborator_id` (soft FK → hcm_service), `role VARCHAR(50)` — alimenta sección "Equipo de Soporte"

- Migration Alembic: `add_facility_production_area_resource`
- Seed: `CELDA-58D`, `CELDA-59A`, `TURRET-01`, `AREA-PRENSA` vinculados a facilities/areas demo

**Endpoints `backend/mes_service/mes_app/api/v1/endpoints/resources.py`:**
- `GET /api/v1/mes/resources` — lista activos de la empresa (scope `mes:read`)
- `GET /api/v1/mes/resources/{code}` — detalle + turno activo + breaks + equipo soporte
- `POST /api/v1/mes/resources` + `PATCH /api/v1/mes/resources/{code}` (scope `mes:write`)

### Parte 2 — Backend MES: Gráfica Hora × Hora (el "algoritmo ~120L" del legacy)
El algoritmo vive en `ResultController.GetGraphic()` del legacy. Portado a Python:

**`GET /api/v1/mes/resources/{code}/graphic`** — responde `ResourceGraphicResponse`:
```python
# Paso 1: Detectar turno activo (6h-17h → turno 1, resto → turno 2)
# Paso 2: Generar slots horarios [shift.start .. shift.end]
#          Disponible[i] = 1.0  (hora completa disponible)
# Paso 3: Aplicar breaks → reducir Disponible[i] en horas con descanso
#          break inicia en slot i → Disponible[i] = break.start - slot_hour
#          break termina en slot i → Disponible[i] = next_slot - break.end
# Paso 4: Para cada WO del día ordenada por priority:
#          qtyPerHour = floor(disponible_i / operationTime.set_time)  [si hay OperationTime]
#                     = round(plan_qty / total_horas_necesarias)       [fallback]
#          Meta[i] = qtyPerHour; Faltante[i] = qtyPerHour
# Paso 5: Cargar HourlyProductionSnapshot de hoy → agrupar por hora
#          Si actual > meta → Excedente[i] = actual - meta; Faltante[i] = 0
#          Si actual < meta → Faltante[i] = meta - actual; Producidas[i] = actual
# Paso 6: Eficiencia[i] = ceil((Producidas[i] * 100) / Meta[i])
```
Retorna: `{hours[], meta[], actual[], missing[], excess[], efficiency[], breaks[], cumulative_table[]}`

**Endpoints adicionales en el mismo archivo:**
- `GET /api/v1/mes/resources/{code}/active-workorder` → WO con `status=IN_PROGRESS` para la celda
- `GET /api/v1/mes/resources/{code}/planned-workorders` → WOs del turno (`status IN [DRAFT, IN_PROGRESS]`)

### Parte 3 — Frontend Angular: ResourceService + Desconexión del Mock
**Archivos a crear/modificar:**
- `frontend/src/app/core/services/resource.service.ts`:
  - `loadResource(code)` → `GET /mes/api/v1/resources/{code}`
  - `loadGraphic(code)` → `GET /mes/api/v1/resources/{code}/graphic` (reemplaza `productionData` + `tableData`)
  - `loadActiveWorkOrder(code)` → `GET /mes/api/v1/resources/{code}/active-workorder`
  - `loadPlannedWorkOrders(code)` → `GET /mes/api/v1/resources/{code}/planned-workorders`
- `resource-monitor.component.ts` — refactor completo:
  - Añadir `ActivatedRoute` → parámetro `:code`
  - Reemplazar los 3 signals hardcodeados por signals del service
  - Loading skeleton states
  - Andon → binding a `resource.is_active`
  - Botón "Incidencia" → `TicketsNewModalComponent` pre-poblado con `resource_code`
- `app.routes.ts`: `/monitor/resources` → `/monitor/resources/:code`
- Nuevo `ResourceSelectorComponent` — lista de recursos activos para navegar a `/monitor/resources/:code`

### Parte 4 — Nginx (verificación)
- Confirmar upstream `mes-service` en `nginx.conf` apunta al nombre de contenedor correcto (puerto interno 8000, no host 8005)

### Checkboxes de seguimiento Phase 154 ✅ COMPLETADO
- [x] Parte 1: `Facility` + `ProductionArea` + `Resource` + migration 009 + CRUD endpoints (commit `b9c2f05`)
- [x] Parte 2: `ResourceGraphicService` + `/graphic` + `/active-workorder` + `/planned-workorders` (commit `76c6488`)
- [x] Parte 3: `ResourceService` Angular + `ResourceSelectorComponent` + mock desconectado + `:code` param (commit `ebe5bfa`)
- [ ] Parte 4 → **Phase 156** MES Cold-Start: seed config + Admin UI + endpoints Shift/StandardTime (ver sección arriba)

---

## 🛠️ Microservicios & Lógica de Negocio
- [ ] **Tickets Service (CRÍTICO)**: Incrementar cobertura de tests del 0% a al menos 70%. Es el motor de escalación meso-ERP.
- [ ] **Help Desk (Tickets)**: Esqueleto presente, pero nula lógica de escalaciones.
- [x] **Logística (WMS/Inventory)**: Trasladada madurez de Catalog/Prices a Handhelds (Inbound/Picking). Implementado soporte Offline y Visibilidad Financiera.
- [ ] **WMS ICT Validation**: Pruebas de carga para transferencias atómicas entre empresas (Inter-Company Transfers) en entornos de red inestable.
- [ ] **Viatra Grace Period**: Implementar el periodo de gracia de 48h para suscripciones con pago fallido (Sync con Stripe).
- [ ] **Frontend Search Protocool**: Asegurar que todos los buscadores de productos implementen el patrón RxJS `debounceTime(300)` + `switchMap`.
- [ ] **Dashboard de Márgenes (FINANCIERO)**: Crear vista de análisis que compare Nivel 0 (Compra) vs Niveles 1-10 (Venta) para alertar sobre rentabilidad negativa.
- [ ] **Engine Point-in-Time**: Implementar helper en el backend para recuperar el precio histórico exacto basado en la fecha del documento (Inmutabilidad).
- [ ] **Handshake de Inventarios**: Validar que el flujo de venta descuente stock usando el `price_id` de la versión inmutable activa.

## 📦 WMS Inbound & Outbound Handheld (Industrial Integrity)
- [x] **Cycle Count (Spot Audit)**: Implementado flujo de conteo ciego (Blind Count) con reconciliación automática. Componente `CycleCountComponent` con 3 pasos (Scan Location → Blind Count → Discrepancy Analysis).
- [x] **Audit Sheet Export**: Generador CSV de hojas de conteo técnico con Anexo 24 (Ubicación/SKU/Pedimento/Cantidad Teórica + columna de conteo manual).
- [x] **Put-Away Handheld & Entrada Manual**: Actualizados estilos dinámicos de colores para `surface-bg`. Flujo implementado: Escaneo en Rampa -> Escaneo en Rack -> Confirmación.
- [x] **Picking & Embarques Handheld (Outbound)**: Implementado componente `inventory-shipping` para despacho. **Incluye la validación crítica de Gafete del Operador** como paso hacia HR Service (Fase 50).
- [ ] **Density Guard V2**: Extender la validación de capacidad para incluir volumen (m3) además de piezas.
- [ ] **Inter-Company Stress Test**: Validar transferencias masivas entre MX y US bajo carga de red simulada (Fase 48).

## 🧬 Estrategia BOM / PLM (Decisión Arquitectónica)

> **Decisión:** No implementar un módulo PLM propio. Concentrar esfuerzo en BOM + Rutas de Producción dentro del ERP/MES.

- **Fase actual (simplificada):** Maestro de BOMs (`inventory_service` — tablas `bom`, `bom_lines`) + Rutas de Producción (`mes_service` — tabla `mes_routings`, actualmente `routing.py` vacío).
- **Fase futura (API abierta):** Si un cliente usa Teamcenter, Windchill o Fusion 360, puede inyectar la BOM directamente a `POST /api/v1/inventory/bom` sin que Interno Core tenga que reimplementar el PLM.
- **Por qué no un PLM propio:** PLM = software masivo y muy específico de industria. La propuesta de valor de Interno Core es la integración ERP+MES+WMS+HCM, no el diseño de producto.
- [ ] **Pendiente:** Implementar `Rout` model en MES (actualmente `routing.py` vacío) para cerrar el ciclo BOM → WorkOrder → Ruta de Producción.
- [ ] **Pendiente:** Endpoint `POST /inventory/bom` de bulk-import para ingesta desde PLM externo vía API.

---

## 🏛️ Arquitectura & Documentación
- [ ] **Diagramas C4**: Actualizar diagramas de contenedores para reflejar el estándar de prefijo `CORE_`.
- [ ] **API Reference**: Generar documentación OpenAPI unificada en el portal `DOCS_INTERNOCORE.html`.
- [x] **Registry de Catálogos (Performance)**: Implementado Cache Map (SKU -> UI Metadata) en Frontend para reducción de latencia (Registry Cache).
- [ ] **Industrial UX Optimization**: Implementar CDK Virtual Scroll para listas masivas (>100 items).

## 👤 HR Service (Gestión de Colaboradores)
- [ ] **Modelo de Colaborador (hr_service)**: Crear entidad `Collaborator` con campos de identidad industrial: nombre, puesto, planta asignada, turno.
- [ ] **Cross-Border Despacho (Credenciales Binacionales)**: Integrar atributos `visa_number`, `sentry_id`, `global_entry_id`, `visa_expiry` al perfil del colaborador. Estos datos son prerequisito para autorizar embarques internacionales MX↔US. *(Hallazgo del análisis del legacy `Interno.Domain/Person.cs`)*.
- [ ] **Compliance Fiscal (RFC/CURP)**: Agregar campos `rfc` y `curp` con validación regex al modelo del colaborador para cumplimiento SAT. *(Portado del legacy `Interno.Domain/Person.cs`)*.
- [ ] **Consulta de Elegibilidad**: Endpoint que valide si un operador tiene credenciales vigentes para operar en un despacho cross-border (Visa no expirada + Sentry activo).

## 🌐 Infraestructura (Fase 65)
- [x] **AWS Cost Pivot**: Transición exitosa de ALB (~$23 USD) a AWS App Runner nativo.
- [ ] **AWS Support Ticket**: Confirmar aprobación del Ticket `#177671606300742` para subir cuota de App Runner de 2 a 5.
- [x] **App Runner VPC Connector**: Creado `InternoCore-VPC-Bridge` cruzando subredes privadas para evitar el bloqueo del Healthcheck de Postgres RDS. Aplicado a `auth` y `master-data`.
- [ ] **AWS Secrets Manager**: Migrar todas las variables `CORE_` desde archivos `.env` locales hacia el gestor de secretos de AWS.
- [ ] **Cloud Connectivity**: Validar que MinIO resuelva correctamente bajo el dominio en entorno de App Runner.
- [ ] **Telemetría**: Configurar Prometheus/Grafana para capturar métricas de los 10 principales microservicios.

## 🧠 Últimas Lecciones Relevantes (Fase 65 - FinOps)
- **App Runner Anti-Fraude:** La UI marca 30 servicios, pero la API en cuentas nuevas restringe a 2. Requiere Ticket a soporte para levantar el Sandbox.
- **Costos "Zombies":** Servicios en App Runner en estado `CREATE_FAILED` siguen sumando al contador de cuota y bloquean el ecosistema. Usa `delete-service` ante fallos de boot.

📊 InternoCore: Estado General y Panorama Tecnológico
InternoCore es un ecosistema industrial multi-tenant para la gestión de inventario, manufactura (MES), capital humano (HCM) y tickets de soporte.

Tecnologías Principales: FastAPI (Python 3.12+), SQLAlchemy (Async), Alembic, PostgreSQL, Redis, Angular 19 (Zoneless + Signals + Tailwind) y Flutter (Mobile POS).
Modo de Ejecución: Arquitectura de microservicios locales en Docker, orquestados por un Gateway Nginx en el puerto 8000.
Salud del Código: Validado mediante un auditor estático de grafos de dependencias (generate_code_graph.py) con 0 violaciones arquitectónicas críticas (Clean Code).
🚀 1. Hitos Críticos Completados Recientemente (Mayo 2026)
El desarrollo ha progresado de manera constante, consolidando componentes clave que antes estaban incompletos:

A. Soporte Dinámico de Timezones por Tenant (27 de Mayo)
Base de datos: Se añadió el campo timezone (e.g., America/Monterrey, America/Chicago) al modelo Company, replicado de forma segura en auth_db y master_data_db.
Seguridad y JWT: Las claims del JWT ahora incluyen el timezone dinámico configurado para el tenant durante el flujo de Handshake T1/T2.
Frontend (Angular): Se implementó un pipe personalizado reactivo (localDate) que reemplaza los formateadores de fecha nativos del navegador, garantizando que todas las pantallas rendericen la hora local configurada del tenant.
B. Patrón Documento+Líneas en MES y Despliegue en Docker (28 de Mayo - Hoy)
Base de Datos y Modelos: Implementación de WorkOrder y WorkOrderLine respetando el patrón inmutable Documento+Líneas y usando tipos enumerados nativos en PostgreSQL.
Lógica de Consumo (Backflush/BOM): Creación del WorkOrderHandler que realiza la explosión de listas de materiales (BOM) mediante llamadas HTTP de tipo best-effort hacia inventory-service.
Tests de Integración: Escritura y ejecución exitosa de 17 tests de integración corriendo sobre una base de datos real PostgreSQL con rollback automático (evitando ensuciar datos).
Despliegue: El contenedor interno-mes-dev fue agregado al stack dev de Docker y expuesto a través de Nginx en el puerto 8005.
🏢 2. Estado de Completitud por Microservicio
El backend se encuentra actualmente en un ~82-85% de completitud global para entornos de producción.

Servicio / Componente	Puerto	Completitud	Estado en Docker	Enfoque / Rol en el Ecosistema
common	N/A	100%	✅ Integrado	Modelos base, RLS Postgres, middlewares y utilidades compartidas.
auth_service	8001	92%	🟢 Operativo	Autenticación robusta, tokens T1/T2, RFID, biometría y God Mode.
inventory_service	8006	95%	🟢 Operativo	Kardex inmutable, transferencias ICT, Density Guard, FIFO y control físico.
master_data_service	8003	98%	🟢 Operativo	SSOT de productos, variantes industriales y precios con Soft-Close.
whatsapp_gateway	3011	100%	🟢 Operativo	Pasarela local Node.js con Headless Chromium para envíos sin costo vía API local.
notification_service	8009	90%	🟢 Operativo	Enrutamiento inteligente de notificaciones (Email Resend + WhatsApp Gateway).
mes_service	8005	80%	🟢 Operativo	OEE, consumos de materiales (BOM), órdenes de trabajo y control de piso.
tickets_service	8008	75%	🟢 Operativo	Mesa de ayuda con Triple Identidad (Internal/Plant/External), SLAs y debouncing.
subscription_service	8002	70%	🟢 Operativo	Entitlements, planes y validación de suscripción activa (Stripe).
hcm_service (HR)	8004	50%	🟢 Operativo	Gestión de colaboradores, departamentos y auditoría de personal.
wms_service	8007	35%	🟡 No desplegado	Gestión de ubicaciones lógicas optimizadas y picking de almacén.
🎨 3. Panorama del Frontend y la App Móvil
Angular 19 (Zoneless + Signals) — ~79% Completado
Puntos Fuertes: Excelente arquitectura reactiva sin zona para máximo rendimiento de CPU/batería en tablets industriales. Posee interceptores resilientes con reintentos exponenciales y resiliencia ante caídas de red.
Brechas de Integración Frontend vs. Backend:
WhatsApp Gateway (Brecha Alta): El backend del Gateway local de WhatsApp está al 100%, pero la interfaz del panel de administración en Angular para escanear el código QR y ver el estado de la sesión (CONNECTED/DISCONNECTED) no ha sido implementada.
Stripe Self-Service (Brecha Media): Si un cliente entra en estado UNPAID (impago), el frontend despliega un paywall rígido pero no cuenta con el botón autogestionado para abrir la pasarela de Stripe y regularizar el pago.
Chat en Tiempo Real: El backend de tickets soporta WebSockets para chat de soporte, pero la vista de chat en tiempo real dentro del panel del ticket está pendiente en la UI Angular.
Flutter POS (App Móvil)
Puntos Fuertes: Aprovisionamiento rápido mediante escaneo de código QR (hereda variables de red, tokens y contexto de sucursal), persistencia robusta ante fallos de conexión e integración limpia con el lector de códigos de barra físico de la terminal Moto g04s.
🔴 4. Bloqueos y Tareas Pendientes Críticas
El panorama consolidado de prioridades inmediatas para continuar la estabilización del proyecto se resume en:

Validación E2E del POS Checkout: Verificar la integración entre el checkout móvil, la creación de documentos de inventario y los movimientos negativos (OUT) atómicos en la base de datos de producción.
UI de QR para WhatsApp Gateway: Diseñar e integrar la pantalla en el módulo /admin de Angular para escanear el QR y emparejar dispositivos móviles locales con la pasarela.
Transiciones Automáticas MES: Automatizar la transición de estados en las órdenes de producción (DRAFT $\rightarrow$ IN_PROGRESS $\rightarrow$ COMPLETED) basadas en los escaneos de los operarios reportados por el ScannerService.
Rate Limiting Completo: Integrar los límites de peticiones por endpoint en los módulos de HCM, MES, WMS y Subscripciones para proteger el rendimiento de la API.
Ajuste Fiscal en US: Reconfigurar la tasa impositiva por defecto a 0.0 para las transacciones originadas en la entidad legal "Planta US" en master_data_service.

---
**SSOT - Última Actualización:** 2026-05-28
**Enfoque:** Industrial MES/ERP Only.
**Próxima fase planificada:** Phase 154 — Monitor de Recurso MES ↔ Frontend
