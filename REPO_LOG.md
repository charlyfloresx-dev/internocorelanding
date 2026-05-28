# Interno Core - Global Engineering Log

Tracking the major milestones, architectural shifts, and technical decisions of the ecosystem.

---
### [2026-05-28] Phase 155: HCM — Industrial Identity & Cross-Border Eligibility Hardening ✅

**Objetivos:**
- Incorporar atributos de identidad industrial y credenciales binacionales/satelitales al expediente de colaboradores en el servicio HCM.
- Endurecer el motor de elegibilidad cross-border con reglas estrictas de vencimiento (CDL, Visa, Certificado Médico, Sentry/Global Entry).
- Hacer configurable por tenant/empresa el margen de seguridad de días de expiración.
- Sincronizar el seed unificado de base de datos industrial para pruebas de integración locales.

**Decisiones Arquitectónicas:**
- **Esquema de Base de Datos:** Se crearon las columnas `assigned_plant`, `shift` y `global_entry_id` en la tabla `collaborators` de `hcm_db` (Migración `005`).
- **Elegibilidad Hardened:** El cálculo verifica: Licencia CDL no expirada, Certificado Médico (SCT/DOT) no expirado, Visa estadounidense no expirada, y presencia de Sentry ID o Global Entry ID activo.
- **Configuración Dinámica:** Se extendió el modelo `HrTenantConfig` para almacenar la columna `cross_border_expiry_threshold_days` a nivel empresa. La elegibilidad consulta este umbral para calcular los márgenes de seguridad.
- **Seed Unificado:** Se portaron las dependencias y catálogos correctos a `scripts/unified_industrial_seed.py` para asegurar que el seed industrial del ecosistema inserte correctamente los nuevos campos de colaboradores y las configuraciones de empresa.

**Workarounds / Deuda Técnica:**
- Ninguno en esta fase; las migraciones de Alembic se diseñaron de manera idempotente y limpia en `hcm_db`.

**Archivos clave:**
- `backend/hcm_service/hcm_app/models/collaborator.py`
- `backend/hcm_service/hcm_app/models/tenant_settings.py`
- `backend/hcm_service/hcm_app/domain/entities/collaborator_entities.py`
- `backend/hcm_service/hcm_app/api/v1/endpoints/collaborators.py`
- `backend/hcm_service/alembic/versions/005_add_plant_shift_global_entry.py`
- `backend/scripts/unified_industrial_seed.py`

---
### [2026-05-28] Phase 154: Análisis Arquitectónico — Resource Monitor MES ↔ Frontend (Plan)

**Objetivo:** Diseñar la implementación del Monitor de Recurso real: conectar `ResourceMonitorComponent` (Angular, actualmente 100% mock) al backend `mes_service`.

**Análisis del frontend:**
- `ResourceMonitorComponent` (`/monitor/resources`): UI completa con gráfica hora×hora, tabla acumulada, equipo de soporte y horarios de descanso — todo en signals estáticos hardcodeados. Cero llamadas HTTP.
- `MesItemConfigComponent`: único componente MES ya conectado al backend (scan patterns Phase 152).

**Análisis del legacy `.NET` (`Interno.Production`):**
- `Resource : Warehouse` — en el legacy el recurso hereda directamente del almacén (mismo `Code` string max 13, `Name`, `Type`, `Capacity`, `Group`). Agrega `BreakGroupId` y `ProductionArea`.
- Jerarquía: `Facility → ProductionArea → Resource`, con `BreaksGroup → Break[]` para horarios de descanso.
- `Result` = sesión de producción (fecha + turno + recurso + prioridad). Contiene `HourByHour[]`, `Labor[]`, `Downtime[]`, `Goal[]`. Tiene KPIs: OEE, OE, TEP, Availability, Efficiency, FirstPassYield.
- `GetGraphic()` en `ResultController` es el "algoritmo ~120L": genera slots horarios → aplica breaks → calcula meta por OperationTime → carga actual de `HourByHour` → computa Faltante/Excedente/Eficiencia.

**Decisión arquitectónica (Iron Wall):**
- `Resource` en `mes_service` NO hereda Warehouse (cross-service prohibido).
- Tendrá `warehouse_id: Optional[UUID]` como soft FK hacia `inventory_service.warehouses` — sin FK de BD.
- El `code` (max 13) sigue siendo la clave de negocio operacional.

**Plan plasmado en `docs/historial/PENDIENTES_INDUSTRIAL_CORE.md`** (4 partes con checkboxes):
- Parte 1: `Facility` + `ProductionArea` + `Resource` + tabla pivote soporte + migration + seed.
- Parte 2: `GET /graphic` con algoritmo hora×hora portado de .NET + endpoints `active-workorder` + `planned-workorders`.
- Parte 3: `ResourceService` Angular + desconectar los 3 signals mock + parámetro `:code` + `ResourceSelectorComponent`.
- Parte 4: Verificar nginx upstream MES.

**Archivos clave:** `docs/historial/PENDIENTES_INDUSTRIAL_CORE.md`

---
### [2026-05-28] Phase 153: Kiosk Company Binding + ID Pattern Validation + Light Theme ✅

**Objetivo:** Tres mejoras de producción: vincular el kiosko a una empresa específica en login industrial, validar el formato del ID interno por tenant, y corregir el tema claro en la app Flutter.

**`internal_id_pattern` (auth_service):**
- Migration `c7d4e5f6a8b9`: columna `internal_id_pattern VARCHAR(200) NULL` en tabla `companies`.
- `collaborator_login_command.py` Step 0: si la empresa tiene patrón, valida `re.fullmatch()` antes de autenticar. Inválido → 422 con mensaje descriptivo.
- `PATCH /companies/my/id-pattern` endpoint: admin configura/limpia el regex de su empresa.

**Kiosk Company Binding (Flutter `LoginScreen`):**
- `_handleAutoLogin`: cuando el QR de provisioning contiene `companyId`, lo guarda en `SharedPreferences` como `kiosk_company_id`.
- `_buildKioskCompanyBadge`: estado sin provisionar muestra alerta amber con instrucciones explícitas (admin config o QR scan).
- El `company_id` en `POST /collaborator-login` limita el login al tenant correcto — colaboradores de otras empresas reciben 401.

**Light Theme Flutter (Phase 153):**
- `receipts_screen.dart`: reescrito completo — todas las referencias `Colors.black`/`Colors.white*` reemplazadas por `cs.onSurface.withValues(alpha:…)` y `Theme.of(context).cardColor`.
- `sales_screen.dart`: bottom sheet, modal partner, dialog catálogo — todos theme-aware. Camera overlay intencionalmente oscuro.

**HCM Hotfix:**
- `collaborator_verify_service.py` línea 93: `department=collaborator.department` → `department=collaborator.department.name if collaborator.department else None`. El campo era ORM relationship, Pydantic esperaba string.

**Archivos clave:**
- `backend/auth_service/alembic/versions/c7d4e5f6a8b9_add_internal_id_pattern.py`
- `backend/auth_service/app/commands/collaborator_login_command.py`
- `backend/hcm_service/hcm_app/services/collaborator_verify_service.py`
- `src/interno_billing_app/lib/features/auth/presentation/login_screen.dart`
- `src/interno_billing_app/lib/features/home/presentation/receipts_screen.dart`
- `src/interno_billing_app/lib/features/home/presentation/sales_screen.dart`

---
### [2026-05-28] Phase 151: MES — manufactured_quantity + WO Status Transitions ✅

**Objetivo:** Conectar el flujo de escaneo con el contador de progreso de la WorkOrder.

**`IWorkOrderRepository`** (nueva interfaz + implementación):
- `increment_manufactured_quantity(work_order_id, qty, company_id)`: incrementa `manufactured_quantity`, actualiza `actual_quantity` de la línea PLANNED_OUTPUT, y conduce transiciones de estado.

**Transiciones de status automáticas:**
- `DRAFT → IN_PROGRESS`: en el primer escaneo registrado.
- `IN_PROGRESS → COMPLETED`: cuando `manufactured_quantity >= order_quantity`.
- Sobreproducción permitida (sigue acumulando, status=COMPLETED).

**`ScannerService`**: inyección de `wo_repo`; llama `increment_manufactured_quantity()` post-ledger-entry (best-effort: excepción en WO no rechaza el escaneo).

**Archivos clave:**
- `mes_app/domain/repositories/interfaces.py` — `IWorkOrderRepository`
- `mes_app/infrastructure/repositories/sqlalchemy_repositories.py` — `SQLAlchemyWorkOrderRepository`
- `mes_app/services/scanner_service.py` — `wo_repo` injection
- `mes_app/api/v1/endpoints/scan.py` — `get_work_order_repo` dependency
- `tests/integration/test_manufactured_quantity.py` — 9 tests

---

### [2026-05-28] Phase 150: MES Service — WorkOrder Document+Lines Pattern + Deployment ✅

**Objetivo:** Implementar el Patrón Documento+Líneas en MES, desplegar mes-service en el stack Docker y escribir tests de integración contra mes_db real.

**Infraestructura:**
- `Dockerfile` reescrito: paths `app` → `mes_app`, entrypoint.sh estándar (migrate→seed→serve).
- `docker-compose.dev.yml`: añadido bloque `mes-service` (puerto 8005, `mes_db`).
- `nginx.conf`: descomentada ruta `/api/v1/mes` → `mes-service:8000`.
- `migrate_all.ps1`: añadido `interno-mes-dev` al array de servicios.

**Modelos:**
- `WorkOrder`: añadidos `wo_type: WOType` (enum PostgreSQL), `rout_id` (UUID nullable), `lines` relationship.
- `WorkOrderLine` (NUEVO): Patrón Documento+Líneas — `MATERIAL_INPUT` (BOM explode) + `PLANNED_OUTPUT` (pieza terminada). `work_order_id` con `ForeignKey` + `ondelete=CASCADE`.
- Enums nuevos en `mes_app/core/enums.py`: `WOType`, `WorkOrderLineType`, `WorkOrderLineStatus`, `ProdIssueType`, `IssueType`.

**Migration 008** (`008_wo_doc_pattern`):
- Crea 3 enums PostgreSQL nativos con DO blocks idempotentes (docker restart safe).
- Añade `tenant_id` (nullable) a las 10 tablas existentes en `mes_db`.
- Crea `mes_work_order_lines` con FK cascade, unique constraint `(work_order_id, line_number)`.
- Usa `postgresql.ENUM(..., create_type=False)` para evitar conflictos de tipo existente.

**WorkOrderHandler:**
- `_fetch_bom()`: GET best-effort a inventory-service; retorna `[]` si falla (WO se crea igual).
- `handle_create()`: BOM explode → `N` líneas `MATERIAL_INPUT` + 1 línea `PLANNED_OUTPUT`. CQRS `begin_nested()`.

**Endpoints nuevos:**
- `GET /api/v1/mes/work-orders/{order_number}/lines` → `List[WorkOrderLineRead]`.

**Tests (17 integration tests + 3 unit tests):**
- `tests/integration/test_work_order_lines.py`: schema verification, CRUD, handler BOM explode, cascade delete, FK constraint — todos contra PostgreSQL real.
- `conftest.py` (root + integration): carga `.env` raíz con `python-dotenv` antes de imports de `common`.
- `test_work_order.py`: migrado de SQLite a PostgreSQL (SQLite incompatible con JSONB/UUID).

**Bug encontrado durante tests:** `WorkOrderLine.work_order_id` faltaba declaración `ForeignKey` en el ORM — migrado al definir la columna correctamente.

**Archivos clave:**
- `backend/mes_service/Dockerfile`
- `backend/mes_service/entrypoint.sh`
- `backend/mes_service/mes_app/models/work_order_line.py`
- `backend/mes_service/mes_app/core/handlers/work_order_handler.py`
- `backend/mes_service/alembic/versions/008_add_workorder_document_pattern.py`
- `backend/mes_service/tests/integration/test_work_order_lines.py`
- `infrastructure/docker/docker-compose.dev.yml`

---
### [2026-05-27] Phase 149: MES WorkOrder + Inventory BOM — CRITICAL Bug Fixes ✅

**Objetivo:** Corregir dos bugs CRÍTICOS que impedían la creación de WorkOrders en MES y causaban `AttributeError` en cualquier representación de objetos BOM en inventory.

**WorkOrder (mes_service):**
- `WorkOrderHandler.handle_create()` construía `WorkOrder(order_qty=..., due_date=..., alias=..., release_date=..., status="PLANNED")` — 4 campos inexistentes en el modelo y status incorrecto.
- **Fix modelo**: Añadidos `alias: Mapped[Optional[str]]` y `release_date: Mapped[Optional[datetime]]`.
- **Fix handler**: `order_qty` → `order_quantity`, `due_date` → `request_date`, `status="PLANNED"` → `status="DRAFT"`.
- **Migration `007`**: `ADD COLUMN alias`, `ADD COLUMN release_date` en `mes_work_orders`.

**BOM (inventory_service):**
- `BOM.__repr__` referenciaba `self.parent_item_code` que no existía en el modelo → `AttributeError`.
- El endpoint `POST /api/v1/inventory/boms/` pasaba `parent_item_code` e `is_active` al constructor sin columnas en la tabla → campos silenciosamente ignorados por SQLAlchemy.
- El backflush consumer y reconciliation worker ejecutaban `BOM.parent_item_code == ...` → `AttributeError`.
- **Fix modelo**: Añadidos `parent_item_code: Mapped[Optional[str]]` (indexed) e `is_active: Mapped[bool]`.
- **Migration `005`**: `ADD COLUMN parent_item_code`, `ADD COLUMN is_active` en `inventory_boms`.
- **Referencia legacy**: `Interno.Inventory.BOM.cs` usaba navigation property `Item Item`; Python traduce a `product_id UUID` (FK) + `parent_item_code` string para queries cross-service.

**Archivos clave:**
- `backend/mes_service/mes_app/models/work_order.py`
- `backend/mes_service/mes_app/core/handlers/work_order_handler.py`
- `backend/mes_service/alembic/versions/007_add_workorder_alias_release_date.py`
- `backend/inventory_service/inventory_app/models/bom.py`
- `backend/inventory_service/alembic/versions/005_add_bom_parent_item_code.py`

---

### [2026-05-27] Phase 148: Mobile — Full Theme Dark/Light + i18n en Todas las Pantallas ✅

**Objetivo:** Completar la migración tema/i18n a todas las pantallas individuales de la app (deuda de Phase 146).

**Decisiones Arquitectónicas:**
- **Patrón uniforme**: `scaffoldBg = Theme.of(context).scaffoldBackgroundColor`, `cardBg = Theme.of(context).cardColor`, `cs = Theme.of(context).colorScheme`. Sub-widgets llaman `Theme.of(context)` localmente para evitar prop-drilling.
- **Camera screens frozen**: `setup_screen.dart` (full-screen QR) y el overlay de cámara en `scanner_screen.dart` conservan `Colors.black` hardcodeado — requisito de visibilidad de cámara en hardware real (Moto g04s).
- **Uber POS design frozen**: El carrito/scanner bottom layer de `scanner_screen.dart` conserva paleta oscura hardcodeada; solo las strings se traducen.
- **i18n**: 60+ keys nuevas añadidas a `es.json`/`en.json` cubriendo todos los flows: `scanner.*`, `payment.*`, `checkout.*`, `inventory.*`, `warehouse.*`, `ticket_chat.*`, `login.*`, `setup.*`.
- **Fixes lint incluidos**: `context.mounted` en guards async; `State<T>` return type en `createState()`; imports/campos no usados eliminados.

**Pantallas migradas:** `ticket_chat_screen.dart`, `warehouse_selection_screen.dart`, `inventory_stock_screen.dart`, `checkout_screen.dart`, `payment_confirmation_screen.dart`, `login_screen.dart`, `setup_screen.dart`, `scanner_screen.dart`.

**Status:** ✅ COMPLETED — `flutter analyze` 0 errores, APK debug compilado. Deuda técnica de Phase 146 cerrada.

---

### [2026-05-27] Phase 147: Multi-Tenant Timezone Integration (Frontend & Backend) ✅

**Objetivos:** Implementar soporte dinámico de zona horaria por empresa para corregir desviaciones de horario en auditorías y reportes transaccionales.

**Decisiones Arquitectónicas:**
- **Backend Timezone Infrastructure:** Columna `timezone` (ej. `America/Monterrey`) añadida a la tabla `companies` en `auth_service` y `master_data_service` con valor default `UTC`.
- **JWT Claims:** La zona horaria se inyecta en el payload del Access Token durante el handshake (`/login` -> `/select-company`) en `select_company_command.py`.
- **Frontend Timezone Signal:** Angular lee la zona horaria del JWT y la expone vía `AuthService.companyTimezone()` como signal reactivo.
- **Pipe Standalone:** Se construyó `LocalDatePipe` reemplazando la dependencia nativa de Angular `| date`, manejando la zona horaria destino vía `date-fns-tz`.
- **Seeding Unificado:** El script `unified_industrial_seed.py` se actualizó para sembrar las empresas Planta MX y Planta US con sus zonas horarias operativas reales.

**Workarounds / Deuda Técnica:**
- La migración progresiva del pipe `| date` al nuevo `| localDate` requiere barrer sistemáticamente el frontend, actualmente en progreso iterativo.

**Archivos clave:**
- `backend/auth_service/auth_app/commands/select_company_command.py`
- `backend/common/models/company.py`
- `frontend/src/app/shared/pipes/local-date.pipe.ts`
- `frontend/src/app/core/services/auth.service.ts`

---
### [2026-05-27] Phase 146: Mobile Config — Theme Dark/Light + Language ES/EN ✅

**Objetivo:** Implementar el panel de configuración de la app móvil con selector de tema (oscuro/claro) y selector de idioma (ES/EN), persistentes entre sesiones.

**Decisiones Arquitectónicas:**

- **`ThemeNotifier` (ChangeNotifier):** Persiste `ThemeMode` en SharedPreferences bajo `app_theme_mode`. Default: dark. Registrado en `MultiProvider` por encima del `MaterialApp` para sobrevivir cambios de locale (easy_localization reconstruye el árbol al cambiar idioma).
- **`AppTheme.lightTheme`:** Paleta alineada con el frontend Angular (`styles.css` light vars): scaffold `#F1F5F9`, card `#FFFFFF`, primary `#0284C7`, texto `#0F172A`, muted `#94A3B8`. El dark theme ahora usa `#050B14` (Angular `--color-ic-dark`) en lugar de `#000000` puro — consistencia visual entre plataformas.
- **`MaterialApp` con `themeMode`:** `theme: lightTheme`, `darkTheme: darkTheme`, `themeMode: themeNotifier.mode`. Cambio de tema es instantáneo vía `notifyListeners()` — sin reinicio requerido.
- **Idioma vía `easy_localization`:** El plugin ya persiste el locale internamente. `context.setLocale(Locale('en'/'es'))` reconstruye el árbol. Los nuevos keys `config.*` añadidos a `assets/translations/es.json` y `en.json`.
- **`_ConfigSheet` widget:** Modal bottom sheet con chips animados (180ms). El sheet mismo es theme-aware (fondo negro en dark, blanco en light). Se llama desde el botón "Config." de la pantalla Usuario — reemplaza el stub `_confirmReconnect()` que no tenía función real.
- **Menú Usuario:** Removidos "Perfil del Usuario" y "Tickets de Soporte" (duplicados de otras tabs). Solo quedan: Cambiar Almacén y Reconectar Servidor.

**Archivos clave:**
- `src/interno_billing_app/lib/core/theme/theme_notifier.dart` — nuevo
- `src/interno_billing_app/lib/core/theme/app_theme.dart` — `lightTheme` + dark scaffold actualizado
- `src/interno_billing_app/lib/main.dart` — `ThemeNotifier` provider + `Consumer<ThemeNotifier>` + `themeMode`
- `src/interno_billing_app/lib/features/home/presentation/home_screen.dart` — `_ConfigSheet` + `_Chip` widgets; `_showProfileDialog` removido
- `src/interno_billing_app/assets/translations/es.json` + `en.json` — keys `config.{title,theme,dark,light,language,spanish,english}`

**Workarounds / Deuda Técnica:**
- Las pantallas individuales usan colores hardcodeados (uber_pos industrial design). El `lightTheme` afecta únicamente widgets Material que consumen el `Theme` implícitamente (Scaffold, BottomNav, AppBar). Migración pantalla-por-pantalla a `Theme.of(context)` es deuda futura si se quiere light theme completo.

**Status:** ✅ COMPLETED — APK instalado en Moto g04s · Code Graph 0 CRITICALs · Ecosystem 8/8 OK

---

### [2026-05-27] Phase 145: HCM Departments Seed + Soporte Tab Mobile + Tickets Action Fixes ✅

**Objetivo:** Activar el dropdown de departamentos en la pantalla Soporte del móvil (áreas de la empresa desde HCM), corregir bugs acumulados en el seed de HCM por incompatibilidad con migraciones previas, y limpiar dos bugs en el tickets service (min_length y company_id hardcodeado).

**Decisiones Arquitectónicas:**

- **Migration `003_add_department_description` (hcm_service):** Columna `description VARCHAR(250) NULL` en `departments`. Alembic tiene múltiples heads por las ramas paralelas `001_add_audit_logs` y `001_add_id_pattern` — comando correcto es `alembic upgrade heads` (plural). El `down_revision` de `003` apunta a `a6054c79a22f` (la cabeza de la rama principal después de `002_split_last_name`).
- **Seed HCM corregido (3 bugs):** (1) `last_name=` inválido desde migration `002_split_last_name` (Phase 138) — corregido a `last_name_paternal=`. (2) `department="Warehouse"` pasado como string a un campo que es `relationship` desde Phase 118 — corregido a `department_id=uuid.uuid5(...)` FK determinista. (3) `first_name="Luis (Enterprise)"` / `"Luis (USA)"` — limpiado a `first_name="Luis"` para que `full_name` sea correcto.
- **18 departamentos default seeded:** Producción/PROD, Calidad/QUAL, Mantenimiento/MANT, Almacén/ALM, Administración/ADMIN, Ingeniería/ENG × 3 empresas. UUIDs deterministas `uuid.uuid5(NAMESPACE_DNS, f"interno.dept.{company_id}.{code}")` — idempotent, re-runable.
- **Nginx `/api/v1/hcm`:** Ruta añadida en `nginx.conf` para exponer todos los endpoints HCM al gateway incluyendo el nuevo departamentos.
- **Mobile Soporte Tab (CreateTicketScreen):** Dropdown de áreas populado con `GET /api/v1/hcm/departments/?is_active=true`. Retry button en estado vacío (en lugar de texto muerto). `_loadDepartments()` resetea `_loadingDepts=true` en cada intento.
- **`TicketActionCreate.description` min_length 5→1:** "Test", "OK", "Done" son descripciones legítimas de acciones cortas. El campo `...` (requerido) ya previene strings vacíos.
- **AI Assistant auto-comment:** Removida la línea `"Asegúrate de estar en el tenant correcto: " + str(ticket.company_id)` que exponía el UUID interno del tenant en la UI de producción. Reemplazada con texto genérico de orientación al usuario.

**Archivos clave:**
- `backend/hcm_service/alembic/versions/003_add_department_description.py` — nueva migración
- `backend/hcm_service/hcm_app/models/department.py` — campo `description`
- `backend/hcm_service/hcm_app/schemas/department.py` — `description` en Read/Create/Update
- `backend/hcm_service/scripts/seed.py` — 3 bugs corregidos + 18 depts seeded
- `backend/tickets_service/tickets_app/schemas/ticket_dto.py` — `TicketActionCreate.description` min_length 1
- `backend/tickets_service/tickets_app/services/ticket_service.py` — AI comment sin company_id hardcodeado
- `infrastructure/docker/nginx.conf` — ruta `/api/v1/hcm`
- `src/interno_billing_app/lib/features/home/presentation/create_ticket_screen.dart` — retry button en dept dropdown

**Workarounds / Deuda Técnica:**
- `alembic upgrade heads` requerido en hcm_service por ramas paralelas pre-existentes (`001_add_audit_logs` y `001_add_id_pattern`). Esto es correcto y no requiere merge de ramas.
- El `full_name` de "Luis (Enterprise)" y "Luis (USA)" fue limpiado — si hay datos en producción con esos nombres, requieren update manual.

**Status:** ✅ COMPLETED — Code Graph 0 CRITICALs · Ecosystem 8/8 OK

---

### [2026-05-27] Phase 144: Tickets Mine Triple-Identity + Scanner Conformance + CAPA Checkbox ✅

**Objetivo:** Refinar visibilidad de tickets en móvil (solo asignados, todas las identidades), alinear el scanner POS a la spec Uber, y mejorar la UX del card de acciones CAPA con checkbox circular.

**Decisiones Arquitectónicas:**

- **`GET /tickets/mine` Triple Identity:** El filtro anterior retornaba tickets `created_by OR assigned_to`. Cambiado a solo los asignados, cubriendo las 3 identidades del sistema: INTERNAL (`assigned_to_id` + `ticket_assignees INTERNAL`), PLANTA (`collaborator_id` + `ticket_assignees PLANTA`), EXTERNO (`external_contact_id` + `ticket_assignees EXTERNO`). El endpoint acepta `?collaborator_id=<uuid>&external_contact_id=<uuid>` opcionales para cuando el móvil tenga el perfil físico del usuario. Los `EXISTS` subqueries cubren la tabla nueva `ticket_assignees` evitando que tickets triageados vía multi-asignado queden invisibles (en triage nuevo, `assigned_to_id` es null pero `ticket_assignees` tiene la entrada INTERNAL).
- **Scanner Conformance (spec `uber_pos_layout.md`):** 3 desviaciones corregidas: (1) tarjeta de carrito ahora muestra solo el código (`code ?? sku`) en negrita blanca — sin nombre del producto; (2) scan duplicado ya no muestra modal, sino snackbar una sola vez y silencio subsecuente via `_warnedDuplicates` Set en el BLoC; (3) `scanWindow` pasado al `MobileScanner` restringiendo detección al rectángulo del cutout visual.
- **CAPA Checkbox:** Card de acción reemplaza el botón "Cerrar" (texto top-right) con un checkbox circular animado en el lado izquierdo. `AnimatedContainer` transiciona de círculo vacío (borde blanco24) a círculo verde relleno con ícono check. Touch target 44×44px para uso con guantes industriales. Al cerrarse muestra descripción con tachado + color atenuado. Consistente con el diseño del frontend Angular.
- **audit_logs verificado:** Tablas `audit_logs` en `hcm_db` y `subscription_db` ya existían y estaban aplicadas (migraciones `001_add_audit_logs_hcm` y `001_add_audit_logs_sub`). No requirió acción nueva.

**Archivos clave:**
- `backend/tickets_service/tickets_app/infrastructure/repositories/ticket_repository.py` — `list_by_visibility` con EXISTS subqueries + params `collaborator_id / external_contact_id`; import `or_, exists` a nivel módulo
- `backend/tickets_service/tickets_app/services/ticket_service.py` — `get_tickets_with_visibility` +2 params opcionales
- `backend/tickets_service/tickets_app/routers/ticket_routes.py` — `/mine` +2 query params opcionales
- `src/interno_billing_app/lib/features/scanner/presentation/bloc/scanner_bloc.dart` — `_warnedDuplicates`, skip modal en duplicado, `_onClearCart` limpia set
- `src/interno_billing_app/lib/features/scanner/presentation/scanner_screen.dart` — `scanWindow`, cart item code-only
- `src/interno_billing_app/lib/features/home/presentation/ticket_chat_screen.dart` — `_buildActionCard` con checkbox circular (reemplaza botón "Cerrar")

**Workarounds / Deuda Técnica:**
- `collaborator_id` y `external_contact_id` no están en el JWT — el móvil no los pasa por ahora. Cuando el perfil de colaborador esté en el app, pasar ambos IDs al endpoint `/mine`.
- `_warnedDuplicates` no se limpia en `RemoveItem` individual (solo en `ClearCart`) — edge case: si el usuario retira un ítem y vuelve a escanear el mismo, no verá el warning de nuevo en esa sesión.

**Status:** ✅ COMPLETED

---
### [2026-05-27] Phase 143: ticket_assignees (Multi-Asignado Real) + Fixes Stack Migraciones ✅

**Objetivo:** Implementar soporte real de múltiples asignados por ticket (N usuarios de cualquier tipo por ticket). Corregir stack de errores de migraciones acumuladas en `ticket_actions`. Agregar fecha+hora (5min steps) en formulario de acciones CAPA.

**Decisiones Arquitectónicas:**

- **`ticket_assignees` tabla JOIN:** Reemplaza el diseño de 3 columnas simples (`assigned_to_id`, `collaborator_id`, `external_contact_id`) que limitaba a 1 por tipo. Nueva tabla: `ticket_id FK + identity_type (INTERNAL/PLANTA/EXTERNO) + identity_id UUID (weak ref) + is_lead bool`. Sin FK cross-service — mismo patrón que Triple Identity en tickets.
- **Replace-all semántica en triage:** `replace_assignees()` hace DELETE de todos los assignees del ticket + INSERT bulk de la lista nueva. No hay acumulación incremental — cada triage define el estado final de asignados. Las 3 columnas legacy se sincronizan con el lead de cada tipo para backward compat.
- **`TicketTriage.assignees: List[AssigneeInput]`:** Nuevo campo. Si lista no vacía, usa la nueva tabla. Si vacía, path legacy (3 columnas) — permite rollback y backward compat con clientes que aún no envíen `assignees`.
- **Backfill automático en migración:** `006_add_ticket_assignees` hace INSERT desde las 3 columnas legacy de todos los tickets existentes con `is_active=true`.
- **Corrección de migraciones acumuladas:** `004` añade columnas faltantes de `MultiTenantBase` en `ticket_actions` (`group_id`, `updated_by`, `deleted_at`, `transaction_id`). `005` cambia `updated_at` de `NOT NULL` a `nullable=True`. Root cause: la migración `003` se creó sin comparar vs el ORM base class completo.
- **`alembic_version_tickets.version_num VARCHAR(32)`:** Las IDs de migración deben tener ≤32 chars. `005_fix_ticket_actions_updated_at` (33 chars) causó error en alembic — renombrado a `005_fix_ta_nullable`.
- **datetime CAPA:** `type="date"` + `type="time" step="300"` separados. Chrome respeta `step=300` en `type="time"` (scroll de 5 en 5 min) pero no en `type="datetime-local"`. Si no se selecciona hora, default `00:00`.

**Archivos clave:**
- `backend/tickets_service/tickets_app/models/assignee.py` — nuevo `TicketAssignee`
- `backend/tickets_service/tickets_app/models/ticket.py` — relationship `assignees`
- `backend/tickets_service/alembic/versions/004_fix_ticket_actions_columns.py`
- `backend/tickets_service/alembic/versions/005_fix_ticket_actions_updated_at.py`
- `backend/tickets_service/alembic/versions/006_add_ticket_assignees.py`
- `backend/tickets_service/tickets_app/schemas/ticket_dto.py` — `AssigneeInput`, `TicketTriage.assignees`, `TicketAssigneeRead`, `TicketRead.assignees`
- `backend/tickets_service/tickets_app/services/ticket_service.py` — `replace_assignees` call + legacy sync
- `backend/tickets_service/tickets_app/infrastructure/repositories/ticket_repository.py` — `replace_assignees()` + `selectinload(Ticket.assignees)`
- `frontend/src/app/core/models/support.types.ts` — `TicketAssignee`, `AssigneeInput`, `Ticket.assignees`
- `frontend/src/app/core/services/support.service.ts` — `triageTicket` nueva firma
- `frontend/src/app/modules/monitor/tickets/components/tickets-form.component.ts` — `_prePopulateAssignment` desde `assignees[]`, `submitTriage` con array, datetime dual
- `frontend/src/app/modules/monitor/tickets/tickets-dashboard.component.ts` — `getAssignedLabels` desde `assignees[]`
- `frontend/src/app/modules/monitor/tickets/components/ticket-triage-drawer.component.ts` — nueva firma

**Pendiente:**
- `ticket_assignees` — deprecar 3 columnas legacy (`assigned_to_id`, `collaborator_id`, `external_contact_id`) en phase futura cuando todos los clientes envíen `assignees[]`

---

### [2026-05-27] Phase 142: Tickets Multi-Assignees Fix + TicketActions (CAPA) + Metrics Plan ✅

**Objetivo:** Corregir que el triage solo guardaba un asignado. Implementar tabla `ticket_actions` (acciones correctivas tipo CAPA del legacy Interno.Actions). Planificar sistema de métricas/KPIs y multi-asignados como tabla.

**Decisiones Arquitectónicas:**

- **Triage schema bug fix:** `TicketTriage` Pydantic solo tenía `new_assigned_to_id`. Campos `collaborator_id` y `external_contact_id` no existían en el schema → Pydantic los ignoraba silenciosamente. `ticket_service.py` usaba `getattr(cmd, "new_collaborator_id", None)` (campo inexistente) → siempre `None`. Fix: agregar los campos al schema y leer directamente `cmd.collaborator_id` / `cmd.external_contact_id`.
- **TicketAction (CAPA):** Nuevo modelo derivado del legacy `Interno.Actions.Action.cs`. Campos: `description`, Triple Identity (assigned_to_id | collaborator_id | external_contact_id), `commit_date`, `escalation_date`, `closed_date`, `is_closed`. Migration `003_add_ticket_actions`. Endpoints: `POST /{id}/actions`, `GET /{id}/actions`, `PATCH /{id}/actions/{aid}/close`.
- **Frontend Actions:** Sección "PLAN DE ACCIONES" en columna izquierda del SideDrawer de triage. Lista con checkbox de cierre, badge de responsable y fecha. Formulario desplegable para crear nueva acción.
- **Angular Signals loop definitivo:** `ngOnInit()` ya no llama `loadTickets()` cuando `view() === 'triage'` (setter `data` ya prepobló la vista antes que `ngOnInit` dispare). Root cause del loop era `selectedIdentities()` leído sin `untracked()` dentro del efecto del SideDrawer → `_syncIds()` ahora usa `untracked(() => this.selectedIdentities())`.
- **Downtime → Ticket → Actions flow confirmado:** `mes_service.Downtime` (OPEN) → `tickets_service.Ticket` (type=DOWNTIME) → `TicketAction[]` (CAPA correctivo) → KPIs impactados.
- **Plan multi-asignados (tabla):** Diseñada `ticket_assignees` con `identity_type` ENUM + `identity_id` weak ref + `is_lead`. Migración planificada como Phase siguiente para no romper API actual.
- **Plan KPI/Métricas:** Diseñado `KPIDefinition + KPITarget + KPIReading` basado en `ScoreCard.cs` legacy (DJO). Pendiente decisión de ubicación: `mes_service` (alcance operacional) vs nuevo servicio dado que WMS, Inventory y Tickets también necesitan métricas. `ActionKPILink` (weak ref por `kpi_code`) en `tickets_service`.

**Archivos clave:**
- `backend/tickets_service/tickets_app/schemas/ticket_dto.py` — `TicketTriage` +2 campos + schemas TicketAction
- `backend/tickets_service/tickets_app/services/ticket_service.py` — fix triage fields
- `backend/tickets_service/tickets_app/models/action.py` — nuevo `TicketAction`
- `backend/tickets_service/tickets_app/models/ticket.py` — relationship `actions`
- `backend/tickets_service/tickets_app/routers/ticket_routes.py` — 3 endpoints actions
- `backend/tickets_service/alembic/versions/003_add_ticket_actions.py` — migración
- `frontend/src/app/core/models/support.types.ts` — tipo `TicketAction`
- `frontend/src/app/core/services/support.service.ts` — 3 métodos actions
- `frontend/src/app/modules/monitor/tickets/components/tickets-form.component.ts` — UI acciones + loop fix

**Workarounds / Deuda Técnica:**
- Multi-asignados todavía usa 3 columnas simples en `tickets` (plan de migración a tabla pendiente Phase 143)
- `ActionKPILink` no implementado — pendiente definir ubicación del sistema de métricas
- Search de identidades filtra por `company_id` del JWT — colaboradores de otras empresas del grupo no aparecen (multi-tenant isolation intencional, puede cambiarse a `group_id` si se requiere)

**Status:** ✅ COMPLETED

---
### [2026-05-26] Phase 141: Partner Modal Unification + Dead Code Cleanup + Angular Abs Fix ✅

**Objetivo:** Unificar el selector de cliente/proveedor entre modo venta y modo entrada (mismo componente), eliminar código muerto en `scanner_screen.dart`, y corregir montos negativos en el listado de documentos Angular.

**Decisiones Arquitectónicas:**

- **`PartnerSearchModal` universal**: El modal ya detectaba el modo (`ScannerMode.entry` → `SUPPLIER`, else → `CUSTOMER`) en línea 33. Modo venta usaba un `AlertDialog` simple sin búsqueda (`_showPartnerSelectionDialog`). Reemplazado por el mismo `_showPartnerSearch()` en ambos modos — 0 duplicación, mismo componente. El `AlertDialog` sin búsqueda eliminado.
- **Carga eager + filtro local**: `PartnerSearchModal` antes sólo cargaba socios al escribir (red por cada tecla). Reescrito con `initState → getPartners(type)` para traer todos los socios al abrir, y `_onSearch` filtra localmente por `name` o `code`. Sin latencia de red por tecla; `if (!mounted) return` previene setState post-dispose.
- **`MasterDataClient` ENV_ACCESS_VIOLATION**: `os.getenv("CORE_MASTER_DATA_URL", ...)` directo en `__init__` violaba el invariante `ENV_ACCESS_VIOLATION` del Code Graph. Reemplazado por `settings.int_master_data_service_url` (campo existente en `common/config.py` con alias `CORE_MASTER_DATA_SERVICE_URL`). Code Graph: 0 errores.
- **Angular `total_value` abs**: El endpoint de listado devuelve `total_amount` con signo del motor FIFO (negativo en OUT). `Math.abs()` aplicado en el mapeo Angular (`inventory-documents.component.ts:622`). El signo de dirección lo porta la columna TIPO, no el valor monetario.
- **Dead code cleanup `scanner_screen.dart`**: Removidos `import 'package:intl/intl.dart'`, `_UberCircleIcon`, `_CircleIconButton`, imports de `partner_repository` y `domain/entities/partner` (ahora sólo `PartnerSearchModal` los usa). `_showManualInput` conectado al estado vacío del entry mode con `TextButton.icon(keyboard_rounded)`.

**Archivos clave:**
- `src/interno_billing_app/lib/features/scanner/presentation/scanner_screen.dart` — dead code out, ambos modos usan `_showPartnerSearch`
- `src/interno_billing_app/lib/features/scanner/presentation/widgets/partner_search_modal.dart` — reescrito eager+local filter
- `backend/inventory_service/inventory_app/infrastructure/clients/master_data.py` — `os.getenv` → `settings.int_master_data_service_url`
- `frontend/src/app/modules/inventory/inventory-documents.component.ts` — `Math.abs()` en mapeo `total_value`

**Status:** ✅ COMPLETED

---
### [2026-05-26] Phase 140: Entry Screen UX + vdetail Fix + MasterDataClient Docker URL ✅

**Objetivo:** Resolver 500 en `/vdetail`, corregir negativos en totales OUT, redeseñar pantalla de recepción móvil (partner selector + controles de cantidad + layout compacto).

**Decisiones Arquitectónicas:**

- **`vdetail` 500 → ItemVariant en DB equivocada**: `get_document_by_id` hacía `SELECT inventory_item_variants` en `inventory_db`, pero esa tabla vive en `master_data_db` desde Phase 119. Fix: reemplazadas ambas queries por `md_client.get_product_internal_metadata()` — llamada HTTP al servicio correcto con fallback resiliente.
- **MasterDataClient URL Docker**: `localhost:8000` no funciona dentro de un contenedor Docker (apunta al contenedor mismo). Cambiado a `os.getenv("CORE_MASTER_DATA_URL", "http://master-data-service:8000/api/v1")`. El nombre `master-data-service` es el service name de Docker Compose dentro de la red `interno-network`.
- **Negativos en documentos OUT**: El motor FIFO almacena `quantity_change` negativo para salidas (permite `new_balance = prev + change` sin condicional). La capa de presentación aplica `abs()` en `quantity`, `total_amount`, `total_weight`. El `document_type` + `concept` ya porta la semántica de dirección — exponerle negativos al frontend sería fuga de abstracción del motor FIFO.
- **Pantalla de entrada rediseñada**: `checkout_screen.dart` refactorizado en componentes privados (`_PartnerSelector`, `_ItemRow`, `_QtyButton`, `_Footer`, `_TotalLabel`). El `_PartnerSelector` abre `PartnerSearchModal` (ya filtraba por `type=SUPPLIER` en modo entry) con tap para limpiar selección. `_ItemRow` tiene controles `+/−` que despachan `UpdateQuantity`; botón `−` en cantidad 1 despacha `RemoveItem`. Footer compacto con subtotal + IVA + total en una sola fila.

**Archivos clave:**
- `backend/inventory_service/inventory_app/infrastructure/clients/master_data.py` — URL Docker + `get_product_internal_metadata` usa `_get_headers()`
- `backend/inventory_service/inventory_app/infrastructure/repositories/sqlalchemy_inventory_repository.py` — `get_document_by_id` sin ItemVariant, `abs()` en totales/cantidades
- `src/interno_billing_app/lib/features/scanner/presentation/checkout_screen.dart` — rediseño completo con partner selector y qty controls

**Status:** ✅ COMPLETED

---
### [2026-05-26] Phase 139: POS Checkout Stabilization — Folio Fix + IVA Display + Receipts Screen ✅

**Objetivo:** Resolver errores de producción que bloqueaban el flujo completo de venta móvil (500 en checkout) e implementar la pantalla de recibos con datos reales. Venta `DOC-000007` completada exitosamente en dispositivo físico Moto g04s.

**Decisiones Arquitectónicas:**

- **Folio multi-tenant**: `_next_doc_folio` contaba solo documentos del mismo `document_type`, causando colisión `DOC-000001` entre IN y OUT del mismo tenant. Corregido a `COUNT(*) WHERE company_id = :cid` (todos los tipos). El folio es un secuencial global por empresa, no por tipo.
- **Constraint único**: `inventory_documents_folio_key` era `UNIQUE(folio)` global — imposible en multi-tenant. Migration `004_fix_folio_unique_constraint` lo convierte a `UNIQUE(company_id, folio)`.
- **ForensicImmutability whitelist**: El guard `before_update` en `events.py` solo permitía mutar `available_quantity`. El discharge FIFO también escribe `source_movement_id` en el movimiento OUT (traceabilidad). Añadido al whitelist como campo de auditoría, no de negocio — solo se asigna una vez (si es NULL) y no modifica el ledger financiero.
- **Error SKU en stock insuficiente**: Backend ahora enriquece el mensaje `ERR_INSUFFICIENT_STOCK` con `| SKU: {sku}` para que el móvil pueda extraer y mostrar el código exacto sin parsear el mensajero completo.
- **Parsing de errores anidados**: Los errores `DioException` con `detail` como `dict` (Python) se serializan con single quotes — Flutter BLoC ahora maneja `rawMsg is Map` antes de hacer `.toString()`.

**Archivos clave:**
- `backend/inventory_service/inventory_app/core/events.py` — whitelist `source_movement_id`
- `backend/inventory_service/inventory_app/api/v1/endpoints/transactions.py` — folio fix + SKU en error + `GET /documents`
- `backend/inventory_service/alembic/versions/004_fix_folio_unique_constraint.py` — constraint multi-tenant
- `src/interno_billing_app/lib/features/scanner/presentation/bloc/scanner_bloc.dart` — dict error parsing + SKU extraction
- `src/interno_billing_app/lib/features/scanner/presentation/payment_confirmation_screen.dart` — IVA breakdown
- `src/interno_billing_app/lib/features/home/presentation/receipts_screen.dart` — pantalla real con API
- `src/interno_billing_app/lib/features/home/data/document_repository.dart` — `GET /inventory/documents`
- `src/interno_billing_app/lib/features/home/data/models/document_models.dart` — `InventoryDocumentRow`

**Workarounds / Deuda Técnica:**
- `TRB-700` sin stock en seed — solo `ECM-600` tiene existencias suficientes para pruebas POS.
- Emojis/iconos eliminados de todos los mensajes de log backend y Flutter BLoC.

**Status:** ✅ COMPLETED — Venta end-to-end `DOC-000007` confirmada en dispositivo físico.

---
### [2026-05-26] Phase 135-137: mes_service — Core Matemático, Planning Bulk-load, Seguridad ✅

**Objetivo:** Implementar los tres bloques de refactorización del MES derivados del análisis legacy de la sesión anterior.

**Decisiones arquitectónicas:**
- `break_minutes INTEGER DEFAULT 60` en `mes_shifts` — configurable por turno, elimina el hardcoded del legacy `TotalTimeBreaks = 1h`
- `cycle_time_seconds INTEGER NULL` en `mes_standard_times` — RunTime por pieza; NULL = sin time-study, fallback a `set_time_hours`
- `ShiftService.calculate_available_minutes()` con aritmética overnight: `(24h − start) + end` para T2 16:30–01:45
- `ManufacturingMath.calculate_theoretical_capacity()` — nueva función para capacidad teórica por turno
- `POST /planning/bulk-load` con `begin_nested()` por entrada — fallo parcial no aborta el lote
- Downtime IDOR eliminado: `tech_user_id`/`admin_user_id` extraídos del JWT (`current_user.sub`), nunca del body/params
- `require_scope` aplicado en scan, dashboard (3 endpoints), labor (4 endpoints), downtime (5 endpoints)
- Fix `float(ledger_entry.qty)` → `str(Decimal(...))` en scan.py — PRIMITIVE_FLOAT_VIOLATION resuelto
- Fix `db.get(WorkOrder, order_number)` → `select().where(order_number == ...)` — BUG-02 resuelto
- `alembic/env.py` limpiado: debug prints eliminados + `version_table="alembic_version_mes"` añadido
- Code Graph Auditor: **100% Compliance, 0 CRITICALs, 0 WARNINGs** post-implementación

**Archivos clave:** `mes_service/alembic/versions/006_mes_cycle_time_and_breaks.py` · `mes_service/mes_app/api/v1/endpoints/planning.py` · `mes_service/mes_app/api/v1/endpoints/production.py` · `mes_service/mes_app/services/shift_service.py`

---

### [2026-05-26] Phase 138: hcm_service — Mexicanización del Expediente ✅

**Objetivo:** Adaptar el modelo de colaborador al marco legal mexicano con doble apellido.

**Decisiones arquitectónicas:**
- `last_name` → `last_name_paternal VARCHAR(50) NOT NULL` + `last_name_maternal VARCHAR(50) NULL` (doble apellido MX)
- `full_name` property actualizada para componer los dos apellidos
- RFC y CURP ya existían con validators desde Phase 50 — no requirieron cambios
- Migration con data copy: `SET last_name_paternal = last_name` antes de DROP COLUMN

**Archivos clave:** `hcm_service/alembic/versions/002_split_last_name.py` · `hcm_service/hcm_app/models/collaborator.py`

---

### [2026-05-26] Phase 134: mes_service — Análisis Legacy + Plan de Refactorización (Phases 135–138) 📋

**Objetivo:** Auditoría completa del código legacy (.NET) y definición del plan de refactorización del `mes_service` absorbiendo conocimiento de dominio genérico de manufactura.

**Legados analizados:**
- `Interno.Production` (.NET 7) — sistema de producción original; confirmó gaps en `RunTime`, `Planning`, `ResultWorkOrder N:M`, `WOType`
- `Interno.HumanResource` (.NET 7) — sistema HR; confirmó necesidad de doble apellido + RFC/CURP en `hcm_service`
- `Interno.DJO` (.NET Core 3.1) — supply chain para cliente Enovis (procurement, STBL, Kanban) → **descartado como deuda futura** (dominio separado, no genérico)
- `Interno.Outset` (.NET 7) — adaptador Tulip MES → confirma que `RunTime` es crítico para StdTime real

**Decisiones arquitectónicas:**
- Modelo `ProductionRun` ya limpio (Phase 17.5) — solo extensión de atributos, no rediseño
- `cycle_time_seconds` (RunTime) se agrega como campo nullable a `StandardTime`
- Flujo de planificación vía `POST /planning/bulk-load` en lugar de Excel monolítico legacy
- N:M WorkOrders resuelto con patrón Ledger (ya existe `IManufacturingLedgerRepository`)
- Downtime endpoints sanitizados extrayendo IDs de usuario del JWT, no del body/params
- Funcionalidad DJO-específica descartada: STBL, Kanban, Supplier Scorecard, Tulip integration

**Fases derivadas (pendientes de implementación):**
- **Phase 135** — Core matemático: `cycle_time_seconds`, overnight shift, alembic cleanup
- **Phase 136** — Ingesta: `POST /planning/bulk-load` con `ScheduleProduction` en batch
- **Phase 137** — Seguridad: IDOR downtime + scopes faltantes + endpoint `/scrap`
- **Phase 138** — hcm: `last_name_paternal/maternal` + RFC/CURP validators

**Archivos clave:** `backend/mes_service/SERVICE_LOG.md` · `docs/historial/tasks/consolidated_tasks20260526.md`

---
### [2026-05-26] Phase 133: Security Hardening Sprint 2 — Exception Exposure Fix + AuditService DB Logging ✅

**Objetivo:** Auditoría OWASP Top 10 del ecosistema + corrección de excepción raw expuesta en respuestas HTTP 500 del middleware global + implementación real de `AuditService.track()` con persistencia en DB.

**Decisiones Arquitectónicas:**

- `InternoCoreGlobalMiddleware` ya no expone `str(e)` al cliente — respuesta genérica `"An unexpected error occurred."` con `trace_id` para soporte. Stack trace completo va a logs del servidor via `logger.error(exc_info=True)`.
- `AuditService.track()` implementado como `asyncio.create_task(_persist())` fire-and-forget — abre su propia sesión con `AsyncSessionLocal`, falla silenciosamente si la DB no está disponible. Era un `print()` stub desde Phase 1.
- Errores críticos de middleware quedan en `audit_logs` con `action="CRITICAL_MIDDLEWARE_ERROR"` y metadata completa (`trace_id`, `error_type`, `error_message`, `method`, `path`).

**Hallazgos pendientes (no corregidos en esta fase):**

| Severidad | Hallazgo |
|---|---|
| CRÍTICO | `kiosk_service` CORS `allow_origins=["*"]` |
| ALTO | `asset_manager_service` CORS fallback a `["*"]` |
| MEDIO | `"https://*.vercel.app"` wildcard subdomain en `common/config.py` |
| MEDIO | God Mode `==` no constant-time — debería ser `hmac.compare_digest()` en `middleware.py:123` |

**Archivos clave:** `backend/common/middleware.py` · `backend/common/services/audit_service.py`

---
### [2026-05-24] Phase 132: ScannerScreen Dual-Mode UI — Uber POS Restaurado ✅

**Objetivo:** Restaurar el diseño Uber POS frozen (`uber_pos_layout.md`) en la pestaña Ventas sin romper la arquitectura de cámara única establecida en Phase 131.

**Decisión Arquitectónica:**
`ScannerScreen` ahora renderiza dos UIs distintas según `state.mode` — un solo `MobileScannerController` compartido para ambos modos, evitando el conflicto de hardware BLASTBufferQueue del Moto g04s que aparece con dos instancias simultáneas de `MobileScanner`.

| Mode | UI renderizado | Checkout destino |
|---|---|---|
| `ScannerMode.sale` | Uber POS: camera fullscreen + cutout verde + laser rojo + top pill MX$ + `DraggableScrollableSheet` + slide-to-confirm | `PaymentConfirmationScreen` |
| `ScannerMode.entry` | Design actual: VENTA/ENTRADA toggle + panel fijo 45% altura | `CheckoutScreen` |

**Cambios Mobile:**

| Cambio | Archivo |
|---|---|
| `_buildSaleMode()` — diseño completo de `SalesScreen` integrado (overlay painter, laser, top bar, draggable sheet, slide-to-confirm) | `scanner_screen.dart` |
| `_buildEntryMode()` — diseño previo de `ScannerScreen` (toggle + panel fijo) intacto | `scanner_screen.dart` |
| Estado de sync integrado en `_ScannerScreenState`: `_sheetController`, `_slideProgress`, `_isSyncing`, `_productCatalog` | `scanner_screen.dart` |
| Listener `BlocConsumer` dispara `_showProductDetectedSheet` (sale) o `_showProductConfirmation` (entry) según modo | `scanner_screen.dart` |
| `_ScannerOverlayPainter` (custom painter con cutout + esquinas verdes) incluido en `scanner_screen.dart` | `scanner_screen.dart` |

**Workarounds / Deuda Técnica:**
- `sales_screen.dart` permanece intacto como archivo de referencia del diseño frozen
- `main_navigation_screen.dart` sin cambios — sigue con `_physicalSlots = [0, 0, 1, 2, 3]`
- Tickets `/internal` retorna 400 sin firma (no 403) — body validation precede al HMAC check; no es brecha (no 200)

**Archivos clave:** `src/interno_billing_app/lib/features/scanner/presentation/scanner_screen.dart`

---

### [2026-05-24] Phase 131: ScannerScreen Unificado (Ventas/Recibos) + payment_method Backend

**Objetivo:** Unificar las pestañas Ventas y Recibos del mobile en una sola `ScannerScreen` compartida, y elevar `payment_method` de workaround en `notes` a campo propio en `inventory_documents`.

**Cambios Mobile (Flutter):**

| Cambio | Archivo |
|---|---|
| Pestañas Ventas (tab 0) y Recibos (tab 1) comparten slot físico 0 en `IndexedStack` | `navigation/main_navigation_screen.dart` |
| `_physicalSlots = [0, 0, 1, 2, 3]` — un solo `MobileScannerController` evita conflicto de hardware | `main_navigation_screen.dart` |
| `_onTabTapped` despacha `ModeSelected(sale/entry)` al `ScannerBloc` compartido | `main_navigation_screen.dart` |
| Guard `if (event.mode == state.mode) return` en `_onModeSelected` — evita limpiar carrito al re-tapear la misma pestaña | `scanner_bloc.dart` |
| `ScannerScreen` acepta `isTabMode: bool` — oculta botón X al estar embebida como tab | `scanner_screen.dart` |
| `PartnerSearchModal` bug fix: `context.read<PartnerRepository>()` → `sl<PartnerRepository>()` | `partner_search_modal.dart` |
| `_buildNotes()` workaround eliminado — `payment_method` se envía como campo JSON directo | `inventory_document_request.dart` |

**Cambios Backend (inventory_service):**

| Cambio | Archivo |
|---|---|
| Alembic migration `003_add_payment_method_to_documents.py` — columna `payment_method VARCHAR(20) NULL` | `alembic/versions/003_add_payment_method_to_documents.py` |
| `InventoryDocument.payment_method: Mapped[Optional[str]]` | `models/document.py` |
| `InventoryDocumentCreate.payment_method: Optional[str] = None` | `schemas/inventory.py` |
| `doc_entity` incluye `payment_method` en `create_document` | `api/v1/endpoints/transactions.py` |
| `create_inventory_document` mapea `payment_method` al constructor | `infrastructure/repositories/sqlalchemy_inventory_repository.py` |

**Cambios Seed / Enumeraciones:**

| Cambio | Archivo |
|---|---|
| `PAYMENT_METHOD` añadido a `enums_to_seed`: CASH, CARD, TRANSFER, STRIPE, CREDIT | `scripts/unified_industrial_seed.py` |
| Section 3 ahora llama `seed_enumerations(session)` en `master_data_db` — sinc entre DBs | `scripts/unified_industrial_seed.py` |
| `PAYMENT_METHOD` añadido a `master_data_service/scripts/seed_enums.py` | `master_data_service/scripts/seed_enums.py` |

**Arquitectura de enums — Payment Method:**
- `PAYMENT_METHOD` es un enum **dinámico de DB** (`enumerations` table, `company_id=NULL` para globales)
- Empresas pueden extender con métodos propios (p.ej. `CUENTA_CORRIENTE`) via `company_id` específico
- El enum Python `PaymentMethod` en `common/enums.py` se mantiene para validación en código
- El frontend consulta `GET /api/v1/enumerations?type=PAYMENT_METHOD` (endpoint dinámico)
- La columna almacena la key string (ej: `"CASH"`) sin FK hard-coded para máxima flexibilidad

**Contrato JSON verificado:**
```json
{
  "correlation_id": "uuid",
  "type": "OUT",
  "concept_id": "SAL-VEN",
  "warehouse_id": "uuid",
  "payment_method": "CASH",
  "notes": "Venta móvil",
  "items": [...]
}
```

**Status:** ✅ Phase 131 COMPLETED

---
### [2026-05-23] Phase 130: POS Checkout Stabilization + Nginx Dynamic Resolver

**Objetivo:** Estabilizar el flujo completo de venta desde la app móvil Flutter (INTERNO POS) al backend, eliminando el error 502 Bad Gateway y el 500 por consulta SQL cross-DB.

**Bugs corregidos:**

| Bug | Causa | Fix |
|---|---|---|
| `500` en `POST /pos/checkout` | `pos.py` ejecutaba `SELECT allow_price_override FROM products` contra `inventory_db`. La tabla `products` vive en `master_data_db`. | Reemplazado por `await service.md_client.validate_product(...)` (HTTP cross-service correcto) |
| `partner_id` ignorado en checkout B2B | Mobile envía `partner_id`, schema `SaleCreate` solo tenía `customer_id` | Añadido `partner_id` con `model_post_init` alias en `schemas/pos.py` |
| OUT movements suman stock en vez de restar | `transactions.py` pasaba `item.quantity` (siempre positivo) para salidas | Negado para tipos `OUT` y `BACKFLUSHING` con `_OUTBOUND_TYPES` set |
| `SqliteException ON CONFLICT` en sync de precios | `insertAllOnConflictUpdate` en `local_prices` con PK autoincrement-only | `fullSyncReplace` usa `insertAll` (tabla vacía antes de insertar) |
| `type 'Null' is not a subtype of type 'int'` en catálogo | `LocalPrice.fromData()` casteaba `row_id` a `int` no-nullable; LEFT JOIN devuelve NULL | `rowId` cambiado a `int?` en `local_database.g.dart` |
| Partner selection no repreciaba ítems del carrito | `_onSelectPartner` era sync void, no re-fetched precios | Cambiado a `async Future<void>` con re-lookup por ítem en `scanner_bloc.dart` |
| `502 Bad Gateway` al hacer checkout | Nginx cacheó IP vieja del contenedor tras rebuild (`172.19.0.5` vs nuevo `172.19.0.12`) | `nginx.conf` migrado a `resolver 127.0.0.11 valid=30s` + `proxy_pass` via variables dinámicas |

**Decisiones Arquitectónicas:**
- `product_override = True` en POS: el precio ya viene resuelto por el móvil vía Onion Lookup. El backend no re-valida precio si `validate_product` pasa (precio enforcement suave).
- Nginx community edition requiere `set $svc http://hostname:port; proxy_pass $svc;` para activar resolución DNS dinámica. Los bloques `upstream` estáticos cachean IPs en startup.

**Archivos clave:**
- `backend/inventory_service/inventory_app/api/v1/endpoints/pos.py`
- `backend/inventory_service/inventory_app/schemas/pos.py`
- `backend/inventory_service/inventory_app/api/v1/endpoints/transactions.py`
- `src/interno_billing_app/lib/core/database/local_database.dart`
- `src/interno_billing_app/lib/core/database/local_database.g.dart`
- `src/interno_billing_app/lib/features/scanner/presentation/bloc/scanner_bloc.dart`
- `infrastructure/docker/nginx.conf`

**Status:** ✅ Phase 130 COMPLETED

---
### [2026-05-23] Phase 129: Landing Audit vs Operational Plan + WhatsApp How-To Reference

**Objetivo:** Auditoría estratégica cruzada entre la landing page (`src/landing/`) y el historial de fases implementadas. Identificar gaps entre lo prometido y lo entregado. Consolidar documentación de WhatsApp.

**Hallazgos de auditoría (9 módulos evaluados):**

| Módulo | Estado |
|---|---|
| Auth, Master Data, Inventory, Subscription | ✅ Completos |
| HCM Identity, Notifications/WhatsApp | ⚠️ Parciales |
| MES Engine, WMS Logistics, CMMS Assets | ❌ Pendientes (código existe, sin despliegue activo) |

**Features implementados no comunicados en landing:** Flutter INTERNO POS, Price Agreements B2B, Soft-Close Pricing, RFID Dual-Hash, RLS multi-tenant, Currency SSOT Banxico.

**ADRs registrados:**
- ADR-04: MES + WMS activar en nginx como prioridad P1 del próximo sprint (habilita Plan Industrial $350/mes)
- ADR-05: CMMS como módulo de `mes_service` — no microservicio independiente

**Documentación How-To WhatsApp (referencia):**
- `docs/howto/whatsapp_pairing_and_notifications.md` — pairing + test-send (Phase 124)
- `docs/howto/whatsapp_group_setup.md` — descubrimiento de grupos + mappings (Phase 128)
- Stack verificado E2E: Angular → Nginx:8000 → notification_service:8009 → gateway:3011 → WhatsApp

**Status:** ✅ Phase 129 COMPLETED

---
### [2026-05-22] Phase 128: WhatsApp Group Discovery + Registration UI + E2E Group Delivery

**Objetivo:** Completar el canal de notificaciones grupales de WhatsApp: descubrimiento de JIDs desde el panel Angular, registro de mappings en DB y verificación de entrega E2E a grupo real.

**Cambios implementados:**
- **`backend/whatsapp_gateway/src/manager.ts`**: Nuevo método `getChats(companyId)` — llama `client.getChats()`, filtra grupos `@g.us`, retorna `{ id, name, participantCount }`.
- **`backend/whatsapp_gateway/src/index.ts`**: Nuevo endpoint `GET /api/v1/whatsapp/session/:company_id/chats`.
- **`backend/notification_service/app/routers/whatsapp_routes.py`**: Nuevo proxy `GET /whatsapp/session/chats` con ADR-02 (company_id del JWT).
- **`frontend/src/app/modules/admin/whatsapp-gateway.component.ts`**: Reemplazado placeholder "Grupos configurados" con UI funcional: botón "Descubrir grupos", lista de grupos con JID y participantes, registro inline con nombre auto-sugerido, badge "Registrado" para grupos ya mapeados, carga automática de mappings al conectar.
- **`docs/howto/whatsapp_group_setup.md`**: How-to completo (arquitectura, 5 pasos, tabla de nombres lógicos, troubleshooting).
- **`backend/tickets_service/scripts/test_whatsapp_chats.py`**: Script de descubrimiento y registro de mappings vía CLI.
- **`.agent/workflows/initialize-dev.md`**: Actualizado con paso 6.4 de descubrimiento de grupos y opción C de rebuild con restart gateway.
- **`.agent/workflows/sync-docs.md`**: Paso 3.55 de verificación de mappings de grupos.

**Verificación E2E:**
- Grupo "Coppel" (`120363042693431357@g.us`, 4 participantes) — mensaje recibido físicamente a las 2:22 PM ✓
- Stack completo: Angular drawer → Nginx:8000 → notification_service:8009 → gateway:3011 → WhatsApp

**Mapping registrado:**
- `ALERTAS_INTERNO` → `120363425542705784@g.us` (grupo "Alertas Interno")
- Grupo "Coppel" → `120363042693431357@g.us` (verificación E2E)

**Status**: ✅ Phase 128 COMPLETED

---
### [2026-05-22] Phase 127: Sentinel Mobile Dashboard Enrichment & Field Alignment

**Objetivo:** Enriquecer el dashboard de tickets móvil agregando visualización de prioridad, asignación y área operacional, garantizando la compatibilidad con el backend `tickets_service` y alineando los endpoints de consumo.

**Cambios implementados:**
- **Mapeo de Campos en Dart (`ticket_models.dart`)**: Agregados campos `assignedToId`, `area` y `ticketType` al modelo `Ticket` mapeados desde los payloads del backend.
- **Rutas y Endpoint en Mobile (`ticket_repository.dart`)**: Modificada la petición del listado de tickets en la app móvil para llamar a `GET tickets/mine` (obtiene tickets creados por o asignados al usuario en el tenant actual) en lugar de `GET tickets/` (que es el endpoint de administración global de la empresa).
- **Dashboard Móvil Mejorado (`tickets_screen.dart`)**: 
  - Añadido indicador de prioridad lateral de color con código de color de alta visibilidad (Crítica = Rojo, Alta = Naranja, Media = Amarillo, Baja = Azul).
  - Añadido badge de prioridad con texto estilizado en la parte inferior de la tarjeta.
  - Añadido indicador de asignación: "👤 Asignado" (o nombre del operador si está disponible) vs "⚠️ Sin Asignar".
  - Añadido tag visual para el área operativa del ticket (ej., Producción, Almacén, Mantenimiento).
- **Verificación de Soporte del Backend**:
  - Validado que el DTO `TicketRead` del backend define exactamente los campos `assigned_to_id`, `area`, `ticket_type` y son expuestos correctamente.
  - Verificado el cumplimiento de Code Graph de `tickets_service` al 100% (0 errores) y pruebas HMAC funcionales para endpoints de canal interno.

**Status**: ✅ Phase 127 COMPLETED

---
### [2026-05-22] Phase 126: Multi-Tenant Isolated Ticket Consecutive Number Fix

**Objetivo:** Resolver la colisión de números consecutivos de tickets en escenarios multi-tenant aislados y dar soporte a secuencias heredadas.

**Cambios implementados:**
- **Base de Datos & Migraciones**: Creada migración de Alembic `002_ref_code_composite.py` para reemplazar la restricción única global `tickets_reference_code_key` por un índice y restricción compuesta `tickets_company_id_reference_code_key` sobre `(company_id, reference_code)`. Migración ejecutada exitosamente en el contenedor `interno-tickets-dev`.
- **Modelos SQLAlchemy (`ticket.py`)**: Removido `unique=True` de la columna `reference_code` y agregada la restricción a `__table_args__` del modelo `Ticket`.
- **Algoritmo de Consecutivos (`infrastructure/repositories/ticket_repository.py`)**: `_generate_ref_code` ahora busca tickets mediante el patrón `%-{current_year}-%` filtrado por `company_id`. Cuenta correctamente todos los prefijos del tenant (`IT-`, `SEC-`, `EXT-`, `TKT-`) y emite folios continuos de forma atómica y aislada por empresa (ej. genera `TKT-2026-0008` tras los 7 tickets pre-sembrados).

**Status**: ✅ Phase 126 COMPLETED

---
### [2026-05-22] Phase 125: Sentinel Mobile Ticket Integration & Support Drawer Sync

**Objetivo:** Integrar el módulo de soporte y tickets en la aplicación Sentinel Mobile (Flutter) con arquitectura offline-first y multitenancy dinámico (sin fricción para el usuario de planta), logrando sincronización en tiempo real con el panel de control web.

**Cambios implementados:**
- **Modelos y DTOs en Dart (`ticket_models.dart`)**: Modelos `Ticket`, `TicketCreateRequest`, y `TicketComment` sincronizados con los esquemas Pydantic del backend en formato, tipos de datos y mapeos.
- **Repositorio HTTP (`ticket_repository.dart`)**: Implementado en `Dio` y registrado en `GetIt`. Inyecta el `company_id` obtenido localmente de `SharedPreferences` para aislar el multi-tenant sin pedir datos redundantes al operador (cero fricción).
- **Gestión de Estado (`tickets_bloc.dart`)**: Inyectado como `Factory` en `injection.dart` y registrado globalmente en `main.dart` para manejar los eventos `LoadTickets`, `CreateTicket`, `LoadTicketComments`, y `AddTicketComment` con refresco automático de bandejas.
- **Vistas "Uber-Style" de Alto Contraste (UI Layer)**:
  - `tickets_screen.dart`: Visualiza el listado de tickets consumido del backend, con estadísticas rápidas (pendientes vs resueltos) y navegación limpia.
  - `create_ticket_screen.dart`: Formulario de reporte express de nivel 1 de alto contraste (fondo oscuro con cyan) con validación local robusta.
  - `ticket_chat_screen.dart`: Chat bidireccional fluido con burbujas alineadas según emisor (operador/soporte), cabecera estática con metadatos del ticket y auto-scroll.
- **Validación del Ecosistema**: Análisis estático mediante `flutter analyze` completado con 0 errores y 0 advertencias.

**Status**: ✅ Phase 125 COMPLETED

---
### [2026-05-22] Phase 124 Addendum: WhatsApp Drawer UI + SingletonLock Fix + Mensaje Entregado

**Cambios adicionales (misma jornada):**
- **WhatsApp Gateway como Drawer**: `WhatsAppGatewayComponent` migrado a `SideDrawerService` (mismo patrón que POS). Ítem del menú admin abre el drawer deslizable de 520px en lugar de navegar a `/admin/whatsapp`. Componente adaptado: padding reducido, `min-h-screen` eliminado, `max-w-xl` removidos para que los paneles se adapten al ancho del drawer.
- **SingletonLock Fix (Chromium)**: Root cause del error "browser already running" — `SingletonLock` es un symlink; `fs.existsSync()` sigue el symlink y retorna `false` para symlinks rotos. Fix en `manager.ts`: usa `fs.lstatSync()` que detecta el symlink independientemente de si el socket destino existe. Limpia `SingletonLock`, `SingletonSocket` y `SingletonCookie` antes de cada `initializeSession`.
- **Entrega confirmada**: Mensaje `"InternoCore WhatsApp test - canal local multitenant activo"` recibido físicamente en `+526641667684`. LID resolution en logs: `Resolved number +526641667684 -> 263401871777841@lid`.

**Status**: ✅ Phase 124 FULLY COMPLETED — canal WhatsApp verificado de extremo a extremo.

---
### [2026-05-22] Phase 124: WhatsApp E2E Verification + Test Send Endpoint + How-To Docs

**Objetivo:** Confirmar la sesión WhatsApp CONNECTED end-to-end, añadir endpoint de envío de prueba al stack seguro, y documentar el proceso completo de emparejamiento y notificaciones.

**Verificación E2E:**
La sesión WhatsApp fue emparejada exitosamente desde el portal Angular (`/admin/whatsapp`). El polling de `/api/v1/whatsapp/session/status` retorna 200 OK de forma sostenida. El QR Base64 se renderiza correctamente como `data:image/png;base64,...`. Estado final: **CONNECTED** visible en el badge verde del panel.

**Endpoint `POST /api/v1/whatsapp/test-send` (notification_service):**
El schema `TestWhatsAppMessageRequest` ya existía en `whatsapp_routes.py` sin endpoint asociado. Se completó añadiendo el campo `to` (número o group JID) y el handler que actúa como proxy seguro hacia el gateway, protegido por `require_scope(["admin"])` y extrayendo `company_id` exclusivamente del JWT (Muro de Hierro ADR-02). Acepta números en formato `+52XXXXXXXXXX` (auto-normalizado a `@c.us`) o JIDs de grupo (`@g.us`).

**Documentación `docs/howto/whatsapp_pairing_and_notifications.md`:**
Guía operacional completa que cubre el ciclo de vida completo del canal WhatsApp local: arranque del gateway, emparejamiento QR (portal Angular y curl dev), envío de prueba via JWT (stack completo) y directo al gateway, configuración de `WhatsAppGroupMapping` para enrutamiento por área, integración con la Dispatch Matrix del `notification_service`, y tabla de troubleshooting con las causas raíz más comunes.

**Status**: ✅ Phase 124 COMPLETED

---
### [2026-05-21] Phase 123: WhatsApp Local Gateway Completion & E2E Compliance

**Objetivo:** Finalizar la Fase 2 del Gateway Multitenant local de WhatsApp, estabilizar el entorno de desarrollo y generar los reportes de estado del ecosistema (Backend/Frontend).

**Cambios implementados:**
- **Proxy Routes Confirmados (`app/routers/whatsapp_routes.py`)**: Los endpoints de inicialización de sesión, status y código QR funcionan como un Muro de Hierro seguro mediante JWT y ruteo interno, aislando el servicio Node.js.
- **Factoría Multitenant (`whatsapp_factory.py`)**: Resolución dinámica inyectada exitosamente en el flujo principal de `notification_service.py` para usar `LocalWhatsAppClient` o `TwilioWhatsAppClient` según las preferencias del Tenant guardadas en BD, o default del `.env`.
- **Code Graph Compliance Fix**: Se detectó una infracción de seguridad estricta (`ENV_ACCESS_VIOLATION`) en el `notification_app/infrastructure/local_whatsapp_client.py` debido a llamadas crudas a `os.getenv`. Fue refactorizado para usar inyección tipada mediante `pydantic_settings.BaseSettings`, devolviendo el ecosistema a un estado perfecto de `100% Compliance (0 err)` en los 14 servicios.
- **Documentación de Reportes Diarios**: Generados `backend_status_report_20260521.md` (85%) y `frontend_status_report_20260521.md` (80%), evidenciando un progreso firme hacia producción, siendo el mayor bloqueo actual la falta de interfaces (UI) en Angular para visualizar el escaneo QR del Gateway de WhatsApp.

**Status**: ✅ Phase 123 COMPLETED

---
### [2026-05-21] Phase 122: Inter-Service HMAC Hardening (subscription_service Internal Endpoints)

**Objetivo:** Proteger los endpoints internos de `subscription_service` con el mismo patrón HMAC-SHA256 que ya existía en `tickets_service`. Eliminación de dead code en `auth_service`.

**Contexto del problema:**
Los endpoints `GET /internal/status/{company_id}` y `GET /internal/entitlements/{company_id}` de `subscription_service` no tenían ninguna autenticación. Aunque Nginx no los expone externamente (no hay `location /internal` en nginx.conf apuntando a subscription_servers), eran accesibles directamente en el puerto 8002 (dev) y en la red Docker interna sin restricción. Cualquier contenedor en la misma red podía consultar el estado de suscripción de cualquier tenant con solo conocer (o adivinar) el company_id.

**Decisión Arquitectónica — HMAC como contrato inter-servicio:**
Se replicó el patrón existente en `tickets_service/ticket_routes.py`: HMAC-SHA256 del `company_id` con `SECRET_KEY` compartido. El llamador (`auth_service`) computa `hmac(SECRET_KEY, company_id, sha256)` y lo envía en `X-Service-Signature`. El receptor verifica con `hmac.compare_digest` (timing-safe). Sin firma → 403 inmediato, sin revelar detalle.

**Cambios implementados:**

- **`subscription_service/api/v1/endpoints/internal.py`**: Añadida función helper `_verify_service_signature(company_id, signature)` que computa y compara HMAC. Ambos endpoints GET ahora aceptan `x_service_signature: str = Header(None, alias="X-Service-Signature")` y llaman `_verify_service_signature` antes de tocar el repositorio.

- **`auth_service/infrastructure/clients/subscription_client.py`** (el client activo — usado en `select_company_command.py` y `auth_service.py`): Añadida función `_service_signature(company_id)` + `X-Service-Signature` inyectado en el `headers` dict de `get_company_entitlements()`.

- **Eliminado**: `auth_service/infrastructure/subscription_client.py` — dead code (legacy client con URL hardcodeada que nadie importaba; el único caller activo era el legacy mismo). Grep confirma: cero importadores en `auth_service`.

**Workaround / Nota:**
El endpoint `/internal/status/` no tiene caller activo (el legacy client que lo usaba fue eliminado). El endpoint queda protegido igualmente por HMAC para cualquier uso futuro.

**Actualización de workflow:**
`sync-docs.md` actualizado con paso 1.5 (verificación de endpoints internos HMAC), paso 3.6 (verificación WhatsApp Gateway), formato de commit estándar, y criterios de éxito ampliados.

**Verificación:** Code Graph 0 errores, ecosistema 8/8 OK.

**Status**: ✅ Phase 122 COMPLETED

---
### [2026-05-21] Phase 121: Inventory Housekeeping + WhatsApp Local Multitenant Gateway

**Objetivo:** Dos entregables: (1) limpieza estructural de `inventory_service` para preparación a producción, y (2) implementación completa del ecosistema WhatsApp Gateway auto-hospedado multitenant para `notification_service`.

**Fase 1 — Inventory Service Housekeeping:**

Se identificaron y resolvieron 4 anomalías detectadas en auditoría de código:

- **`inventory_app/main.py`**: Bloque de imports duplicado (líneas 72-88 re-importaban los mismos routers ya declarados en la línea 14 y registrados correctamente). Eliminados imports redundantes; imports de `CORSMiddleware`, `Base`, `engine` también eliminados (ya no usados tras migraciones). Declaración `from fastapi import FastAPI, Request, status` consolidada.

- **`scripts/scratch/`** (directorio nuevo): 20 scripts de debug movidos desde la raíz (`check_inventory_tables.py`, `create_dummy_ict.py`, `fix_ict_ids.py`, `inspect_row.py`, `test_db_access.py`, `verify_ict.py`, `error.txt`, `test_out.txt`, et al.). Directorio añadido a `.gitignore`. La raíz del servicio queda limpia.

- **`inventory_app/models/__init__.py`**: `InventoryLocation` verificada como ya presente y expuesta correctamente. No requirió cambios.

- **`requirements.txt`**: Dependencias verificadas como ya pinneadas. No requirió cambios.

**Fase 2 — WhatsApp Local Multitenant Gateway:**

Se implementó el stack completo siguiendo ADR-02 (Proxy Espejo Seguro con Muro de Hierro).

**Nuevo microservicio `backend/whatsapp_gateway/` (Node.js 22 LTS / TypeScript):**
- `src/manager.ts` — `WhatsAppSessionManager` Singleton. `CompanyQueue` por tenant con delay aleatorio 1.5s–3.0s (anti-ban Meta). `LocalAuth` con cookies aisladas en `/app/sessions/session_<company_id>/`. QR convertido a Data URL Base64 (`qrcode.toDataURL`).
- `src/index.ts` — Express con 4 rutas: `POST /api/v1/whatsapp/send`, `GET .../session/:id/status`, `GET .../session/:id/qr`, `POST .../session/:id/initialize`. Bearer auth middleware global. Graceful shutdown SIGTERM.
- `Dockerfile` — Debian con Chromium headless + Puppeteer (args: `--no-sandbox`, `--disable-dev-shm-usage`, `--single-process`).
- `docker-compose.dev.yml` — Servicio `whatsapp-gateway`, puerto `3011:3000`, volumen `whatsapp_sessions_dev:/app/sessions`, red `interno-network`. **No expuesto a través de Nginx** — aislamiento total.

**Refactor `notification_service` — Adapter/Factory Pattern:**
- `app/infrastructure/base_whatsapp.py` — ABC `BaseWhatsAppClient`: `send_group_message(group_id, message, metadata)` + `send_template_message(group_id, template_name, params)`.
- `app/infrastructure/local_whatsapp_client.py` — httpx async client al gateway. `company_id` tomado de `metadata["company_id"]`; error 400 si falta. POST a `{gateway_url}/api/v1/whatsapp/send`.
- `app/infrastructure/twilio_whatsapp_client.py` — Wrapper Twilio existente implementando la interfaz.
- `app/infrastructure/whatsapp_factory.py` — `WhatsAppClientFactory.get_client_for_tenant(db, company_id)`: consulta `company_notification_configs`, resuelve `"local"` o `"twilio"`, soporta BYOK (credenciales propias del tenant en DB) con fallback a credenciales globales.
- `app/core/config.py` — 3 nuevas variables: `DEFAULT_WHATSAPP_PROVIDER`, `LOCAL_WHATSAPP_GATEWAY_URL`, `WHATSAPP_GATEWAY_API_KEY`.
- `app/routers/whatsapp_routes.py` — 3 endpoints proxy espejo con aislamiento JWT (ADR-02): `GET /session/status`, `GET /session/qr`, `POST /session/initialize`. El `company_id` proviene exclusivamente de `current_user.company_id` (JWT verificado) — nunca del path ni del body. Scope: `["admin", "notifications:manage"]`. Helpers DRY `_proxy_get()` / `_proxy_post()` para evitar repetición.

**Workaround / Nota:**
El gateway Node.js no está desplegado aún en el stack de dev (el código existe, pero no se ha ejecutado `docker compose up --build whatsapp-gateway`). Pendiente para la siguiente sesión junto con el escaneo QR inicial.

**Verificación:** Code Graph 0 errores, ecosistema 8/8 OK.

**Status**: ✅ Phase 121 COMPLETED

---
### [2026-05-21] Phase 120: Backend Security Hardening + Frontend Scope/Module Alignment

**Objetivo:** Auditoría de seguridad transversal + corrección de vulnerabilidades Tier 1. Dos vectores de ataque en backend + alineación completa de scopes/módulos en frontend Angular.

**Vector 1 — Iron Wall Violation (inventory_service):**
`inventory.py` (10 endpoints) y `dashboard.py` (9 endpoints) usaban `x_company_id: uuid.UUID = Header(...)` — un header que el cliente controla libremente. Esto viola el Muro de Hierro: cualquier tenant podía acceder a datos de otro tenant simplemente enviando un `X-Company-ID` diferente (IDOR). Fix: todos los endpoints migrados a `token: TokenPayload = Depends(SubscriptionGuard(module_code="INVENTORY_CORE"))` — el `company_id` ahora viene exclusivamente del JWT verificado.

Endpoints corregidos en `inventory.py`: `/movements`, `/reconcile`, `/reserve`, `/release`, `/transfers/dispatch`, `/transfers/receive`, `/stock/{warehouse_id}/{product_id}`, `/stock`, `/audit-export`, `/cycle-count`.

Endpoints corregidos en `dashboard.py`: `/summary`, `/movements`, `/stock`, `/force-release`, `/reports/kardex`, `/reports/valuation`, `/reports/abc`, `/mission-control`, `/consolidated`.

**Vector 2 — Endpoints admin sin autenticación:**
- `auth_service/companies.py`: CRUD completo de empresas (POST/GET/PUT/DELETE) accesible sin ningún guard. Añadida `verify_admin_master_key` a los 5 endpoints.
- `auth_service/seed.py`: `/seed/run` accesible sin guard. Añadida `verify_admin_master_key`.
- `subscription_service/wallet.py`: `/wallet/award` y `/wallet/deduct` (mutaciones de saldo de guest) accesibles sin guard. Añadida `verify_admin_master_key`. Los endpoints de lectura (`/balance`, `/history`) se dejaron abiertos intencionalmente.

**Vector 3 — Audit trail incompleto en hcm_service:**
`bulk_upload` en `collaborators.py` no registraba el evento en `audit_logs`. Añadida llamada `AuditService.log_action(action="COLLABORATOR_BULK_UPLOAD")` con métricas de created/updated/errors antes del `db.commit()`.

**Frontend — Módulos (JWT `modules` claim):**
El JWT de backend incluye un array `modules` (e.g. `["INVENTORY_CORE", "HCM_CORE"]`) que el frontend no capturaba ni exponía. Cambios:
- `domain.types.ts`: Añadido `modules?: string[]` a `AuthSession`.
- `auth.service.ts`: Añadido `modules = computed(() => this.session()?.modules ?? [])` y `hasModule(moduleCode)` (con bypass para SuperAdmin).

**Frontend — Bug 403/401 conflation (multi-tenant.interceptor.ts):**
El interceptor trataba `403 Forbidden` (scope insuficiente) igual que `401 Unauthorized` (token expirado), disparando `auth.logout()` ante cualquier respuesta 403. Un colaborador sin permiso para un endpoint específico era expulsado del sistema. Fix: separar lógicas — 401 → RTR; 403 → `toast.error('Acceso denegado...')` sin logout.

**Frontend — Route guard en /inventory:**
La ruta padre `/inventory` no tenía `canActivate`, permitiendo acceso directo a cualquier ruta hija a usuarios sin scopes de inventario. Añadido `canActivate: [permissionGuard]` con `requiredPermission: ['inventory.stock.read', 'inventory:read', 'inventory.document.create', 'inventory.document.approve', 'inventory.audit.view']` — aceptando ambos formatos de scope (dot-format de colaboradores y colon-format de usuarios invitados).

**Notas de diseño:**
- `/bulk-load` en inventory_service conserva `X-Internal-Secret` — endpoint de comunicación inter-servicio, no expuesto al cliente.
- `master_data_service` tenía todos sus endpoints ya protegidos con `require_scope`. No requirió cambios.
- `subscription_service/admin.py` ya tenía `verify_admin_master_key` en todos los endpoints force-*. No requirió cambios.

**Verificación:** Code Graph 0 errores, ecosistema 8/8 OK.

**Status**: ✅ Phase 120 COMPLETED

---
### [2026-05-20] Phase 119: Variant Table Migration to master_data_db + Point-in-Time Document Reprint

**Objetivo:** Dos entregables en paralelo: (1) mover `inventory_item_variants` de `inventory_db` a `master_data_db` para habilitar typeahead con JOIN directo, y (2) implementar el endpoint de reimpresión de documentos con precios point-in-time (soft-close query).

**Decisión Arquitectónica — Table Migration (inventory_db → master_data_db):**
`inventory_item_variants` era catálogo de datos maestros (cross-reference de proveedores/MPN) que vivía equivocadamente en `inventory_db`. Al estar aislada del `master_data_service`, el método `get_products` usaba un check `has_variants_table` dinámico que siempre devolvía `False` (la tabla estaba en otro DB). Mover la tabla a `master_data_db` permite JOIN nativo en ORM y elimina el anti-patrón.

**Cambios implementados:**
- **Migración master_data** (`alembic/versions/002_add_inventory_item_variants.py`): Crea tabla en `master_data_db` con guard `_table_exists`.
- **Migración inventory** (`alembic/versions/002_drop_inventory_item_variants.py`): Drop de la tabla en `inventory_db`. Downgrade intencional `pass` (migración one-way).
- **Modelo ORM** (`master_app/models/item_variant.py`): `ItemVariant` movido a `master_data_service`.
- **CRUD endpoints** (`master_app/api/v1/endpoints/variants.py`): GET/POST/DELETE con `Security(require_scope(...))`, foto upload via `get_storage_provider()`, upsert por `(company_id, internal_sku, mfg_part_number)`.
- **Proxy inventory** (`inventory_app/api/v1/endpoints/variants.py`): Los 3 endpoints ahora hacen HTTP proxy a `master_data_service` en vez de tocar BD directamente.
- **Repository refactor** (`sqlalchemy_master_data_repository.py`): `get_products` y `get_product_by_sku` reescritos con ORM JOIN sobre `ItemVariant`. Cuando match viene de variante: `p.sku = variant.internal_sku`, nombre enriquecido con `({brand} {mpn})`, precio del campo `unit_price` de la variante.
- **Seed fixes**: `inventory_service/scripts/seed.py` limpiado de `ItemVariant`; `unified_industrial_seed.py` mueve variant seeding de Section 4 (inventory_db) a Section 3 (master_data_db); `flows/seed_variants.py` apunta a `master_data_db`.

**Point-in-Time Document Reprint:**
- **Nuevo endpoint** `GET /api/v1/inventory/documents/{folio}`: Retorna cabecera + líneas del documento con precio al momento de creación.
- **Soft-close query** en `master_data_service`: `GET /prices/products/{id}/price-at?as_of=<datetime>` usando `created_at <= as_of AND (valid_until IS NULL OR valid_until > as_of)`.
- **`MasterDataClient`** ampliado con `get_product_price_at_date()` y `get_product_internal_metadata()`.

**Typeahead result (verificado):**
```
GET /api/v1/products/?q=MPN-GAR
→ "Turbocharger Assembly (Garrett MPN-GAR-701)" | sku: TRB-700 | price: 1200 MXN ✅
```

**Deuda técnica resuelta:**
- `has_variants_table` anti-patrón eliminado.
- Variant seeding desacoplado de `inventory_db`.

**Status**: ✅ Phase 119 COMPLETED — Code Graph 0 errors, ecosystem 8/8 OK.

---
### [2026-05-20] Phase 118: Polymorphic Department Ticket Assignments & Visibility Filters

**Objetivo:** Implementar la Fase 2 del plan de asignación polimórfica de tickets a nivel de departamentos, permitiendo asignación directa a áreas operativas, reseteo inteligente de asignaciones individuales en re-triaje, y visibilidad segmentada para operadores de piso.

- **Modificación del Modelo de Tickets (`ticket.py`)**: Añadido el campo opcional `assigned_department_id` (UUID) indexado para soportar direccionamiento a departamentos sin requerir un ID de colaborador individual.
- **Esquemas Pydantic / DTOs (`ticket_dto.py`)**: Actualizados los esquemas `TicketCreate`, `TicketUpdate`, `TicketRead` y `TicketTriage` para incluir de forma segura `assigned_department_id`.
- **Servicio de Triaje (`triage_ticket` / `ticket_service.py`)**: En el flujo `REASSIGN`, si se proporciona un `assigned_department_id`, el sistema automáticamente limpia las asignaciones individuales previas (`assigned_to_id = None`, `collaborator_id = None`, `external_contact_id = None`), devolviendo el ticket a la cola general del departamento en estatus `ASSIGNED` de forma atómica.
- **Filtro de Visibilidad por Área (`list_by_visibility` / `ticket_repository.py`)**: Ampliada la consulta de visibilidad para aceptar `department_id: Optional[UUID] = None`. Los operadores que pertenecen a un departamento específico ahora pueden visualizar en su bandeja `/mine` todos los tickets que tengan asignada su área/departamento correspondiente.
- **Control de Rutas API (`ticket_routes.py`)**: El endpoint de tickets personales (`GET /mine`) ahora acepta un parámetro query opcional `department_id` para propagar el filtrado de área de forma transparente.

---
### [2026-05-20] Phase 117: Namespace Scope Matching Security Bridge (Collaborator Auth stabilized)

**Objetivo:** Resolver el bloqueo `403 Forbidden` en el flujo de autorización de colaboradores de planta al consultar endpoints de Datos Maestros (`/warehouses`, `/concepts`) integrando resolución de namespaces de seguridad.

- **Resolución de Namespaces de Seguridad (`dependencies.py`)**: Implementado un comparador inteligente de scopes en `common.security.dependencies.require_scope`. Ahora, un scope granular en la base de datos y token del colaborador (ej: `master_data.product.read`) satisface automáticamente la validación gruesa exigida por el endpoint (ej: `master_data:read`).
- **Soporte para Permisos `manage`**: El comparador interpreta automáticamente el sufijo `.manage` como un super-permiso que cubre tanto acciones de lectura (`read`) como escritura (`write`).
- **Remediación de Identidad en Planta (`internal_id` Discrepancy)**: Identificado que el intento fallido de autenticación del operador Carlos Ramírez en el panel web se debió a un desajuste de ID (`003709` vs el valor correcto `003709A` en la base de datos HCM). Al usar la credencial correcta `003709A` o `301`, la autenticación y posterior consumo de catálogos responde con **`200 OK`**.
- **Limpieza de Archivos**: Eliminados scripts temporales de depuración (`debug_roles.py`, `test_scope_fix.py`) para mantener el espacio de trabajo limpio.
- **Validación Automatizada**: El validador del ecosistema local (`validate_ecosystem.ps1`) y el generador de gráfico de código (`generate_code_graph.py`) reportan **100% de cumplimiento y 0 errores**.

---
### [2026-05-19] Phase 116: GOD MODE Smoke Test + Gateway POST Fix + SubscriptionGuard JTI Gate

**Objetivo:** Smoke test E2E del GOD MODE via gateway (puerto 8000). Descubrió y corrigió 2 bugs críticos.

**Bug 1 — nginx `Connection: upgrade` global (impacto: TODOS los POST via gateway → 404):**
`nginx.conf` tenía `proxy_set_header Connection "upgrade"` a nivel `server`, aplicándose a todos los `location` blocks. Uvicorn/ASGI interpreta `Connection: upgrade` como una solicitud de WebSocket upgrade — si no hay `Upgrade: websocket`, devuelve 404. Síntoma: `POST /auth/login`, `POST /admin/elevate` y cualquier POST vía gateway devolvía 404; GET requests funcionaban. Fix: `proxy_set_header Connection ""` a nivel server (limpia el header hop-by-hop para HTTP regular). La location `/ws` conserva sus propios headers `Connection "upgrade"` + `Upgrade $http_upgrade`. Este bug probablemente existía en producción desde la configuración inicial del gateway.

**Bug 2 — `SubscriptionGuard` sin JTI gate (revocación bypass):**
Endpoints con `Depends(SubscriptionGuard(module_code="..."))` leían `TokenPayload` directamente desde `request.state.user_token` (populado por el auth middleware) sin pasar por `get_current_active_user`. Un god-mode token revocado (JTI borrado en Redis) seguía siendo aceptado por estos endpoints. Fix: `SubscriptionGuard.__call__` agrega lookup `GET godmode:{jti}` cuando `token_data.god_mode=True` — mismo fail-safe (Redis unavailable → pass, JWT expira por TTL igual en ≤300s).

**Smoke test E2E — 9/9 pasados vía gateway:**
Clave incorrecta → 401, activación → JTI en Redis, GOD_MODE_ACTIVATED en audit, revocación → Redis DEL, token revocado → 401 en get_current_active_user + SubscriptionGuard, GOD_MODE_REVOKED en audit.

**Status**: ✅ Phase 116 COMPLETED — GOD MODE 100% verificado. Gateway operational para todos los métodos HTTP.

---

### [2026-05-19] Phase 115: GOD MODE Frontend + Security Post-Sprint Hardening

**Objetivo:** Implementar el frontend completo del break-glass panel (Sprint 2) y cerrar 5 gaps de seguridad residuales detectados en revisión post-sprint: nav links faltantes, guard permisivo en security-logs, IP real detrás de Nginx, y ausencia de revocación server-side de JTI.

**Sprint 2 — Angular GOD MODE (5 piezas implementadas):**
- **`GodModeStore` (`core/stores/god-mode.store.ts`)**: Signal store volátil con `providedIn: 'root'`. Signals: `token`, `jti`, `expiresAt`, `attempts`. Computados: `isActive` (verifica `Date.now() < expiresAt`), `isLocked` (≥3 intentos), `secondsRemaining`. `activate()` programa `setTimeout(() => clear(), expiresIn * 1000)` — auto-destrucción garantizada aunque el componente no exista. NUNCA toca `localStorage` ni `sessionStorage`.
- **`godModeInterceptor` (`core/interceptors/god-mode.interceptor.ts`)**: `HttpInterceptorFn` que reemplaza `Authorization: Bearer <god_token>` cuando `store.isActive() === true`. Registrado **al final** del array en `app.config.ts` (corrección crítica: si fuera primero, `multiTenantInterceptor` sobreescribiría el token).
- **`SystemControlComponent` (`modules/admin/system-control.component.ts`)**: Standalone con doble confirmación, input password con toggle show/hide, contador de intentos fallidos `store.attempts() / 3`, banner rojo pulsante con countdown reactivo via `toSignal(interval(1000))`. `closeSession()` limpia el store Y llama `DELETE /admin/elevate/{jti}` (revocación server-side). Master key se limpia del signal inmediatamente tras activación exitosa.
- **`ForensicDashboardComponent` extendido**: Nueva pestaña "Alertas de Seguridad" con `signal<SecurityEvent[]>`. Filas `animate-pulse border-red-300 bg-red-50` para eventos < 24h. Carga lazy al hacer clic en el tab. Nuevo stat-card GOD MODE en el header.
- **Routing + Nav**: Ruta `/admin/system-control` en `app.routes.ts`. Links en sidebar `main-layout.component.ts`: `Auditoría Forense` (ícono `policy`) + `Consola Emergencia` (ícono `emergency`, colores rojos).

**Hardening post-sprint (5 items):**
- **`multi-tenant.interceptor.ts` — stale code eliminado**: Bloque `if (auth.isSuperAdmin()) { headers.set('X-Admin-Master-Key', 'GOD_MODE_ACTIVE') }` removido. Era código muerto del mecanismo break-glass anterior; inyectaba el literal hardcodeado en cada request, no el token real.
- **`GET /security-logs` — guard ampliado**: Condición cambiada de `scopes: ["*"]` exclusivo a `scopes: ["*"]` OR `role in (admin, owner)`. Un admin normal puede ver el audit trail GOD MODE sin necesitar activar una sesión de emergencia.
- **Rate limit IP real**: `multi_layer_key_func` en `limiter.py` ahora lee `X-Real-IP` → `X-Forwarded-For` antes del fallback a `request.client.host`. Nginx ya envía `X-Real-IP` (configurado en `nginx.conf:79`). El rate limit de brute-force en `/elevate` aplica sobre la IP del cliente, no la IP del container Nginx.
- **Revocación JTI en Redis — ciclo completo**:
  - `TokenPayload` extendido: campos `jti: Optional[str]` y `god_mode: bool = False` (parsean del JWT directamente).
  - `/elevate`: tras emitir el token, escribe `SET godmode:{jti} 1 EX 300` en Redis. Si Redis falla, loguea warning — el JWT igual expira por TTL (fail-safe).
  - `get_current_active_user` en `dependencies.py`: para tokens con `god_mode=True`, verifica `GET godmode:{jti}` en Redis. Si no existe → `401 ERR_GOD_MODE_EXPIRED`. Las sesiones normales no pasan por esta verificación (sin degradación de performance).
  - `DELETE /admin/elevate/{jti}`: nuevo endpoint. `DEL godmode:{jti}` en Redis + audit log `GOD_MODE_REVOKED`. Requiere rol admin/owner. Frontend lo llama desde `closeSession()` antes de limpiar el store.
- **TypeScript 0 errores**: `npx tsc --noEmit` limpio. Code Graph 0 CRITICALs en 14 servicios.

**Status**: ✅ Phase 115 COMPLETED — GOD MODE operativo end-to-end (Angular → API Gateway → Auth Service → Redis → Audit DB). Ciclo completo: activación + countdown + revocación manual/automática + audit trail.

---
### [2026-05-18] Phase 114: Mobile Offline-First Sync & UUID Architecture Enforcement

**Objetivo:** Implementar sincronización offline-first local de productos e inventario en la app móvil (Flutter) manteniendo estricta adherencia a la arquitectura determinista del Backend (UUIDs).

- **Sincronización Offline-First**: Implementada la sincronización paginada del catálogo de variantes (`GET /api/v1/inventory/products/{pid}/variants`) inyectando precios jerárquicos y moneda en Drift (SQLite).
- **Hardening de UUID Determinista**: Se eliminó la adaptación incorrecta en el Backend que intentaba hacer "cast" de strings como `'ENT-PUR'` a UUIDs. Se instruyó al ecosistema móvil y scripts de testing a solicitar o usar los UUIDs deterministas asignados a la empresa, garantizando la salud del ruteo FastAPI y la base de datos PostgreSQL.
- **Resolución de Divisas**: Las listas de precios locales resuelven y conservan correctamente la divisa original (`USD` o `MXN`) previniendo que la app asuma `"MXN"` por default gracias a un parseo unificado en `ProductSyncService`.

---
---
### [2026-05-18] Phase 113: Security Hardening Sprint 1 — BOLA Fix, GOD MODE Audit, RLS Protection

**Objetivo:** Remediar los 6 hallazgos críticos/altos identificados en auditoría de seguridad (pentesting estático). Blindar el SaaS multi-tenant frente a BOLA, SQL injection en RLS, price enumeration, y bypass de autenticación no auditado.

- **[C-1] `common/config.py` — Eliminado default hardcodeado `"GOD_MODE_ACTIVE"`**: El `Field` de `int_admin_master_key` ya no tiene `default`. Si `CORE_ADMIN_MASTER_KEY` no está en el entorno, el proceso falla al arrancar (fail-closed). Agregado `@field_validator` que bloquea valores trivialmente conocidos y longitud < 16.
- **[C-1b] `common/middleware.py` — Bypass GOD MODE usa `settings`**: `bypass_tenant` ya no compara contra el string literal `"GOD_MODE_ACTIVE"` — usa `_settings.int_admin_master_key`. Adicionalmente, `/admin/elevate` agregado a `is_public_route` (es un endpoint pre-auth, sin JWT).
- **[C-1c] `subscription_guard.py` — Audit log en cada activación GOD MODE**: Cada activación del break-glass emite `logger.critical` con IP, user-agent, path, trace_id, y persiste en `audit_logs` con `AuditService` via `asyncio.create_task`. El `getattr` fallback con `"GOD_MODE_ACTIVE"` eliminado.
- **[C-2] `common/infrastructure/database.py` — RLS hook blindado**: UUID validado estrictamente antes de interpolación en `SET LOCAL`. `except: pass` reemplazado por `connection_record.invalidate() + raise` — un fallo de RLS ya no es silencioso; invalida la conexión y lanza 500 explícito.
- **[C-3] `inventory_service/pos.py` — BOLA eliminado**: (a) Validación de `warehouse_id` contra `token.company_id` antes de procesar ítems. (b) Query a `products` ahora incluye `AND company_id = :cid`. Ambas rutas usaban `text()` raw que bypassea el `do_orm_execute` interceptor.
- **[H-1] `pos.py` — Price enumeration**: El 400 ya no devuelve `resolved_price` ni SKU — solo `ERR_PRICE_MISMATCH` genérico.
- **[H-3] `pos.py` — `RequirePermission("pos.checkout")`**: Reemplaza el `SubscriptionGuard` raw. Solo usuarios con el slug `pos.checkout` en su JWT pueden procesar checkouts.
- **[H-2] `pos.py` — Float prohibido eliminado**: `float(sale.total_amount)` → `str(sale.total_amount)` en el documento creado (preserva precisión Decimal en DB).
- **`AuditService.log_action()`**: Firma extendida con `ip_address` y `user_agent` opcionales, mapeados a `client_ip` y `user_agent` del modelo `AuditLog`. Eliminado el `print()` de confirmación.
- **`auth_service/core/security.py` — `create_god_mode_token()`**: Nueva función que retorna `(token, jti)` con TTL 300s, claim `god_mode: True`, y JTI único para revocación en Redis. `create_admin_god_token()` legacy conservado (30min, backward compat).
- **`auth_service/admin.py` — `POST /api/v1/admin/elevate`**: Endpoint frontend del break-glass. Rate limit 3/hour, valida key contra `settings`, emite `create_god_mode_token()`, persiste en `audit_logs` con IP/UA/JTI. Retorna `{ access_token, expires_in: 300, metadata.jti }`.
- **`auth_service/admin.py` — `GET /api/v1/admin/security-logs`**: Panel de alertas. Requiere JWT con `scopes=["*"]`. Queries `audit_logs WHERE action LIKE 'GOD_MODE%'` con `ignore_tenant_filter=True`.
- **Validación live**: 5 tests automatizados contra gateway (8000): clave correcta → 200+JTI ✅, clave incorrecta → 401 ✅, sin header → 422 ✅, `/security-logs` con token → 4 eventos ✅, sin token → 401 ✅.
- **Ecosistema**: 8/8 servicios `[ OK ]`, Code Graph 0 CRITICALs en todos los microservicios.
- **Status**: ✅ Phase 113 COMPLETED — Sprint 1 de hardening de seguridad aplicado. BOLA, RLS injection, price enumeration y GOD MODE bypass mitigados.

---
### [2026-05-18] Phase 112: RBAC Full-Stack — DB Seed, JWT Scopes, Angular Guards

**Objetivo:** Cerrar el cortocircuito central del sistema RBAC: la infraestructura de DB, repositorios y guards existía al 100% pero las tablas estaban vacías, por lo que el sistema dependía de `ROLE_SCOPE_MAP` hardcodeado. Esta fase conecta la cadena completa: DB → JWT → Frontend → Rutas.

- **Migración Seed RBAC (`a1b2c3d4e5f6`)**: Creada y aplicada en `auth_service`. Siembra 23 `Permission` slugs granulares, 4 roles sistema (`admin`, `manager`, `warehouse_operator`, `collaborator`) con UUIDs estables, y 33 filas en `role_permissions` (manager: 21, warehouse_operator: 7, collaborator: 5, admin: 0 — wildcard). Idempotente via `ON CONFLICT DO NOTHING` + existence-check por UUID. Corregida la limitación de PostgreSQL donde `NULL ≠ NULL` en unique constraints para evitar roles duplicados.
- **`select_company_command.py` — Extirpación de `ROLE_SCOPE_MAP`**: Eliminado el mapa hardcodeado de 51 líneas. Reemplazado por `_build_scopes()` que detecta admin/owner → `["*"]`, y para otros roles usa los slugs reales de `permission_checker.get_user_permissions()`. Agregado `_load_role_slugs_by_name()` para el fallback de colaboradores industriales (HR Service path).
- **`collaborator_login_command.py` — Scopes desde DB**: Eliminada la lista hardcodeada `["inv:movements:manage", ...]`. Reemplazada por `_load_collaborator_slugs(db)` que consulta la tabla `role_permissions` JOIN `permissions` WHERE `roles.name = 'collaborator'`. Fallback de 5 slugs mínimos si la migración no ha corrido.
- **Validación JWT en vivo**: `full_auth_flow.py` confirma admin → `scopes: ["*"]`. `kiosk_auth_flow.py` confirma 3 colaboradores (Luis Torres RFID, Carlos Ramírez PIN multi-empresa, Ana García) → `scopes: ['inventory.document.create', 'inventory.stock.read', 'master_data.price.read', 'master_data.product.read', 'pos.checkout']`.
- **`auth.service.ts` — 3 bugs corregidos**: (1) `isReadOnly` ya no usa `.includes('read')` en permisos (capturaba `inventory.stock.read` y bloqueaba colaboradores). (2) `isSuperAdmin` usa comparación exacta `r === 'admin' || r === 'owner'` en lugar de `.includes('admin')` (que habría clasificado a managers como super-admins). (3) `collaboratorLogin()` Case B ahora lee `data.scopes || data.permissions` en lugar de hardcodear `['inv:movements:manage']`.
- **`navigation.service.ts` — Blueprint migrado a slugs**: Permisos del menú actualizados a slugs DB (`inventory.stock.read`, `inventory.put_away`, `master_data.product.write`). `isAdmin()` usa `r === 'admin' || r === 'owner' || permissions.includes('*')` — ya no matchea `admin.user.manage` falsamente.
- **`RequirePermission` guard (FastAPI/common)**: Creado en `backend/common/security/require_permission.py`. Compone sobre `SubscriptionGuard` con auto-resolución de `module_code` desde el slug prefix. Corregido el bug de la spec (`module_code="auth_core"` hardcodeado). 0 CRITICALs en Code Graph.
- **`permissionGuard` (Angular)**: Creado en `frontend/src/app/core/guards/permission.guard.ts`. `CanActivateFn` funcional, lee `route.data['requiredPermission']`, soporte OR (array de slugs), bypass `["*"]`. Aplicado en `app.routes.ts`: `/admin/*` → `admin.user.manage`, `/catalog/*` → `['master_data.product.write', 'master_data.product.read']`, `/inventory/audit` → `inventory.audit.view`. TypeScript compila sin errores.
- **`pos.py` — 2 bugs corregidos**: Import de `Decimal` faltante (causaba `NameError` en cualquier checkout con precio resuelto). `quantity_change=item.quantity` → `quantity_change=-item.quantity` (movimientos OUT requieren cantidad negativa para que el ledger descuente stock).
- **Ecosistema**: 8/8 servicios `[ OK ]`, Code Graph 0 CRITICALs.
- **Status**: ✅ Phase 112 COMPLETED — RBAC operativo end-to-end. Scopes granulares en JWT, menú y rutas protegidos.

---
### [2026-05-17] Phase 111: Mobile PDA Sentinel — Hard Reset, Monolith Cleanup & Dynamic Pricing
- **Hard Reset & Dev Stack Consolidation**: Executed a full nuclear reset of the Docker environment (`docker system prune -a --volumes`). Eliminated the stale `interno-monolith` (on-prem stack) in favor of the canonical `infrastructure/docker/docker-compose.dev.yml` microservices stack. The on-prem monolith was a leftover build that created a duplicate `postgres:15` image in Docker Desktop — it is no longer used.
- **Full Rebuild from Zero**: All 7 service images rebuilt fresh (`interno-auth-service`, `interno-master-data-service`, `interno-inventory-service`, `interno-tickets-service`, `interno-subscription-service`, `interno-notification-service`, `interno-hcm-service`) plus Nginx gateway. All migrations applied via `migrate_all.ps1` (✅ all 7 services). Unified seed executed successfully via `unified_industrial_seed.py`.
- **Dynamic Currency Resolution (Master Data)**: Fixed a critical hardcoded `"MXN"` in `product_service.py` `lookup_product_by_code()`. The method now reads the actual currency from:
  1. `PriceAgreement.currency` (B2B contracts)
  2. `ProductPrice.price.currency` (assigned list)
  3. `ProductPrice.price.currency` (fallback to list 1)
  Only falls back to `"MXN"` default if no price object is found at all.
- **QR URL Sanitization (Sales Screen)**: Applied the same URL-parsing logic from `ScannerBloc` (`code.split('/').last`) directly into `sales_screen.dart`'s `onDetect` camera handler. QR codes from `qrto.org/ECM-600` now resolve to `ECM-600` correctly.
- **Ecosystem Health**: All 8 services report `[ OK ]` via `validate_ecosystem.ps1`. Code graph shows 0 `SUBSCRIPTION_GUARD_VIOLATION` — only 23 seed-script cross-service imports (known/acceptable technical debt in `unified_industrial_seed.py`).
- **Status**: ✅ Phase 111 COMPLETED — Dev Stack Hardened, Dynamic Pricing Active, QR Sanitization Unified.

---
 Mobile Navigation Restructure & Price Visual Refactoring
- **Dynamic Shell Restoration**: Switched `setup_screen.dart` auto-login restoration path from `HomeScreen` to `MainNavigationScreen`. This resolves the mobile layout bug on session recovery where the bottom navigation shell (with all tab options and icons) was bypassed, leaving users on a menu-less page.
- **Robust Warehouse Redirection**: Refactored the "Cambiar Almacén" option in `HomeScreen` to pull `company_id` from SharedPreferences and trigger a clean `pushReplacement` to `WarehouseSelectionScreen` rather than calling `Navigator.pop()`, resolving potential layout stack freezing on root-level screens.
- **Price Visual Extensions (Web Dashboard)**: Configured the Angular `ProductPriceListComponent` inside `product-catalog.component.ts` to request a custom wide drawer (`md:w-[750px] w-full`) in all four drawer triggers. This expands the administration panels to easily display multi-tier pricing, taxes, and warehouse logistics data.
- **Master Pricing Integrity**: Successfully pointed product lookups in the mobile repository to `products/lookup/$code` to fetch actual database pricing, resolving previous `$99.99` placeholder inconsistencies.
- **Status**: ✅ Phase 110 COMPLETED — Mobile Navigation Restructured & Pricing Panel Layout Extended.

---
### [2026-05-17] Phase 109: Typeahead Consolidation, Product/Variant/Pricing API & Seed Unification
- **Typeahead API Consolidation**: Debugged and fixed the frontend typeahead that was sending both POST and GET requests to `/api/v1/products?q=`. Confirmed the GET method is the correct one; the POST was a stale endpoint. Updated the Angular `MasterDataService` to use only `GET /products?q=` for product lookup.
- **Product → Variants → Prices Backend API**: Implemented `GET /api/v1/inventory/products/{product_id}/variants` in the `inventory_service` to return item variants with pricing data. Fixed the `GET /products?q=` endpoint in `master_data_service` to return consolidated product data with SKU, variant count, and base pricing.
- **Mobile App Integration**: Updated the Flutter `ProductRepository` to call the same consolidated typeahead endpoint (`GET /products?q=`), replacing the previous dual-call pattern. The mobile scanner now resolves SKU → Product → Variants → Prices in a single API roundtrip.
- **Unified Industrial Seed Consolidation (Docker-Compatible)**: Major refactor of `unified_industrial_seed.py` to eliminate ALL `subprocess.run()` calls that prevented execution inside Docker containers:
  - **Inline Item Variants**: 15 variants (5 products × 3 brands) now seeded via raw SQL `INSERT ... ON CONFLICT DO NOTHING` directly in `seed_inventory()`.
  - **Inline Transfer Prices**: MXN and USD pricing for all 5 products seeded inline in `seed_master_data()`, eliminating the `setup_transfer_prices.py` subprocess dependency.
  - **Inline WMS Locations**: Full Phase 83 industrial layout (3 virtual zones + LOC-AUDIT-01 + 24 rack slots + 6 picking positions = 35 locations) seeded inline.
  - **Inline Shadow Movement Concepts**: Mirror of master_data concepts into inventory_db for cross-db query independence.
  - **Inline Customs Compliance**: Pedimentos and initial inventory movements for 3 companies now use the inventory_db session directly.
- **Status**: ✅ Phase 109 COMPLETED — Typeahead Unified, Seed Docker-Compatible & API Consolidated.

---
- **Subprocess Seed Isolation**: Refactored the `unified_industrial_seed.py` orchestration engine to utilize `subprocess.run` for sub-scripts. This ensures total environment isolation, preventing SQLAlchemy session pollution and `DATABASE_URL` cross-contamination between microservices.
- **HCM Baseline Consolidation**: Engineered a unified `000_hcm_baseline.py` migration, incorporating `collaborators`, `hr_tenant_configs`, and the previously missing `external_contacts` table.
- **Nuclear Reset Validation**: Certified the full system recovery path (Prune -> Migrate -> Seed -> Validate). Successfully seeded the "Triple Identity" layer (Carlos Ramírez, Alicia Torres) into the fresh `hcm_db`.
- **Ecosystem Health Audit**: Confirmed all 8 services are active and properly routed via the Nginx Gateway using `validate_ecosystem.ps1`.
- **Status**: ✅ Phase 108 COMPLETED — Industrial Cold-Start Certified & Seed Isolation Hardened.

---
### [2026-05-16] Phase 107: Inventory Migration Baseline & Schema Stabilization
- **Inventory DB Baseline Implementation**: Engineered a consolidated, idempotent migration baseline (`000_inventory_baseline.py`) for the `inventory_service`. This replaces fragmented and failing migration histories with a single source of truth that correctly initializes 15 core tables, including WAC valuation and industrial WMS hierarchies.
- **Audit & Multi-Tenancy Hardening**: Systematically injected missing audit columns (`created_by`, `updated_by`, `deleted_at`, `transaction_id`) and multitenancy fields across all inventory and notification models.
- **Deterministic Seeding Engine**: Refactored `seed.py` to utilize pre-defined, deterministic UUIDs from the Auth Service (Planta MX, Interno Enterprise). This enables 100% automated, parameter-less bootstrapping of development environments.
- **Ecosystem Health Audit**: Certified the entire 11-microservice backend using `generate_code_graph.py` (100% compliance) and validated the Gateway routing with `validate_ecosystem.ps1`.
- **Infrastructure Cleanup**: Deprecated the redundant `migrate_schema.py` script and optimized `entrypoint.sh` for an Alembic-first migration strategy, ensuring industrial stability during container restarts.
- **Status**: ✅ Phase 107 COMPLETED — Inventory Schema Stabilized & Audit Compliance Hardened.

---
### [2026-05-16] Phase 106: Industrial Auth & Menu Reconciliation
- **Industrial JWT Scope Enrichment**: Patched `collaborator_login_command.py` to include the `scopes` claim within the JWT payload. This ensures that Kiosk/Industrial users (Login T1 Bypass) have consistent sidebar menu visibility and persistence across session refreshes.
- **Frontend Menu Reconciliation**: Analyzed `NavigationService` and `AuthService` (Angular signals) to resolve a visibility gap where industrial permissions (`INVENTORY_READ`) were overriding sidebar scopes (`inv:movements:manage`), resulting in empty menus for collaborators.
- **Kiosk Auth Flow Validation**: Upgraded `kiosk_auth_flow.py` validation script to perform real-time JWT decoding and scope verification, certifying identity propagation for test collaborators (Luis Torres, Ana García).
- **Migration Sweep Expansion**: Updated `migrate_all.ps1` to include `hcm-service` in the unified database maintenance sweep.
- **Status**: ✅ Phase 106 COMPLETED — Industrial Menu Visibility & JWT Scopes Reconciled.

---
### [2026-05-13] Phase 105: Idempotent Monolith Infrastructure Synchronization
- **Zero-Trust Migrations**: Refactored `init` migrations for `auth_service`, `inventory_service`, and `tickets_service` to be fully idempotent using `if not table_exists` logic. This prevents `DuplicateTableError` when deploying over shared databases with pre-existing tables.
- **Schema Auditor v2**: Enhanced `generate_code_graph.py` with `--audit-schema` mode. The auditor now introspects the live PostgreSQL schema and compares it against SQLAlchemy models, detecting missing columns and type mismatches.
- **Phase 83 Implementation**: Formally integrated 16+ missing columns in `inventory_locations` (Hierarchical Addressing, Density Guard, Volumetric Limits) via a formal Alembic migration (`c83f_phase83`).
- **Alembic Version Sync**: Successfully marked version tables (`alembic_version_auth`, `_inv`, `_tickets`) in the shared database to ensure consistent migration tracking.
- **Gateway Resilience**: Patched `nginx.conf` to gracefully handle missing microservices in the current dev stack (commented out non-existent upstreams), restoring the Gateway to `[ OK ]` status.
- **Status**: ✅ Phase 105 COMPLETED — Infrastructure Synchronized & Idempotency Hardened.

---
### [2026-05-12] Phase 104: Microservices Isolation & Cross-Service Import Eradication
- **Cross-Service Import Guard**: Enhanced `generate_code_graph.py` to detect and report `CROSS_SERVICE_IMPORT_VIOLATION` as CRITICAL errors. Matches both `*_service` and `*_app` module patterns.
- **Decoupled inventory→notification**: Replaced direct `from notification_app...` imports in `density_guard_audit.py` and `transactions.py` with async HTTP event dispatch via `httpx` to `notification-service:8000/api/v1/events/`.
- **Decoupled notification→auth**: Replaced `from auth_app.models...` ORM imports in `notification_service.py` with raw SQL `text()` queries against shared tables (`users`, `roles`, `user_company_roles`).
- **Gateway Stabilized**: Fixed Nginx crash loop caused by undefined `wms-service` upstream (commented out WMS until deployed). Added `hcm-service` and `notification-service` upstreams and location blocks.
- **Redis Dependency**: Added `redis==5.0.1` to `common/requirements.txt` — required by `InternoCoreGlobalMiddleware` across all services.
- **HCM Dockerfile Fix**: Corrected `COPY hcm_service/app` → `COPY hcm_service/hcm_app` to match Gold Standard naming.
- **Alembic Zero-Collision**: All 7 services now use unique `version_table` names (`alembic_version_auth`, `_sub`, `_md`, `_inv`, `_tickets`, `_notif`, `_hcm`).
- **Industrial Entrypoints**: All services implement `entrypoint.sh` with Migrate→Seed→Serve lifecycle.
- **Documentation**: Created `backend/README.md` with Gold Standard microservice template. Updated `infrastructure/README.md` port matrix (8001-8009).
- **Ecosystem Validator**: Created `scripts/validate_ecosystem.ps1` — integrated into `initialize-dev.md` and `sync-docs.md` workflows.
- **Code Graph Result**: 0 CRITICAL, 0 CROSS_SERVICE violations, 2 minor WARNINGs (ENV_ACCESS in inventory — acceptable for Docker network defaults).
- **Status**: ✅ Phase 104 COMPLETED — Microservices fully isolated, Gateway operational, Code Graph clean.

---
### 🌟 [2026-05-12] GOLDEN BASELINE ESTABLISHED
**Estatus:** Phase 100 (Big Bang — 1M Records) ✅ COMPLETED. Industrial performance verified at 25k rec/s. Environment cleaned and stabilized.

---

### [2026-05-12] Phase 103: Infrastructure Industrialization & Gateway Unification
- **Standardized Orchestration**: Refactored all Docker configurations into a centralized `infrastructure/` directory, isolating `docker/` (Dev Microservices) from `onprem/` (Production Monolith).
- **Nginx Gateway (Port 8000)**: Implemented a unified entry point for microservices. This enables Frontend (Angular) and Mobile (Flutter) clients to communicate with the entire ecosystem through a single port, maintaining parity with the Monolith architecture.
- **Bulletproof Startup (Healthchecks)**: Integrated Docker Healthchecks for `postgres` and `redis`. Configured service dependencies (`service_healthy`) to ensure 100% connection reliability during cold starts, eliminating transient 500/Restarting errors.
- **Unified Migration Engine**: Developed `migrate_all.ps1`, a PowerShell orchestrator that performs a "Migration Sweep" across all active microservices using Alembic.
- **Nuclear Reset Protocol**: Updated `hard-reset.md` with forensic system pruning, recovering 11GB+ of storage and ensuring zero network/volume collisions.
- **Status**: ✅ Phase 103 COMPLETED — Infrastructure Industrialized & Gateway Unified.

### [2026-05-12] Phase 102: Sentinel Móvil & Industrial POS Resilience
- **Functional Resilience Port**: Successfully ported the Sentinel architecture to Flutter (`interno_billing_app`).
    - **Real-Time Connectivity Sensor**: Integrated `connectivity_plus` to trigger the "Offline" state via hardware sensors, achieving < 100ms reaction time.
    - **Backoff & Idempotency**: Implemented `ResilienceInterceptor` with exponential retries and per-request `X-Idempotency-Key` generation.
    - **Wakelock Protection**: Integrated `wakelock_plus` to prevent device sleep during critical synchronization and recovery windows.
- **Architecture Refactor**: Standardized the `Dio` interceptor chain: `MultiTenant` -> `Resilience` -> `AuditLog`.
- **Status**: ✅ Phase 102 COMPLETED — Mobile Resilience Certified & Production Ready.

### [2026-05-12] Phase 101: Resilience Stress-Test & Kill Switch Certification
- **Definitive Chaos Test (V4)**: Successfully executed a 1,000,000 record injection while performing a controlled DB "Kill Switch" (10s outage). Verified:
    - **Silent Recovery**: The pool (`pool_pre_ping=True`) automatically re-established connectivity without backend restarts.
    - **Idempotency Protection**: Integrated `X-Idempotency-Key` prevented duplicate records during loader retries.
- **Resilience Audit**: Documented full certification in `docs/audit/resilience_audit_v4.md`.
- **Status**: ✅ Phase 101 COMPLETED — Industrial Recovery & Idempotency Certified.

### [2026-05-12] Phase 4.2: Resilience Auditing & "Sentinel" Frontend
- **Frontend Sentinel (`resilience.interceptor.ts`)**: Implemented exponential backoff (2s, 4s, 8s) for transient network errors (Status 0/503) and semantic recovery codes (`DATABASE_RECONNECTING`).
- **Idempotency Stability**: Interceptor now guarantees the SAME `X-Idempotency-Key` is used during retries of a single request instance, preventing server-side duplication.
- **Backend Exception Semantics**: Patched `InternoCoreGlobalMiddleware` to inject domain exception `code` into the JSON response `meta` object.
- **Frontend Error Mapper**: Refactored `error-mapper.ts` to map semantic codes (e.g., `DATABASE_RECONNECTING`) to informational UX components.
- **SQLAlchemy Auto-Reconnect**: Injected `pool_pre_ping=True` across all 14 microservices, ensuring "Stale Connections" are cleanly dropped upon DB reboot.
- **Status**: ✅ Phase 4.2 COMPLETED — Frontend Sentinel Active & Connection Resilience Hardened.

---

### [2026-05-12] Phase 4.1: Industrial Infrastructure Consolidation & Ignition Ready
- **Multi-Stage Containerization**: Refactored Monolith and Microservices Dockerfiles from single-stage to Multi-Stage alpine/distroless environments. Extracted C libraries/build tools (`gcc`, `build-essential`) leaving only the runtime binaries, drastically reducing the image footprint and attack surface.
- **Zero-Trust Connectivity**: Hardened Alembic migrations and application entrypoints to force `ssl=require` on Postgres connections. Ensured Secret Manager (AWS) dynamic resolution via `boto3` when `ENV_MODE=production`.
- **On-Premise Standard Operating Procedure (SOP)**: Created an encapsulated deployment package in `infrastructure/onprem` containing a clean `docker-compose.yml`, `init_db.sh` (with healthchecks), and `migrate.sh` specifically adapted for monolithic orchestrations.
- **Auditor Defense Verification**: Remedied a severe regression in `master_data_service` caused by an automated `git checkout`. Developed a dynamic Python script to re-inject `Security(require_scope)` across 63 endpoints, restoring the Muro de Hierro Code Graph Auditor to 100% Compliance.
- **Status**: ✅ Phase 4.1 COMPLETED — Backend is "Ignition Ready" for AWS VPC Deployment.

---

### [2026-05-12] Phase 3: Industrial Domain Parity & CQRS Finalization
- **Float Extermination Guard**: Replaced all `float` datatypes across models and schemas with the unified `Decimal` and `Money` Value Objects. Engineered a Code Graph Invariant (`PRIMITIVE_FLOAT_VIOLATION`) to actively prevent float contamination in core architectures, securing financial and volumetric calculations.
- **WMS CQRS Atomicity**: Refactored inventory transaction flows into atomic handlers (`TransferStockHandler`, `CreateSalesOrderHandler`) governed by the Unit of Work pattern (`db.begin_nested()`). Implemented strict optimistic locking (`with_for_update()`) to prevent stock-deduction race conditions during industrial throughput.
- **Subscription Governance Hardening**: Developed `ChangeSubscriptionPlanHandler` bridging financial tracking (`BillingEvent`) with identity scopes. Hardened the downgrade validation algorithm (Quota Invariant) to verify that current multi-tenant storage consumption does not exceed the incoming plan's limits, rejecting the transaction instantly otherwise.
- **Code Graph Evolution**: Deployed `CQRS_QUERY_VIOLATION` and `CQRS_ATOMICITY_WARNING` invariants into the static auditor. Rewrote all legacy handlers in `wms_service` and `auth_service` to conform with explicit `begin_nested()` blocks, achieving a pristine 100% Compliance rate across all 14 microservices.
- **Status**: ✅ Phase 3 COMPLETED — CQRS Architecture Stabilized & Float Precision Eradicated.

---

### [2026-05-12] Phase 2: Identity & Access Audit (Heartbeat & Scope Hardening)
- **Granular Scope Enforcement**: Engineered the `require_scope` dependency factory in `common.security.dependencies.py`. Injected `Dependencies(require_scope(["x:read"]))` into high-risk endpoints (WMS locations, MES work orders) to enforce exact RBAC permissions, closing validation gaps.
- **Session Heartbeat (Real-time Revocation)**: Implemented an asynchronous Redis blocklist check within `get_current_active_user`. This "Heartbeat" validates the `blacklist:{user_id}` key, instantly revoking compromised JWTs. Backed by a 5-minute In-Memory Local Cache to absorb heavy frontend traffic without DB/Redis saturation.
- **Cryptographic Hardening**: Upgraded the core password hashing algorithm (`bcrypt`) to `work_factor=12` across the identity layer.
- **Seed Synchronization**: Unified `auth_service/scripts/seed_standalone.py`, `seed.py`, and `unified_industrial_seed.py` to correctly map `Planta MX` and `Planta US` to the central `Interno Global Operations` Business Group, enforcing environmental SSOT.
- **Status**: ✅ Phase 2 COMPLETED — Industrial Identity Hardened & Access Control Standardized.

---

### [2026-05-12] Phase 5: RLS Muro de Hierro & Database Governance
- **Postgres RLS Foundation**: Engineered and deployed dynamic PL/pgSQL Alembic migrations enforcing `ROW LEVEL SECURITY` and `FORCE ROW LEVEL SECURITY` on all tables possessing a `company_id`.
- **Tenant Context Interceptor**: Activated global `do_orm_execute` and `checkout` connection listeners in the Unified Monolith (`common.infrastructure.database`). These inject the `app.current_tenant` context directly into Postgres session variables (`SET LOCAL app.current_tenant`), executing a `RESET` on connection return to prevent leakage across pooled sessions.
- **Microservice DB Decommissioning**: Deleted obsolete local `database.py` files in `mes_service`, `subscription_service`, and `wms_service`, refactoring all layers to strictly consume the global `common.infrastructure.database` to ensure 100% Muro de Hierro compliance.
- **Code Graph Strict Guard**: Integrated strict `MURO_DE_HIERRO_VIOLATION` validations into the Code Knowledge Graph Generator to ensure no service bypasses the global tenant interceptors. Verified 100% Compliance.
- **Status**: ✅ Phase 5 COMPLETED — PostgreSQL Row Level Security Active & Monolithic DB Engine Unified.

---

### [2026-05-12] Phase 100: Big Bang — Industrial Stress Test (1M Kardex Records)
- **Administrative Bypass Engine**: Implemented `X-Internal-Secret` header bypass in `common/security/limiter.py`. When the secret matches `CORE_INTERNAL_API_KEY`, the `multi_layer_key_func` returns `None`, exempting the request from rate limiting. Same bypass available via `X-Admin-Master-Key` (God Mode).
- **High-Performance Bulk Load Endpoint**: Created `POST /api/v1/inventory/bulk-load` in `inventory_service`. Uses SQLAlchemy `insert()` with `executemany` for atomic batch insertion. Maps string transaction types to `TransactionType` Enum to prevent DB type mismatches.
- **Nuclear Docker Cleanup**: Performed deep cleaning of Docker environment, removing all project images and volumes. Executed `docker network prune` to eliminate unused custom networks, leaving only standard Docker defaults (`bridge`, `host`, `none`) and active project networks.
- **The Big Bang Execution**: Successfully injected **1,000,000 Kardex records** into the Unified Monolith.
    - **Performance**: 39.9 seconds total.
    - **Throughput**: ~25,058 records per second.
    - **Integrity**: 1,000,000 records verified in `inventory_transactions` table via psql.
- **BOM Encoding Fix**: Discovered that PowerShell's `echo >>` and `Set-Content -Encoding utf8` inject UTF-8 BOM (`\xef\xbb\xbf`) into `.env` files, which `python-dotenv` silently fails to parse. Solution: strip BOM bytes and use `dotenv_values()` dict merge.
- **Hard Reset Workflow Updated**: Added BOM sanitization as Step 1 in `.agent/workflows/hard-reset.md`.
- **Status**: ✅ Phase 100 COMPLETED — Industrial Scale Verified (1M Records Persisted).

---


---

### [2026-05-12] Phase 99: Iron Wall (Rate Limiting Resilience & Multi-Tenant Isolation)
- **Centralized Rate Limiting (Redis-Backed)**: Deployed a production-grade rate limiting engine using `slowapi` and `Redis`. Integrated the limiter into the Unified Monolith to protect industrial endpoints from traffic bursts and DoS attacks.
- **Multi-Layer Key Identification**: Engineered a sophisticated identification strategy (User > Tenant > IP) that ensures quotas are enforced at the tenant level, preventing one company's activity from affecting another.
- **Connection Resilience Hardening**: Patched the `RateLimitExceeded` exception handler to handle Redis connection failures gracefully, preventing 500 errors when the storage layer is under maintenance.
- **Docker Stack Optimization**: Unified the Redis storage into the `docker-compose.monolith.yml` stack, ensuring a consistent network environment and simplified orchestration.
- **Industrial Stress Validation**: Successfully executed the `test_rate_limit_resilience.py` suite, achieving a 100% pass rate in tenant isolation and log-spam suppression.
- **Documentation Sync**: Updated the `RATE_LIMIT_TEST_PROTOCOL.md` and consolidated daily task and implementation history logs.
- **Status**: ✅ Phase 99 COMPLETED — Perimetric Security Hardened & Multi-Tenant Isolation Verified.

---

 
### [2026-05-12] Phase 98: Cloud Decommissioning & Infrastructure Serialization (ADN Extraction)
- **AWS Account Forensic Audit**: Conducted a final forensic sweep of the AWS environment (`us-east-1`, `us-east-2`). Identified and neutralized residual "ghost" resources including an active secret in Secrets Manager and an empty S3 logging bucket, achieving a verified $0.00 cost state.
- **Infrastructure Serialization (The Recipe)**: Extracted and serialized the technical "ADN" (VPC topologies, IAM Muro de Hierro policies, and CloudFront OAC configurations) into `docs/infraestructura/backup_configs/`.
- **New Account Deployment Engine**: Developed `deploy_to_new_aws_account.ps1`, a parameterized orchestration script that enables 1-click redeployment into any fresh AWS account without hardcoded ID dependencies.
- **Master Resurrection Guide**: Authored `AWS_RESURRECTION_GUIDE.md` and a comprehensive `README.md` for the infrastructure directory, establishing a clear path for cloud-restoration in future scale-up phases.
- **Structural Reorganization & Root Cleanup**: 
    - Migrated all satellite projects (`english-interview-trainer`, `interno_billing_app`, `viatra-frontend`) to the `src/` directory, centralizing the frontend/mobile ecosystem.
    - Neutralized nested `.git` directories to ensure direct tracking within the Unified Monolith repository.
    - Purged legacy `logs/`, `tmp/`, and `scratch/` directories from the root, archiving useful historical data into `docs/historial/legacy_archive/`.
    - Established `scripts/SCRIPTS_MANIFEST.md` as the SSOT for operative tools.
- **Security Vault & Hygiene**: Established a local `vault/` directory (protected by `.gitignore`) to house sensitive credentials (Access Keys, Twilio codes) locally while ensuring Zero-Trust compliance for the source code.
- **Compliance & Documentation**: Verified 100% compliance in the Code Graph Audit and updated the `Forensic_Audit_Report.md`.
- **Status**: ✅ Phase 98 COMPLETED — AWS Account Decommissioned, Infrastructure Recipe Preserved, and Root Purified.

- **Frontend Interceptor Fix (Angular)**: Resolved critical `401 Unauthorized` block on `/auth/delegate-selection` by exempting the endpoint from automatic context-header injection in `multi-tenant.interceptor.ts`. This enables authenticated users to generate QR delegation tokens without triggering circular auth rejections.
- **QR Payload Standardization (Zero-Trust)**: Updated `pos-link-drawer.component.ts` to use a dynamic host (`10.0.2.2` for emulator/localhost fallback) and strictly enforced `snake_case` JSON keys (e.g., `selection_token`, `company_id`) to ensure seamless parsing by the mobile ecosystem.
- **Mobile Handshake Hardening (Flutter)**: 
    - Refactored `LoginScreen` QR parsing to support both legacy `camelCase` and new `snake_case` keys, ensuring backwards compatibility during transition.
    - Optimized the `Dio` interceptor in `injection.dart` to ignore auth routes, preventing session-collision errors during the T1/T2 handshake.
- **Database Schema Consistency**: Manually resolved a `500 Internal Server Error` in the `/api/v1/partners` endpoint by adding the missing `price_list_index` column to the `partners` table (forensic patch).
- **Security Life-cycle Alignment**: Verified and documented a **12-hour (720 min)** access token lifespan in `security.py` to support extended shifts in industrial environments.
- **Monolith Re-initialization**: Executed a full environment restart and re-seeding via `initialize-monolith.md`, achieving 100% compliance in the Code Graph Audit.
- **Status**: ✅ Phase 97 COMPLETED — Industrial Mobile Handshake Stabilized & QR Sync Verified.

### [2026-05-10] Phase 96: Database Integrity & Backend Robustness (Fix 500 Errors)
- **POS Lookup Hardening (ECM-600 Fix)**: Resolved critical `500 Internal Server Error` in the product lookup flow.
    - **Root Cause**: SQL unique constraints in PostgreSQL treat `NULL` values as distinct, allowing multiple active prices for the same product/list when re-seeding without warehouse IDs.
    - **Robustness Fix**: Updated `ProductService` to use `.first()` and `order_by(created_at.desc())` instead of `scalar_one_or_none()`, ensuring the system gracefully handles legacy or duplicate data by picking the most recent valid record.
- **Database Sanitization**: Purged 135 duplicate price records from `product_prices` to restore immediate operational health.
- **Seed Idempotency**: Reverted `unified_industrial_seed.py` to its original state while maintaining system stability through backend-level resolution logic.
- **Mobile App State**: Industrial UX (Glove-ready) validated. **Hardware Stability**: Addressed `BLASTBufferQueue` exhaustion (ret=2) on Moto g04s via active texture pruning. **Pending Tomorrow**: Adapt the Flutter auth flow to strictly match the backend T1/T2 handshake.
- **Status**: ✅ Phase 96 COMPLETED — Database Integrity Restored & POS Lookup Stabilized.

### [2026-05-10] Phase 95: Industrial Mobile POS Identity Hardening (Zero-Trust QR)
- **Zero-Trust QR Delegation (Selection Token)**: Engineered a new "delegated handshake" protocol. The web portal now issues short-lived `selection` tokens via `/auth/delegate-selection`, which are encoded in the QR. This ensures the mobile device is responsible for generating its own final session JWT, maintaining strict Zero-Trust principles.
- **Entitlement Propagation Hardening**: 
    - Updated `unified_industrial_seed.py` to populate `Subscription` and `Entitlement` records for all primary industrial tenants.
    - Verified the presence of the `inventory_core` module in the global entitlement matrix, resolving `403 Forbidden` errors during POS checkout.
- **SubscriptionGuard Refactor (Scope Bypass)**: Enhanced the transversal `SubscriptionGuard` to allow `*` (super-admin) scope bypass. This prioritizes granular permission scopes over module-level lockdowns for administrative and provisioning scenarios.
- **Mobile Industrial UX (Glove-Ready)**:
    - Increased the `Quantity` input touch-target and font size in the `ScannerScreen` to accommodate operators wearing industrial gloves.
    - Physically removed the `MobileScanner` widget from the tree during modal/sheet transitions to clear `BLASTBufferQueue` hardware locks on Mali GPU (Moto g04s).
- **Status**: ✅ Phase 95 COMPLETED — Industrial Identity Hardened & Zero-Trust QR Operational.
- **PENDING (Next)**: 
    1. **Transactional Bulk Test**: Verify atomic stock deductions for carts with 50+ mixed SKUs.
    2. **Warehouse Mapping**: Implement dynamic warehouse discovery in the mobile selection flow.
    3. **Offline Buffer**: Design a local SQLite buffer for offline scanning in low-connectivity zones.

### [2026-05-10] Phase 94: Industrial Mobile POS Cockpit Stabilization (Moto g04s)

### [2026-05-09] Phase 93: Hierarchical Pricing ("Onion Layers") & B2B Mobile POS
- **Hierarchical Price Resolution ("Onion Layers")**: Implemented a 4-layer resolution engine (Agreement > Warehouse > Assigned List > Public List) in the backend `lookup` and `pos_checkout`. This ensures strict commercial compliance and prevents price manipulation in the field.
- **B2B Mobile POS Integration**: Developed a real-time `Partner` search and selection module in the Flutter app. Operators can now link transactions to specific customers, automatically triggering personalized B2B pricing agreements during the scanning process.
- **Mobile Code Graph Auditor**: Engineered and deployed `generate_mobile_graph.py`, a specialized architectural auditor for Flutter. It enforces Clean Architecture, detects hardcoded URLs, validates theme compliance, and ensures multi-tenancy header integrity in the mobile ecosystem.
- **Brand Identity Update**: Renamed the mobile ecosystem to **INTERNO POS**. Updated Android labels, internal titles, and UI headers to reflect the new industrial positioning.
- **Backend Enforceability**: Hardened the `inventory_service` to perform server-side price validation against the master data resolution engine, ensuring that even if a client-side override is attempted, the transaction is rejected unless authorized.
- **Status**: ✅ Phase 93 COMPLETED — B2B Pricing Hierarchy Operational.
- **PENDING (Next)**: 
    1. **Logistics Entry Flow**: Implement scanning and validation from receiving documents (Entradas).
    2. **"Price-less" Validation**: Enable pure counting flows for inventory audits where price metadata is not required.
    3. **Stock Deductions**: Finalize atomic stock deductions for completed mobile transactions (already validated in Phase 91, but requires full loop check with B2B).
    4. **Proactive Notifications**: Implement a "Pending Receipts" counter/indicator on the Scanner dashboard.
    5. **Warehouse Management**: Add a warehouse selector to the Login/Setup flow.

### [2026-05-08] Phase 92: Industrial POS Architecture & Global State Persistence

### [2026-05-08] Phase 91: Industrial Mobile POS Integration & Zero-Trust Provisioning
- **Zero-Trust Provisioning (QR Handshake)**: Engineered a high-performance terminal configuration protocol. Mobile devices now scan a dynamic QR from the web portal to inherit `baseUrl`, `accessToken`, `companyId`, and `warehouseId`, eliminating setup friction for operators.
- **Mobile POS Checkout Flow**: Implemented atomic inventory commits in the `inventory_service` via `POST /api/v1/pos/checkout`. Supports real-time SKU resolution and multi-tenant stock validation.
- **Dynamic Configuration UI**: Developed a hidden "Setup Mode" (Long-press logo) in the Flutter app to allow terminal re-provisioning without re-installation.
- **Frontend POS Link Drawer**: Added a glassmorphic "Vincular POS" panel in the user menu of the Angular portal for instant terminal pairing.
- **Compliance & Audit**: Verified 100% compliance in the Code Graph Audit for the new POS endpoints.
- **Status**: ✅ Phase 91 COMPLETED — Mobile POS Ecosystem Operational & Provisioned.

### [2026-05-08] Phase 90: Supplier Access Industrialization & Audit Evolution
- **Supplier Landing Page**: Finalized `landing/ticket-access.html` — a standalone glassmorphic portal where external providers can view ticket details, SLA countdown (72h), intervention history, and submit comments/evidence using their industrial token.
- **Outbox Worker Integration**: Connected `OutboxWorker` to process `EXTERNAL_ASSIGNMENT` events from `outbox_events`, forwarding them to the `notification_service` via HTTP with company-scoped headers for guaranteed at-least-once delivery.
- **Industrial Flows Simulator (v2)**: Upgraded `IndustrialFlowsComponent` from mock `setTimeout` to real HTTP traffic — now creates 3 tickets and triages them across the Triple Identity (Internal/Plant/External) using `SupportService`, fully auditable in browser Network tab.
- **Code Graph Audit Evolution (Phase 90)**:
    - **Smart Tenant Exclusions**: Methods named with `external_token`, `escalation`, `public`, `global`, `cron`, `webhook`, `migration` are automatically exempt from `MISSING_TENANT_FILTER` without requiring docstring annotations.
    - **Public Data Leakage Guard**: New invariant that flags public endpoints serializing sensitive fields (`company_id`, `tenant_id`, `created_by`).
- **Compliance**: 14/14 microservices at **100% Compliance** — 0 errors.
- **Status**: ✅ Phase 90 COMPLETED — Supplier Portal Operational, Audit Script Hardened.

### [2026-05-08] Phase 89: Triple Identity Triage & Security Hardening
- **Triple Identity Architecture**: Unified `Collaborator` (Physical) and `ExternalContact` (External) identities within the `TicketsService`, enabling a comprehensive triage system that bridges digital and industrial operations.
- **Automated Validation Flows**: Engineered a suite of validation scripts (`backend/tickets_service/scripts/flows/`) to ensure architectural integrity:
    - **Load Balancing (LB)**: Verified the automatic release of internal licenses when tickets are reassigned to external providers.
    - **SLA Enforcement**: Implemented strict 72-hour window validation for external access tokens, ensuring forensic security of industrial data.
    - **Multi-tenant Quotas**: Integrated real-time storage limit validation against active subscription plans (`storage_limit`) for external evidence uploads.
- **Outbox Event Integration**: Standardized the `EXTERNAL_ASSIGNMENT` event flow in `outbox_events` for guaranteed asynchronous notification delivery to providers.
- **Compliance & Governance**: Resolved `ENV_ACCESS_VIOLATION` in the tickets service and reached 100% compliance in the Code Knowledge Graph Audit.
- **Frontend Monolith Gateway**: Synchronized the Angular environment to route all traffic through the Unified Monolith (Port 8000), eliminating CORS and routing deadlocks.
- **Status**: ✅ Phase 89 COMPLETED — Triple Identity Triage Hardened & Automated.

### 🗓️ Mayo 2026: Motor Operacional Industrial (Tickets Service & CMMS)

### [2026-05-05] Phase 88: Landing Page Industrialization & i18n Implementation
- **Landing Page Industrialization**: Developed a premium, production-ready landing portal using Vanilla CSS with high-fidelity glassmorphic aesthetics. Integrated industrial branding for Carlos Flores Montoya as the Master Architect.
- **i18n Dynamic Engine**: Engineered a lightweight JavaScript i18n client (`app.js`) that dynamically swaps content based on `data-i18n` attributes. Supports nested JSON keys and real-time language switching (ES/EN) without page reloads.
- **Sales-Focused Narrative**: Refined the entire system narrative to eliminate technical jargon. Replaced complex terms (SSOT, RBAC, O(1)) with benefit-driven language focused on **Inventarios, Catálogos, Socios y Productos**.
- **Tiered Plan Transparency**: Developed a dedicated technical comparison page (`plans.html`) with precise feature differentiation. Corrected plan boundaries: the **Plan Operativo** explicitly excludes Work Orders (MES) and Maintenance (CMMS) to drive industrial tier upgrades.
- **Production-Ready Pricing**: Standardized all pricing to explicit **USD** notation with clear feature-by-feature comparisons.
- **Status**: ✅ Phase 88 COMPLETED — Landing Portal Production-Ready & Multi-language.

### [2026-05-05] Phase 87: Rescue and Observability (Muro de Hierro - Stage 2)
- **Reactive Subscription Webhooks**: Deployed `/api/v1/webhooks/stripe` listener within the monolith. This endpoint seamlessly processes `payment_failed` and `payment_succeeded` events to toggle multitenant `PAST_DUE` states and activate the "Muro de Hierro" in real-time.
- **Subscription Recovery Service**: Implemented `SubscriptionRecoveryService` integrated into the monolith startup sequence. If the local database is wiped, the system automatically pulls active subscriptions from Stripe API to reconstruct environmental continuity deterministically.
- **Forensic Industrial Dashboard**: Built the `ForensicDashboardComponent` in the Angular frontend (`/admin/forensic`). Engineered real-time visualization of the `audit_logs` table with a custom 5-minute polling interval to maintain network efficiency while providing a "red-alert" kill-switch visualization for blocked 402 access attempts.
- **Audit Logging Augmentation**: Hardened the `SubscriptionGuard` to intercept 402 rejections and proactively inject `ACCESS_DENIED_402` events into the forensic ledger prior to raising HTTP Exceptions, closing the traceability loop on unauthorized mutations.
- **Documentation Hub Unification**: Engineered an automated workflow (`inject_docs_html.py`) to systematically gather all `.md` engineering logs across microservices and inject them into a massive, searchable "Documentation Hub" directly within the core `DOCS_INTERNOCORE.html` artifact.
- **Status**: ✅ Phase 87 COMPLETED — Forensic Traceability and Stripe Synchonization fully operational.

### [2026-05-05] Phase 86: Hardening Identity & Audit (Muro de Hierro Validation)
- **Forensic Audit Injection**: Successfully injected `SecurityAuditLog` tracking into the industrial login workflow. Every physical authentication event (RFID/PIN) now captures `transaction_id`, client IP, and role snapshots for permanent forensic record.
- **SubscriptionGuard Refinement**: Hardened the transversal `SubscriptionGuard` with support for `GOD_MODE_ADMIN` overrides via the `X-Admin-Master-Key`. Standardized error responses with `trace_id` metadata for high observability.
- **Identity Unification**: Linked industrial collaborators (`Carlos Ramírez`) with administrative users (`Charly Flores`) in the HCM seed, establishing the SSOT for cross-domain identity correlation.
- **Global Settings Hardening**: Centralized the `int_admin_master_key` in the global `InternoSettings` to ensure consistent "God Mode" enforcement across the monolith.
- **Muro de Hierro Validation (100% Pass Rate)**: Successfully executed the `validate_muro_hierro.py` suite. Verified Identity Linkage (RFID mapped to core identities), Auth Guard (rejection of invalid credentials), Subscription Guard (402 enforcement for PAST_DUE state), and God Mode Bypass (override capabilities).
- **Forensic Audit Integrity**: Fixed the `AuditLog` listener in the Master Data service by adding missing mandatory constraints (`is_active`, `version_id`) and multitenancy fields (`company_id`, `tenant_id`) to raw SQL inserts, resolving database `IntegrityError` anomalies during master data operations.
- **Internal Microservice Routing Stabilization**: Resolved intra-service deadlocks by configuring the Uvicorn runtime to handle high-concurrency requests and explicitly registered internal `HCM` and `Subscription` endpoints within the unified monolith router.
- **Subscription Entitlements Propagation**: Corrected the `get_company_entitlements` internal endpoint to consistently broadcast `status` and `readonly` flags to the Auth service, ensuring precise reactive lockdowns across the platform.
- **Forensic Manifest Construction**: Drafted the `Forensic_Manifest.md`, crystallizing deterministic infrastructure UUIDs for core hierarchies, master data products, and subscriptions, guaranteeing Foreign Key integrity across staging resets and cloud deployments.
- **Status**: ✅ Phase 86 COMPLETED — Security Audit Ledger Active, Identity Unified & Architectural Validation Finalized.

### [2026-05-04] Phase 85: Industrial CMMS Architecture & Enumerations
- **Domain Specialization**: Implemented `WorkOrderBase` as an Abstract Base Class in `common/models` to unify the concept of work orders across CMMS, MES, and WMS.
- **CMMS Microservice**: Bootstrapped `cmms_service` following Clean Architecture. Created `MaintenanceWorkOrder`, `Asset`, `MaintenancePlan`, and `Tool` entities.
- **Cross-Service Integrity**: Adopted Weak References (`inventory_item_id`) for tools and consumables to integrate seamlessly with the `inventory_service` without violating bounded contexts.
- **Storage Strategy**: Enabled hybrid storage (`S3Provider` / `LocalFSProvider`) with strict multi-tenant quotas for maintenance evidence.
- **Catalogs & i18n**: Developed a centralized `Enumeration` catalog in `master_data_service` replacing hardcoded enums, supporting dynamic updates and translations.
- **Status**: ✅ Phase 85 COMPLETED — CMMS Core Backbone & Catalogs Stabilized.

### [2026-05-03] Phase 84: Forensic Audit Ledger Hardening & Industrial SSOT Consolidation
- **Forensic Audit Engine**: Implemented `AuditService` with database persistence, capturing `SEED_CREATE`, `CREATE_MOVEMENT`, and `DENSITY_OVERFLOW` actions with full snapshotting (Old vs New values).
- **Model SSOT Consolidation**: Resolved systemic `DuplicateTableError` by centralizing the `InventoryLocation` model into `common/models/location.py`. Aliased service-specific models to the common source of truth to maintain backwards compatibility while ensuring a single metadata namespace for the Unified Monolith.
- **Unified Seed Integration**: Hooked `AuditService` into `unified_industrial_seed.py`, guaranteeing a forensic trail from the first second of environment initialization.
- **Indentation & Logic Hardening**: Fixed critical `IndentationError` in `DensityGuard` and restored overflow logic to ensure safety alerts are recorded in the ledger.
- **Workflow Automation**: Updated `hard-reset.md` and `initialize-monolith.md` with forensic validation steps (`SELECT FROM audit_logs`).
- **Status**: ✅ Phase 84 COMPLETED — Forensic Traceability & Model SSOT Hardened.

### [2026-05-03] Phase 83: Industrial Location Management & Active Density Guard (WMS Tier-1)
- **Bug P0 Resolved**: Implemented `GET /api/v1/inventory/locations/{code}/density` — the endpoint referenced by the Frontend Put-Away Handheld Component (Step 2) that was never backed by the server, causing a silent density check failure on every put-away operation.
- **Model Evolution**: Upgraded `InventoryLocation` from a basic `max_capacity` string field to a full industrial spatial entity with PA-SEC-NV-POS hierarchical addressing (Aisle/Section/Level/Bin), physical limits (units, weight, volumetric dimensions), denormalized O(1) occupancy cache (`current_units`, `current_weight_kg`), zone/storage classification enums, and computed density properties (`utilization_percent`, `density_status`).
- **Active Density Guard**: Replaced the passive (log-only) `_check_location_capacity` with a **3-layer active validator**: Layer 1=Units (Soft Block — logger warning only, does not stop transaction), Layer 2=Weight (HARD BLOCK — safety-critical, no override possible), Layer 3=Volumetric (advisory warning).
- **Master Seed Unification**: Consolidated `unified_industrial_seed.py` to orchestrate Auth, Master Data, WMS Layout (Phase 83), and Initial Stock flows in a single idempotent execution.
- **Atomic Race Condition Prevention**: Added `increment_location_occupancy()` repository method using SQL-level `UPDATE` (not ORM read-modify-write) to prevent cache corruption.
- **Status**: ✅ Phase 83 COMPLETED — WMS Industrialized, Density Guard Active & Seed Unified.

### [2026-05-03] Phase 82: Automatic FIFO Motor & Customs Industrialization
- **Automatic FIFO Engine**: Integrated real-time consumption logic in `SQLAlchemyInventoryRepository`. Standard `OUT` and `TRANSFER` movements now automatically decrement Anexo 24 balances from source entries, ensuring forensic traceability without manual input.
- **Cross-Border Validation (Flow 5)**: Successfully executed and validated the Binational Inter-Company Transfer flow (MX -> US), enforcing mandatory Customs Pedimento presence for legal compliance.
- **Industrial Flow Suite (6/6)**: Validated the complete inventory lifecycle across the unified monolith: Entry, Exit (FIFO), Internal Transfer, National ICT, Binational ICT, and Bulk Variant Purchase.
- **Dependency & Encoding Hardening**: Resolved Windows-specific Unicode encoding issues in seed scripts and standardized `PYTHONPATH` for host-based validation of the monolith architecture.
- **Status**: ✅ Phase 82 COMPLETED — Customs Integrity Hardened & FIFO Motor Active.


### [2026-05-03] Phase 81: Monolith Re-engineering & Customs Stability
- **Monolith Namespace Stabilization**: Resolved systemic SQLAlchemy "Multiple classes found for path Product" crashes by renaming the subscription microservice package to `subscription_app` and enforcing absolute, service-qualified imports (`auth_app`, `master_app`, etc.) across the unified entry point.
- **Routing & 404 Remediation**: Successfully mapped and validated the Customs Balance API within the `/api/v1/reporting/customs` namespace, ensuring full reachability from the Frontend Kanban.
- **Dependency Unification (Stripe/MES)**: Updated the `Monolith.Dockerfile` to include all microservice requirements (`stripe`, etc.) and standardized the `PYTHONPATH` to include all service subdirectories.
- **Unified Industrial Seed v4 Execution**: Populated the database with industrial warehouses, products, and variants, enabling immediate operational visibility for the Customs module.
- **Audit Compliance**: Reached 100% CLEAN status in the Code Knowledge Graph Audit by fixing the "localhost" false-positive logic and modernizing the MES service domain logic paths.
- **Status**: ✅ Phase 81 COMPLETED — Monolith Namespace Stabilized & Customs API Operational.

### [2026-05-02] Phase 80: Ticket Triage Workflow & API Hardening
- **Triage API Stabilization**: Corregidos errores críticos 500 en la lectura de claims del JWT (`user.roles` a `user.role_names`) en `ticket_routes.py` para permitir la asignación fluida desde el Kanban.
- **Reference Collision Immunity**: Refactorizado el algoritmo de generación de folios (`_generate_ref_code`) implementando conteos globales atómicos y fallback por timestamp, erradicando los `UniqueViolationError` en multi-tenant concurrent conditions.
- **Workload Metrics Enablement**: Fixeado el route matching 404 para `/tickets/technicians/workload` promocionando el endpoint y configurando su UI component para carga dinámica de técnicos.
- **Automated E2E Testing Expansion**: Ampliada la suite de pruebas `test_tickets_e2e.py` garantizando la cobertura de los endpoints de Workload y Triage.
- **Status**: ✅ Phase 80 COMPLETED — Triage Engine Hardened & UI Data Bound.

### [2026-05-02] Phase 79: Tickets Event Flow & System Resilience
- **Monolith Integration Fixes**: Recreación de contenedores forzando recargas, estabilizando el ruteo interno de `/api/v1/events` y logrando validación de eventos (202 Accepted).
- **Timezone Standardization**: Eliminación del error `asyncpg` mediante la migración global de columnas Naive a `DateTime(timezone=True)` (Afectando Outbox, Inventory, y Notifications).
- **Outbox Debouncing (Event Storm Prevention)**: Desarrollo de lógica en el Repositorio de Tickets limitando tormentas de eventos. Criterio de validación mediante queries asíncronas con ventanas de tiempo (10 segundos) y validado con suite de `pytest`.
- **E2E Ticket Loop**: Comprobación total de creación de tickets mediante el motor Outbox, extrayendo el mensaje exitosamente y procesando la validación del SLA con el `EscalationWatcher`.
- **Status**: ✅ Phase 79 COMPLETED — Tickets Event Flow & Resilience Stabilized.

### [2026-05-01] Phase 78: Master Data Industrialization (SideDrawer Migration)
- **Industrial UI Upgrade**: Complete refactor of `WarehouseFormComponent` and `ConceptFormComponent` to match premium glassmorphic standards with sticky footers and industrial iconography.
- **SideDrawer Unification**: All catalog modules (`Partners`, `Concepts`, `Warehouses`, `UOMs`, `Categories/Brands`) now use the centralized `SideDrawerService` with strict `DrawerOptions` typing.
- **Bug Remediation**: Resolved critical TypeScript compilation errors (`TS2345`, `TS2341`) and Angular template syntax issues (`NG5002`) across the Master Data domain.
- **Reactive Workflow**: Standardized `drawerService.refresh$` pattern to ensure real-time UI updates upon catalog mutations without full page reloads.
- **Documentation Sync**: Synchronized engineering logs and performed architectural audit using the refined `sync-docs.md` protocol.
- **Status**: ✅ Phase 78 COMPLETED — Master Data Domain Industrialized & SideDrawer Unified.

### [2026-05-01] Phase 77: Consolidación de Microservicios (Currency Service Integration)
- **Consolidación del Monolito**: Integración total del `currency_service` dentro del `master_data_service` para reducir la fragmentación y centralizar los Datos Maestros Financieros.
- **Rate Provider Industrial**: Implementación de `ExternalRateProvider` con soporte para **Banxico (FIX)** y **Frankfurter (BCE)** con lógica de fallback automática.
- **Inmutabilidad Financiera**: Migración del modelo `CurrencyExchangeRate` con soporte para auditoría de cambios y flags de variaciones sospechosas (>10%).
- **Unified API Routing**: Registro de endpoints unificados en `/api/v1/currencies` bajo el router de Master Data.
- **Compliance Audit**: Alcanzado 100% de cumplimiento en multi-tenancy para el repositorio de divisas (Fix: `MISSING_TENANT_FILTER`).
- **Decommissioning**: Eliminación exitosa de la carpeta `backend/currency_service` y sus recursos asociados, validado por el Code Graph Auditor.
- **Status**: ✅ Phase 77 COMPLETED — Currency Infrastructure Consolidated & Decommissioned.

### [2026-05-01] Phase 76: Escalación Dinámica Multi-tenant & Soporte AI
- **Matriz de Escalación Dinámica**: Implementación de `EscalationRule` y motor de búsqueda con fallback por área (`Producción`, `Almacén`, `Soporte`, `_default`).
- **Worker Industrial (EscalationWatcher)**: Creación de un worker funcional para el escaneo de SLAs y disparo de eventos de escalación automatizada.
- **Help Center AI (Fase 8 Preview)**: Integración de lógica de auto-respuesta AI para tickets de tipo `SUPPORT` en el `TicketService`.
- **Compliance Audit**: Alcanzado 100% de cumplimiento en el `tickets_service` mediante el uso de `bypass_tenant` explícito en consultas de orquestación global.
- **HCM Alignment**: Departamentos y áreas sincronizados con los estándares de `hcm_service`.
- **Status**: ✅ Phase 76 COMPLETED — Industrial Monolith Unified & Frontend Mature.

### [2026-05-01] Phase 76: Frontend Industrialization (UI/UX Maturity)
- **Currency Support**: Implementación de `CurrencyService` y pipes reactivos para cambio dinámico USD/MXN con impacto en dashboards financieros.
- **God Mode (Modo Dios)**: Despliegue de `AdminAuthService` y `GodModeGuard` para rescate técnico y overrides administrativos.
- **Support Drawer AI**: Integración de panel de soporte lateral con gestión de tickets industriales y simulación de respuestas AI (MCP).
- **Backend Routing Remediator**: Eliminación de prefijos redundantes en `ticket_routes.py` para resolver errores 404 en el monolito unificado.
- **Support Sync Protocol**: Implementación de `/config/constants` para sincronización dinámica de enums industriales (Status, Priority, Type).
- **Reactive Support Engine**: Refactorización de `SupportService` usando Angular Signals y Effects para gestión de tickets y chat en tiempo real.
- **Industrial Localization (i18n)**: Soporte completo ES/EN para el centro de ayuda, dashboard y drawers globales.
- **Excel Mode Enhancement**: Refactorización de `InventoryDocumentComponent` para alta densidad de datos y contraste industrial.
- **Global UI Integration**: Unificación del comando global (Idioma, Moneda, Soporte) en el `MainLayout`.

### [2026-05-01] Phase 75: Tickets Service — Remediación Crítica & Expansión Operacional
- **Remediación de Precisión Financiera**: Migración de `float` a `Numeric(18, 8)` en `cost_estimate` del modelo `Ticket` y `Decimal` en DTOs para eliminar descuadres de Kardex.
- **Seguridad Inter-servicio (HMAC)**: Implementación de validación criptográfica HMAC-SHA256 en el endpoint `/internal` con logging forense de intentos no autorizados vía `AuditService.track()`.
- **Estandarización de Auditoría**: Reemplazo de `audit_repo.create_log` por `AuditService.track()` en todo el `TicketCommandHandler`.
- **Alineación de Secretos**: Corregido `SECRET_KEY` del `tickets-service` en `docker-compose.yml` (era `changeme`).
- **Subscription Seed Fix**: Extendida vigencia de suscripciones de desarrollo a 10 años (`timedelta(days=3650)`).
- **Expansión del Modelo de Dominio (Fase 5)**: 4 nuevos `TicketType` industriales (`Mantenimiento`, `Recibo Material`, `Tiempo Muerto`, `Escalación`) y 7 nuevos campos en el modelo `Ticket` (`source_service`, `station_id`, `reported_by_id`, `parent_ticket_id`, `auto_close_on_event`, `escalation_level`, `resolved_at`).
- **Self-Referential Hierarchy**: Relación `parent_ticket` ↔ `child_tickets` para cadenas de escalación.
- **CQRS Expansion**: `CreateTicketCommand` ahora propaga todos los campos operacionales al repositorio.
- **Status**: ✅ Phase 75 COMPLETED — Tickets Service Hardened & Operationally Expanded.

### 🗓️ Abril 2026: Consolidación Cloud y Resiliencia de Suscripción

### [2026-04-30] Phase 74: Bloqueo Reactivo por Suscripción & SaaS Integrity
- **Motor de Degradación L7**: Implementación de un motor de bloqueo estructurado basado en el estado de la suscripción (`PAST_DUE`, `RESTRICTED`, `UNPAID`) sincronizado entre `auth_service`, `subscription_service` e `inventory_service`.
- **Paywall Reactivo**: Los inquilinos en estado `RESTRICTED` solo tienen acceso de lectura (`402 Payment Required` en escrituras), mientras que los `UNPAID` enfrentan un bloqueo total mediante un **Global Paywall Overlay** en Angular 19.
- **Middleware Security Enforcement**: Refuerzo del `InternoCoreGlobalMiddleware` para imponer el bloqueo de seguridad basado en claims `status` y `readonly`.
- **JWT Identity Enrichment**: Inyección de claims en el JWT final y en los endpoints de `/refresh` y `/me` (Zero Trust) para hidratación de UI.
- **Reactive UI Signals (Angular 19)**: Implementación de signals `isReadOnly()` y `isUnpaid()` en el `AuthService` para bloqueo sensorial inmediato.
- **Auditoría Forense**: Validación exitosa del "cableado" de seguridad mediante `audit_subscription_states.py` (5/5 tests passed).
- **Code Graph Invariants**: Integración del invariant `SUBSCRIPTION_GUARD_VIOLATION` para detectar fugas de seguridad en microservicios de escritura.
- **Status**: ✅ Phase 74 COMPLETED — Subscription Resilience & Reactive Lockdown Operational.

### [2026-04-30] Phase 73: Estabilización de Autenticación Industrial & HCM Migration
- **HCM Service Extraction**: Despliegue del microservicio `hcm_service` bajo Clean Architecture, desacoplando la gestión de colaboradores (RRHH) del núcleo de autenticación.
- **Industrial Auth Handshake (RFID/PIN)**: Restauración del flujo de login industrial mediante escaneo de RFID (SHA-256) y PIN (Bcrypt) con descubrimiento automático de tenants.
- **JWT Identity Enrichment**: Inyección de claims operativos críticos (`full_name`, `internal_id`, `is_supervisor`, `wid`) en el JWT final, permitiendo operación Zero-Trust en dispositivos de borde.
- **Configuration Centralization**: Migración de variables críticas (como `CORE_HCM_RFID_SALT`) al `.env` global, eliminando inconsistencias entre servicios.
- **AWS CloudWatch Readiness**: Sanitización total de logs eliminando emojis y caracteres especiales para asegurar compatibilidad con AWS CloudWatch Logs.
- **Status**: ✅ Phase 73 COMPLETED — HCM Infrastructure & Industrial Auth Stabilized.

### [2026-04-28] Phase 72: Industrial WhatsApp Notifications & Virtual Group Broadcasting
- **Twilio Production Integration**: Implementación del `WhatsAppClient` con soporte para la API de producción de Twilio (Basic Auth y payloads urlencoded).
- **Virtual Group Engine**: Desarrollo de una arquitectura de "Grupos Virtuales" en el `notification_service`, permitiendo mapear un nombre lógico (ej. `ALERTAS_PLANTA`) a múltiples destinatarios individuales para superar las restricciones de Sandbox.
- **Webhook Discovery & Security**: Despliegue del endpoint `/api/v1/whatsapp/webhook` con bypass de seguridad `X-Company-ID` en el middleware global.
- **Broadcast Multitenant**: El `NotificationService` ahora procesa envíos masivos de forma atómica, registrando el estado de entrega individual.
- **Status**: ✅ Phase 72 COMPLETED — Industrial WhatsApp Pipeline Operational.

### [2026-04-18] Estabilidad Cloud AWS
- **CORS Resolution**: Se resolvió el bloqueo `400 Bad Request` ajustando el orden de carga de secretos en Python antes del montaje del middleware, solucionando la conectividad ALB.
- **Microservices Rollout**: Despliegue industrial ECS validado. Conectividad E2E desde CloudFront confirmada en el Mission Control.

### [2026-04-13] Gobernanza de Raíz
- **CORE_ Prefix**: Estandarización del prefijo de variables de entorno de `INT_` a `CORE_` y limpieza profunda del directorio raíz para evitar polución de archivos.

---

## 🏛️ Arquitectura de Identidad (SSOT)
El sistema opera bajo un protocolo de **Identidad Triple** consolidado:

| Capa de Identidad | Método de Validación | Responsabilidad |
| :--- | :--- | :--- |
| **Identidad Digital** | OAuth2 / JWT (T1/T2) | Acceso a la plataforma y APIs. |
| **Identidad Física** | RFID (SHA-256) / PIN | Operaciones en piso de producción (MES). |
| **Identidad Legal** | company_id (Multi-tenant) | Aislamiento de datos y cumplimiento fiscal. |

## 💰 Definición Financiera: La Tríada del Valor
Desde abril de 2026, el sistema rige la existencia de cualquier producto bajo una relación jerárquica estricta:
1.  **Landed Cost**: Costo de adquisición más gastos logísticos (Aduana/Flete).
2.  **CPP / WAC**: Costo Promedio Ponderado para valuación de inventario contable.
3.  **Transfer Price**: El contrato financiero sellado para movimientos entre empresas hermanas. (El precio de venta de Empresa A se convierte en el costo de Empresa B al despacho).

> [!IMPORTANT]
> **Nota de Seguridad (Zero-Trust)**: El BaseRepository captura el `company_id` directamente del JWT verificado. No se permite que el cliente envíe el ID del inquilino en operaciones de escritura para prevenir vulnerabilidades de tipo IDOR.

## 📡 Mapa de Infraestructura (Puertos Core)
| Servicio | Puerto | Función Crítica |
| :--- | :--- | :--- |
| **Monolith** | 8000 | Motor Unificado (Auth, Master, Inv, MES, Tickets). |
| **Auth** | 8001 | Microservicio (Legacy/Separate Mode). |
| **Master Data** | 8003 | Microservicio (Legacy/Separate Mode). |
| **Inventory** | 8006 | Microservicio (Legacy/Separate Mode). |
| **Subscription** | 8002 | Gestión de Billing y Lockdowns L7. |

### 🗓️ Marzo 2026: Identidad Triple y Seguridad Zero-Trust

#### [2026-03-30] Hardening de Seguridad
- **Refresh Token Rotation (RTR)**: Implementación de rotación estricta y taxonomía de tokens (access, refresh, selection).

#### [2026-03-15] Sealed Price (Precio Sellado)
- **Inmutabilidad Financiera**: Aprobación del patrón de transferencias Inter-Company: el precio de venta de la Empresa A se convierte en el costo de compra de la Empresa B al momento del despacho.

#### [2026-03-03] Estructura de Holdings
- **BusinessGroup Model**: Introducción de jerarquías para compartir catálogos maestros entre empresas del mismo grupo.

---

### Historical Archive (Legacy Phases)

### [2026-04-27] Phase 71: Financial Valuation & Forensic Audit (Ledger Stabilization)
- **Forensic Audit Engine**: Despliegue del endpoint `/api/v1/audit/` en el `inventory_service` para exponer el historial inmutable de transacciones (Ledger).
- **Audit Log UI**: Implementación del componente `InventoryAuditComponent` con visualización glassmórfica de cambios (Old vs New Value) y filtrado por acción/tabla.
- **Financial Mapping Fix**: Resolución del bug de mapeo en SQLAlchemy (`_amount` vs `unit_price`) que impedía la auditoría de movimientos financieros.
- **Notification Persistence**: Corrección del estado de lectura de notificaciones mediante auditoría de `rowcount` en el `notification_service`.
- **Multi-Currency Foundation**: Actualización de esquemas de empresa para soportar `base_currency` nativa desde el onboarding.
- **AWS Readiness**: Limpieza de strings `localhost` en configuraciones críticas, validado por Code Graph Auditor.
- **Code Graph**: ✅ 100% Compliance — 14 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 71 COMPLETED — Financial & Forensic Traceability Stabilized.

### [2026-04-25] Phase 70: Interno Assets CRM & GIS Intelligence Pipeline
- **Asset Manager Service Inception**: Despliegue del microservicio `asset_manager_service` bajo Clean Architecture, integrando un motor financiero de evaluación de ROI para oportunidades inmobiliarias.
- **GIS-to-CRM Pipeline**: Implementación de `BackgroundTasks` en el `master_data_service` para la propagación automática de reportes catastrales hacia el CRM de inversiones.
- **Zero-Trust Multi-Tenancy (Personal Scope)**: Implementación de filtros por `created_by` con bypass de `company_id` para gestión de activos privados, validado 100% por el Code Graph Auditor.
- **Resiliencia de Datos (RPPC Bypass)**: Documentación de inconsistencias en el GeoServer de Tijuana y estrategia de reintentos para claves catastrales complejas (PK-020-119).
- **Kanban Dashboard UI**: Creación del módulo nativo Angular 19 (`/investments/asset-manager`) usando Angular Signals y CDK Drag&Drop.
- **Plusvalía Tooltip**: Integración del Padrón Inmobiliario 2020 vs 2026 para el cálculo en tiempo real de la apreciación del activo.
- **Seguridad RBAC**: Módulo protegido nativamente bajo el scope `investments:manage` inyectado en el NavigationService.
- **Code Graph**: ✅ 100% Compliance — 14 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 70 COMPLETED — Asset Intelligence Layer Active (Backend + UI Kanban).

### [2026-04-24] Phase 69: Industrial Zero-Hardcode Frontend (SSOT Enforcement)
- **Eliminación de Mocks**: Se eliminaron los métodos `getMockWarehouses` y `getMockConcepts` de `InventoryService`, erradicando datos estáticos del flujo de inventario.
- **Resolución Dinámica de UOMs**: Se reemplazaron UUIDs quemados por una lógica de resolución por código (`PZA`, `FT`) mediante el nuevo `MasterDataService.resolveUomByCode`.
- **Limpieza de Fallbacks en Búsqueda**: `ItemSearchComponent` fue purgado de datos de ejemplo (`MAT-001`, `MAT-002`), garantizando que solo se visualicen productos reales del catálogo.
- **Staging Locations Dinámicas**: `InventoryInboundComponent` ahora genera sus puntos de estiba (*Docks*) dinámicamente desde el catálogo de almacenes, eliminando el registro estático `DOCK-01`.
- **Smart Form Preview Reactivo**: La previsualización de conceptos en el catálogo ahora utiliza almacenes reales del tenant activo para simular la lógica de negocio.
- **Intercompany Transfers UI (ICT)**: Se integró la lógica de binding de datos de dropdowns "Empresa Destino" vs "Cliente" basado en `requires_external_entity` de `TRF-EXT`.
- **Resiliencia en Documentos Financieros**: Modificación de las plantillas de `printInvoice` y `printLabel` para cast de Decimals dinámicos a Number y evitar bloqueos en el UI con `NaN` exceptions. Agregado de badges para "Pendiente de Valuación Financiera".
- **Code Graph**: ✅ 100% Compliance — 13 microservicios, 0 errores críticos.
- **Resiliencia de Excepciones**: Estandarización de `DomainException` con atributo `status_code` nativo, eliminando errores `AttributeError` en el middleware global.
- **Integración de God Mode**: Implementación del header `X-Admin-Master-Key` que permite la elevación a `GOD_MODE_ADMIN` para bypass de validaciones de propiedad multi-tenant en correcciones administrativas.
- **Middleware Guardado**: Refactorización del middleware global para manejo resiliente de errores críticos con logging forense de trazas.
- **Status**: ✅ Phase 69 COMPLETED — Zero-Hardcode & Backend Resilience Enforced.

### [2026-04-22] Phase 68: Frontend Concept-Guard Architecture (Signal-Safe Inventory Integration)

- **Signal-Safe Resolution**: `MasterDataService.resolveConceptByCode(code)` retorna `null` durante LOADING — ningún componente puede enviar `concept_id: null` al backend, eliminando errores 400/422 en cold-start de tenant.
- **Three-State Catalog Guard**: `conceptCatalogState` expone `'LOADING' | 'READY' | 'ERROR'` para que los botones de submit muestren "Configurando Empresa..." en lugar de bloquearse silenciosamente.
- **Write Guard Pattern**: `canSubmitTransfer = computed(() => isFormValid() && transferConceptId() !== null)` — patrón replicado en Transfer e Inbound.
- **Concept Injection**: `initiateInterCompanyTransfer` y `dispatchInternalTransfer` en `InventoryService` ahora tienen payloads tipados con `concept_id: string` requerido.
- **Display Duality**: Dashboard y Documentos muestran `concept_name` ("Recepción de Compra") con fallback al tipo técnico ("ENTRY") para documentos legacy.
- **Code Graph**: ✅ 100% Compliance — 13 microservicios, 0 errores críticos.
- **Status**: ✅ Phase 68 COMPLETED — Frontend Inventory Industrialization Complete.

### [2026-04-22] Phase 67.5: Master Data Concept Industrialization (Backend)
- **JIT Seeding**: `SQLAlchemyMasterDataRepository` auto-crea conceptos estándar (PUR-REC, SAL-DIS, INT-TRA) para empresas nuevas sin catálogo.
- **Inheritance Query**: Repositorios usan `OR (company_id = X, group_id = Y)` para catálogos corporativos compartidos.
- **Flow Compliance**: Los 6 scripts de flujos de inventario (`flow_1` a `flow_6`) resuelven e inyectan `concept_id` de forma dinámica.
- **Status**: ✅ Phase 67.5 COMPLETED — Backend Concept Architecture Stabilized.

### [2026-04-21] Phase 67: Hierarchical Multi-Tenancy & Master Data Visibility
- **Hierarchical Access Protocol**: Implementamos la propagación de group_id en el JWT durante la selección de empresa. Esto permite la visibilidad jerárquica de datos maestros (Catálogos Corporativos) en todos los microservicios.
- **Master Data Synchronization**: Reparación y estandarización de registros existentes en la DB (product_brands, product_categories, uoms, products). Todos los activos globales ahora están correctamente vinculados al eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e (Interno Business Group).
- **Backend Serialization Fix**: Implementación de InternoCoreEncoder en el middleware global para manejar UUID, datetime y  ytes, eliminando errores 500 en flujos de autenticación complejos.
- **Unified Industrial Seed v4**: Evolución del script de seed para poblar automáticamente la jerarquía de grupos y catálogos compartidos.
- **Status**: ✅ Phase 67 COMPLETED - Hierarchical Authorization & Visibility Stabilized.

### [2026-04-21] Phase 66: Unified Monolith & Cloud Governance (Kill Switch)
- **Monolith Pivot**: Transicionamos el entorno local a un **Monolito Unificado** (`interno-monolith`), consolidando 11 microservicios en un solo motor de alto rendimiento.
- **FinOps Kill Switch (Cloud Janitor)**: Implementación de `backend/scripts/infraestructure_aws/99_nuke_everything.ps1`, un mecanismo de demolición total para llevar la factura de AWS a **$0.00** de forma instantánea.
- **AWS Orchestrator**: Creación de `backend/scripts/infraestructure_aws/01_deploy_full_stack.ps1` para el re-ensamblaje automatizado de la infraestructura (VPC-Bridge + PrivateLink).
- **Subscription Guard (Kill Switch v1)**: Desarrollo del middleware `SubscriptionGuard` que implementa el modo "Solo Lectura" (Soft Kill Switch) para proteger la integridad de los datos en caso de suscripciones vencidas.
- **Infraestructure State**: Documentación del estado **LOCAL ONLY** en `INFRASTRUCTURE_STATE.md` con guías de recuperación.
- **Status**: ✅ Phase 66 COMPLETED - Governance & Performance Stabilized.

### [2026-04-20] Phase 65: FinOps App Runner Isolation & AWS Service Quotas
- **App Runner Deployment refactor**: Transicionamos la validación de AWS desde despliegues manuales en CLI atados a la cuenta de GitHub hacia un enfoque `Amazon ECR` nativo, optimizando los costos de despliegue mediante AWS App Runner.
- **Service Quotas Discovery**: Se descubrió una cuota oculta ("Anti-Fraude") de AWS en cuentas nuevas que restringe App Runner a un máximo de **2 servicios simultáneos**. Se abrió Ticket Support `#177671606300742` a Operaciones de AWS para incrementar la cuota a 5 y acomodar la flota Microservicios completa.
- **Limpieza Estratégica**: Se ejecutó limpieza via CLI eliminando `notification-service` y recursos bloqueados para priorizar de forma elástica la disponibilidad del `master-data-service` y el `auth-service` dentro del límite de 2 slots actual.
- **Status**: ⏳ Phase 65 PAUSED - Pending AWS Support Quota Approval (ETA < 24h).

### [2026-04-20] Phase 63: High Operational Availability (Laissez-Faire) & Density Guard
- **Recepción Laissez-Faire**: Refactorización del flujo de entrada de mercancía para priorizar la continuidad operativa. El sistema ahora responde con **202 Accepted** de forma inmediata, delegando la validación a tareas de fondo.
- **Density Guard Asíncrono**: Implementación de auditoría silenciosa que valida la capacidad física de las ubicaciones sin bloquear la transacción. Registra estados de `OVERFLOW_CONFIRMED` en el Ledger para visibilidad gerencial.
- **Centralización de Master Data**: Migración definitiva de `InventoryLocation` al `master_data_service` como única fuente de verdad (SSOT) estructural.
- **Arquitectura Reactiva**: Activación de eventos `CapacityViolationEvent` hacia el `notification_service` para alimentar alertas en tiempo real en el Dashboard principal.
- **Compliance DB (Alembic)**: Despliegue de la migración `fe63_val_status` para soportar estados de validación en el ledger de movimientos.
- **Status**: ✅ Phase 63 COMPLETED - Reactive Industrial Logic Online.

### [2026-04-20] Phase 64: Visibility Stress-Test & Resilience
- **E2E Validation**: Successfully executed the "Stress-Test de Visibilidad" injecting a 500-unit overflow into a 10-unit location.
- **Notificación Industrial**: El `notification_service` procesó correctamente la alerta `CapacityViolationEvent`, persistiendo el estado en el Dashboard de Control.
- **Hardenning**: Corregidos fallos de integridad multitenancy y esquemas faltantes en el motor de notificaciones.
- **Status**: ✅ FASE 64 E2E VALIDATION: PASSED.

### [2026-04-20] AWS Budget Pivot: ALB to App Runner
- **Optimización de Costos**: El Application Load Balancer (ALB) fue identificado como un gasto excesivo (~$23 USD/mes base) para el presupuesto de $5.00 USD.
- **Acción**: Eliminación del ALB e infraestructura de ECS Fargate residual. Transición hacia **AWS App Runner** (PaaS) para el `auth_service`.
- **Infraestructura**: Creado `apprunner.yaml` y guía de despliegue `APP_RUNNER_DEPLOY_GUIDE.md` para estandarizar el despliegue de bajo costo.
- **Status**: ✅ Phase 58 COMPLETED - Low-Cost Infrastructure Pivot.

### [2026-04-18] Phase 57: GIS Integration & Tijuana Cadastral Mapping
- **GIS Core Integration**: Desarrollo de `ArcGisTijuanaProvider` en `common/gis` para validación de claves catastrales y georeferenciación frente al IMPLAN Tijuana.
- **Web Scraping de Propietarios**: Implementación de scraping resiliente con manejo de `__VIEWSTATE` para recuperar el nombre del propietario legal desde el portal de pagos de Tijuana.
- **ValueObject Address**: Enriquecimiento del objeto de dirección con `cadastral_key`, coordenadas y tipo de propiedad, manteniendo compatibilidad con servicios existentes.
- **Status**: ✅ Phase 57 COMPLETED - GIS & Cadastral Validation Online.

### [2026-04-18] AWS Cloud Stability & CORS Resolution
- **Problema de CORS (Mixed Content vs Preflight)**: Se resolvió que el bloqueo `400 Bad Request` en producción provenía del orden de carga en Python (Starlette evalúa CORS antes de que `boto3` inyecte secretos).
- **Resolución**: Arquitectura ajustada invirtiendo Imports para que AWS Secrets (`load_aws_secrets`) parchee `int_backend_cors_origins` antes de que el middleware sea montado, solucionando instantáneamente la conectividad ALB.
- **Microservices Rollout**: Despliegue industrial ECS validado. Conectividad E2E desde CloudFront confirmada en el Mission Control.
- **Status**: ✅ Phase 55 STABILIZED - Production Auth Service Online & Verified.

### [2026-04-17] Phase 55: AWS Industrial Deployment & Frontend CDN
- **Microservices**: `auth_service` desplegado en AWS ECS Fargate us-east-2.
- **Infrastructure**: ALB validado, RDS conectado, Secret Injection implementado.
- **Frontend**: Angular build corregido con `fileReplacements` y desplegado en CloudFront.
- **Docs**: Creados `MICROSERVICE_DEPLOY_GUIDE.md` y reportes de estatus.
- **Status**: ✅ Phase 55 COMPLETED - Auth & Frontend Production Ready.

## [2026-04-16] - Phase 44: Infrastructure Convergence & Media Assets support
- **Unified Cloud Abstraction (`StorageProvider`)**: Engineered a strategy-pattern based storage library in `backend/common`. Supports multi-tenant S3 (AWS/LocalStack) and Local storage with a single interface. Implemented automatic Pre-signed URL generation for secure, high-speed frontend retrieval.
- **SSM Configuration Resilience**: Established a hierarchical Parameter Store structure (`/interno-core/global/` vs `/interno-core/{service}/`) to deduplicate global secrets. Validated migration through de-duplication scripts and LocalStack (v1.4.0) integration to bypass AWS Pro license requirements.
- **Microservice Media Expansion (RH, Inventory, Master Data)**: Scaled the industrial photo pattern across the ecosystem. Engineered `VariantService` to handle asset logic in `inventory_service` and updated `master_data_service` for catalog photos. Applied targeted Alembic schema synchronization to ensure multi-tenant RDS integrity for digital assets.
- **Frontend URL Normalization**: Developed an Angular `imageInterceptor` and `secureImage` Pipe to handle multi-tenant asset paths. The system automatically injects the primary assets domain (`environment.assetsUrl`) and handles default placeholders, ensuring a premium UX regardless of deployment mode.
- **Logistics Cleanliness (Gobernanza)**: Moved all operational test and migration scripts to `backend/tests/integration/infrastructure/` to maintain a zero-pollution root directory.
- **Status**: ✅ COMPLETED (Cloud-Ready, Media-Enabled & Scaled Backbone)

## [2026-04-15] - Phase 53: Industrial Data Simulation Injection
- **Data Scaling for UI Validation**: Engineered a direct SQLAlchemy integration bypass (`simulate_liquor_distro.py`) to inject highly dense logic scenarios without relying on API controllers. 
- **Simulated RBAC**: Explicitly wired 3 multi-tenant roles testing boundaries: `tony@interno.com` (Group Admin), `garry@interno.com` (Distributor Logistics), and `tropy@interno.com` (Single Node Operator) to fully evaluate Angular Component un-mounting and guarded routing.
- **Kardex Injection**: Simulated over 15 days of continuous operations (+180 entries) involving IN, OUT, and ADJUSTMENT operations pushing pricing valuation logic (WAC bounds) specifically targeted towards forensic audit rendering scenarios.
- **Status**: ✅ COMPLETED (High Volume QA Environment Ready)

## [2026-04-15] - Phase 49.8: Outbound Shipping & Compliance (Embarques Industrial)
- **Shipping Handheld Module**: Launched `InventoryShippingComponent` (`/inventory/shipping`) completing the warehouse loop. The module validates scanned Folios from the Picking stage and prepares the dispatch manifest.
- **Anexo 24 Driver Validation**: Integrated a mandatory "Driver Badge Scan" step as a bridge to Phase 50 (`hr_service`). This ensures that only authorized personnel with valid cross-border credentials (Visa/Sentry) can authorize international material dispatch.
- **WMS Menu Integration**: Registered "Embarques" as the final stage in the `NavigationService` and Dashboard quick-access loops.
- **Status**: ✅ COMPLETED (Full Warehouse Loop Closed)

## [2026-04-15] - Phase 49.5: Handheld UI Stabilization & Surface Refresh
- **Theme Unification**: Refactored all handheld modules (`Inbound`, `Picking`, `Put-Away`, `Cycle-Count`) to consume global Design System tokens (`surface-bg`, `surface-card`, etc.). Hardcoded dark-mode hex values were eliminated to support the system's dynamic Light/Dark mode toggles.
- **Full-Width Responsiveness**: Optimized industrial layouts for wide-aspect ratios (i.e. iPad Pro/Industrial Tablets). Standardized screen containers to `max-w-4xl` for better touch-target balance and visual hierarchy in desktop/tablet environments.
- **Manual Entry Restoration**: Rescued the "Blind Entry" and "Scan-less" flows in the handhelds, ensuring operators can recover from damaged barcodes while maintaining audit integrity.
- **Status**: ✅ COMPLETED (Industrial UX Optimized for Modern Hardware)

## [2026-04-15] - Phase 49: Cycle Count & Audit Sheets (Auditoría Total)
- **Blind Count Module**: Developed `CycleCountComponent` with a 3-step industrial flow: Location Lock → Blind Scan (no theoretical data shown) → Discrepancy Analysis. Operator scans SKUs individually; quantity adjustments via +/- controls. All validated against `InventoryRegistryService` ($O(1)$).
- **Audit Sheet Export**: Backend CSV generator (`/warehouses/{id}/audit-export`) with UTF-8-BOM encoding for Excel compatibility. Columns include Location, SKU, Pedimento (Anexo 24), and a blank "Physical Check" column for floor auditors.
- **Supervisor Override**: Discrepancies exceeding 5% of theoretical quantity require `supervisor` or `admin` role to confirm, enforcing segregation of duties on inventory adjustments.
- **Navigation Integration**: Added quick-access card ("Auditoría Spot") to Inventory Dashboard and sidebar entries in both Inventarios and WMS/Logística menus.
- **Status**: ✅ COMPLETED (Physical-to-Digital Reconciliation Enabled)

## [2026-04-15] - Phase 48: Industrial Integrity & "The Density Guard"
- **The Density Guard (Capacity Safety)**: Implemented a robust physical safety layer. Created `InventoryLocation` models with `max_capacity` constraints. The backend now performs real-time occupancy calculations (SUM of FIFO balances) and blocks movements (IN/RELOCATE) that exceed physical limits, raising `ERR_LOCATION_OVERFLOW`.
- **Registry Cache ($O(1)$ Search)**: Optimized the handheld experience for large-scale operations (10k+ SKUs). Developed an in-memory registry hydration system in Angular, ensuring SKU validation and metadata retrieval are instant, eliminating network-induced barcode delay.
- **Visual & Audio Feedback**: Integrated a semantic progress bar (Green/Amber/Red) in the Put-away flow to visualize rack utilization. Added an industrial overflow beep (110Hz) to notify operators of capacity violations without looking at the screen.
- **Legacy Port (Data Hygiene)**: Ported and modernized the `getNumber` regex logic from the .NET legacy codebase to sanitize scanner inputs, automatically stripping invisible characters and hardware-injected suffixes.
- **Status**: ✅ COMPLETED (Physical Integrity & Low-Latency Verified)

## [2026-04-15] - Phase 47: Industrial Put-Away & Session Stability
- **Handheld Put-Away Module**: Developed and integrated the `InventoryPutAwayComponent` with a specialized "3 Scans" flow (Origin -> Destination -> Confirm). Optimized for industrial scanners with F2 hotkey support and square-wave audio feedback (200Hz/880Hz).
- **Session Resilience Engine**: Patched critical session loss bugs by implementing defensive `getattr` lookups in the Auth service and a "Resilient Parsing" layer in the Angular frontend to handle varying microservice response structures (Double-Wrap Fix).
- **Anexo 24 Compliance Lock**: Enforced automated `pedimento_id` inheritance in internal relocations, ensuring 100% legal traceability from DOCK-01 to final RACK position.
- **Mission Control Integration**: Added quick-access industrial cards to the Dashboard for the multi-tenant warehouse operator.
- **Status**: ✅ COMPLETED (Warehouse Cycle Closed & Session Resilient)

## [2026-04-15] - Phase 46: Industrial Logistics Scalability & Anexo 24 Compliance
- **Server-Side Scalability**: Implemented unified pagination (`limit`/`offset`) and global search filters in `InventoryService` (Backend). The system is now architecture-ready for 10,000+ SKU catalogs.
- **Handheld UX Stabilization**: Resolved build-breaking Angular compilation errors (ESBuild compatibility) and standardized industrial UI aesthetics for stock audit views.
- **Standardized API Metadata**: Evolved `ApiResponse` model to include `total_count`, providing foundation for paginated reports across the ecosystem.
- **Logistics Integrity**: Fixed JSON parsing bottlenecks and ensured token-aware service integration for warehouse operators.
- **Handheld Response Resilience**: Implemented a 300ms RxJS debounce mechanism in terminal search bars to protect Backend resources during high-speed industrial scanning.
- **Status**: ✅ COMPLETED (Inventory Backbone hardened for Industrial Scale)

## [2026-04-14] - Phase 46: Industrial Pricing Pipeline Finalization
- **Secure Ticket Bridge**: Migrated the binational pricing system from fragile Blob downloads to a robust, session-based ticket mechanism (`/export/ticket`). UUID tokens guarantee isolation and cryptographic access.
- **Native File Naming (Suffix Hack)**: Successfully bypassed Chrome's Cross-Origin `window.location.href` naming restrictions by injecting a dummy suffix (`/plantilla.csv`) and refactoring Angular's `MasterDataService` to forcefully overlay the generic `.csv` name on background-downloaded blobs.
- **In-Memory Validation**: Verified standard CSV loads with 15+ articles confirming that 1.5KB real prices are pulled and formatted securely by the Backend core. Tested and approved Soft-Close Insert architecture via Drag & Drop pipeline in `price-import-dashboard.component.ts`.
- **Status**: ✅ COMPLETED (Catalog Pricing fully industrialized and deployable)

## [2026-04-14] - Phase 45.1: Pricing Stabilization & B2B Immortality (Final)
- **Immutable Pricing Logic**: Finalized the **"Soft-Close & Insert"** pattern for B2B price agreements and master prices, ensuring 100% auditability for industrial contracts. Validated via direct DB queries (Time-Torn timestamps).
- **Complexity Resolution**: Fixed critical `500 Internal Server Errors` (`AttributeError` on `amount`) in `master_data_service` by bridging Pydantic/SQLAlchemy composite `Money` mapping with native Python `@property` decorators on ORM variables (`ProductPrice`). Resolved `NotNullViolationError` by strictly enforcing `current_user.company_id` onto `tenant_id` namespace explicitly.
- **Enterprise Templates**: Generated official `plantilla_carga_precios_industrial.csv` for standardized mass-imports across multiple hierarchy vectors (List 0-10, Agreements).
- **Hybrid Pricing Interface**: Completed the tabbed UI for `ProductPriceListComponent`, integrating live partner alerts and premium "Missing Data" tooltips.
- **Quality Assurance**: Integrated `pytest` suite for automated pricing validation and patched `aiosqlite` for in-memory testing of complex Postgres-specific models (UUIDs).
- **Status**: ✅ COMPLETED (Pricing Infrastructure Hardened & Verified)

## [2026-04-14] - Phase 45: Industrial Pricing & Identity Stabilization (Frontend UX & RBAC)
- **SSOT UI RBAC Enforcement**: Standardized the `scopes` validation on `navigation.service.ts` aligning strictly with the `ROLE_SCOPE_MAP` backend injection map (`inv:movements:manage`, `master:catalog:manage`, `wms:manage`). 
- **Dynamic Scope Resolution**: Hardcoded scope mapping was decoupled from `auth_service.app.commands.select_company_command`. Scopes are now dynamically generated via `ROLE_SCOPE_MAP` mapping roles to UI sidebar modules, including `["*"]` logic for administrators.
- **Pricing Matrix UX Refactor**: Re-engineered `product-price-list.component.ts` layout using industrial flex-box standards. Implemented fixed header and sticky `ic-modal-body` constraints to resolve `max-height: 90vh` rendering overflow glitches.
- **Master Data Integrity Check**: Finalized `master_product_id` schema logic generation utilizing Python `uuid5` cross-service standard generation, guaranteeing binational entity ID tracking.
- **RBAC Catalog**: Added `rbac_scopes_catalog.md` defining strict constraints over `permissions` (backend logic) VS `scopes` (frontend UI menus).
- **Status**: ✅ COMPLETED (Ecosistema Totalmente Mapeado y Estabilizado)

## [2026-04-13] - Phase 44: Industrial Pricing & B2B Contracts
- **Inmutabilidad Industrial (Soft-Close)**: Se blindó el maestro de precios prohibiendo ediciones directas. Todo cambio genera una nueva versión inmutable con sellado de tiempo, garantizando auditoría "Point-in-Time".
- **Engine de Acuerdos B2B**: Implementación de la jerarquía de precios: Contrato > Lista > Maestro. Integración del modelo `PriceAgreement` para condiciones comerciales específicas por Partner.
- **Control Tower de Importación**: Desarrollo de un pipeline atómico de carga masiva en el backend y dashboard Drag & Drop en el frontend (Angular 18). Soporte para templates dinámicos y reporteo forense de errores.
- **Compliance DB (Alembic)**: Despliegue seguro de esquemas para multi-tenancy inmutable sin impactar la data existente.
- **Status**: ✅ COMPLETED (Ecosistema Financiero Estabilizado)

## [2026-04-13] - Phase 43: Root Governance & Global Standardization

- **Global Rename (CORE_ Prefix)**: Se estandarizó el prefijo de todas las variables de entorno de `INT_` a `CORE_` en microservicios, dockers, scripts y documentación para evitar colisiones semánticas.
- **Estructura de Directorios & Backend Cleanup**: 
    - Scripts operativos movidos a `scripts/`. Reportes y logs consolidados en `logs/`. Documentación categorizada en `docs/`.
    - Sanitización profunda de `backend/`: Eliminación de 8+ archivos huérfanos (`.log`, `.txt`, `.json`) y carpetas redundantes (`backend/backend`).
    - Separación del historial en `docs/historial/tasks` e `implementation`.
- **Exclusión de Kiosk**: El proyecto se re-enfoca exclusivamente en el núcleo industrial MES/ERP. Las tareas de eventos han sido archivadas y marcadas como fuera de alcance.
- **Premium Web Documentation**: Creación de `docs/DOCS_INTERNOCORE.html` como portal web de alta fidelidad enfocado exclusivamente en el núcleo MES/ERP (Industrial Backbone).
- **Workflow Updates**: Actualización de los agentes de sincronización para operar bajo la nueva jerarquía de archivos y el estándar de variables `CORE_`.
- **Status**: ✅ COMPLETED (Ecosistema Estandarizado e Industrializado)

## [2026-04-12] - Phase 42.5: Event Engine Generalization & N-Approver Quórum
- **Universal Engine**: El sistema evolucionó de un modelo de "Bodas" a un **Motor de Trabajo de Eventos Universal**. Se reemplazaron los roles fijos por un sistema de **Quórum de $N$ Aprobadores** dinámicos totalmente configurable.
- **Blindaje de Base de Datos (Alembic Async)**: Implementación de migraciones versionadas asíncronas para el `kiosk_service`. Eliminada la dependencia de recreación manual de tablas, permitiendo actualizaciones de esquema seguras y automáticas mediante `alembic upgrade head` durante el arranque.
- **Filtro de Integridad (Identity Protection)**: Incorporación de validación por `device_id` en el backend para garantizar votos únicos por hardware físico, evitando suplantaciones en el proceso de moderación.
- **Mecanismo de Emergencia "Staff Reset"**: Funcionalidad de autocuración que permite al Staff reiniciar el ciclo de votación (Quórum) de cualquier foto defectuosa o errónea.
- **Status**: ✅ COMPLETED (Industrial Ready for Offline Mini-PC)

## [2026-04-11] - Phase 42: Event Kiosk Initialization & Smart Checkout
- **Infrastructure**: Se configuró un orquestador ligero (`docker-compose.kiosk.yml`) exclusivo para eventos, interconectando `postgres-db`, MinIO, y el nuevo `kiosk-service` con límites de memoria estrictos para Mini PCs.
- **Match System (Tinder Mode)**: Lógica de aprobación fotográfica dual (Novio y Novia) en el backend y cliente Angular 19 (PWA).
- **Checkout Híbrido**: Arquitectura *One-Intent* consolidando compras de carrito e integrando Monedero Paparazzi interno con Stripe Elements.
- **Hardware Integration (CUPS & Print Daemon)**: Worker asíncrono para consumir estados `PURCHASED`, aplicar recorte 3:2 DNP y volcado directo al spool de linux vía `pycups`.
- **Status**: ✅ COMPLETED (Binomial Digital-Physical Verified)

## [2026-04-03] - Phase 41.5: UI Consolidation & Industrial Readiness
- **Dynamic Binational Guard**: Implementada lógica inteligente basada en códigos de país (MX/US) en el frontend.
- **Modo Permisivo Industrial**: Configuración del formulario en modo "Warning-Only" para evitar bloqueos operativos por falta de metadata aduanera no crítica.
- **Status**: ✅ COMPLETED

## [2026-04-01] - Phase 39: Auth Proxy & Kiosk Integration
- **Collaborator Login Handshake**: Integrated `auth_service` with `hr_service`. Supports secure proxy where Auth issues JWT after HR verifies physical credentials (RFID/PIN).
- **O(1) Physical Scans**: Database indexing optimized for SHA-256 RFID hashes, ensuring sub-10ms response times for high-volume entry/exit.
- **Status**: ✅ COMPLETED

## [2026-03-26] - Phase 38: HR Microservice Bootstrap
- **Service Extraction**: Decoupled HR logic from Auth into `hr_service` with dedicated `hr_db`.
- **Infrastructure**: Added healthchecks and automated migrations for HR ecosystem.
- **Status**: ✅ COMPLETED

## [2026-03-25] - Phase 37: HR Microservice Inception
- **Architectural Shift**: Transitioned from Monolithic Auth to SRP-based identity management.
- **Warehouse Lock Concept**: Defined zero-trust barriers for physical inventory operations.
- **Status**: ✅ COMPLETED

## [2026-03-24] - Phase 35: Multi-Tenant Data Consistency & CORS Stabilization
- **Data Homologation**: Synced Company IDs across all 11 services (Enterprise, Logistics, Demo).
- **Master Seed Orchestration**: Automated multi-tenant seeding via `master_seed.py`.
- **CORS Permissiveness**: Resolved preflight (OPTIONS) blocks by unifying allowed headers.
- **Status**: ✅ COMPLETED

## [2026-03-15] - Phase 30: Refresh Token Rotation (RTR) & Security
- **Token Taxonomy**: Implemented `typ` claim (access/refresh/selection) to prevent token misuse.
- **Refresh Token Rotation**: Engineered SHA-256 backed RTR to detect and block replay attacks.
- **Status**: ✅ COMPLETED

## [2026-03-07] - Phase 19: Clean Architecture Enforcement
- **Repository Pattern**: Standardized `IRepository` interfaces across Inventory and Master Data.
- **Dependency Injection**: Implemented automated resolution for service-to-repository mapping.
- **Status**: ✅ COMPLETED

## [2026-03-04] - Phase 4: Traceability & Governance (Guardianship)
- **Governance**: Refactored `MultiTenantBase` inheritance for strict auditor compliance.
- **Traceability**: Integrated `X-Trace-Id` for forensic tracking of login attempts.
- **Status**: ✅ COMPLETED

## [2026-03-03] - Phase 3: Cluster Structures (Holdings)
- **Holding Support**: Introduced `BusinessGroup` model for shared visibility in Master Data.
- **Corporate Context**: Injected `group_id` claim in JWT for cross-company transfers.
- **Status**: ✅ COMPLETED

## [2026-02-25] - Phase 2: Subscription & Entitlements
- **Interconnectivity**: Synchronized `auth_service` with `subscription_service`.
- **Read-Only Mode**: Implemented enforcement for expired tenant subscriptions.
- **Status**: ✅ COMPLETED

## [2026-02-12] - Phase 1: Foundation & T1/T2 Handshake
- **Protocol Inception**: Implementation of OAuth2 Password Flow.
- **Dual-Step Auth**: Engineered the `/login` (T1) and `/select-company` (T2) flow for multi-tenant environments.
- **Standardization**: Established UUIDv5 as the deterministic standard for cross-service entity mapping.
- **Status**: ✅ COMPLETED (Ecosystem Birth)

*(End of historical log)*