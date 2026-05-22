# Consolidated Tasks — 2026-05-20 (Phase 119)

## Completadas ✅

### Phase 119: inventory_item_variants Migration + Point-in-Time Reprint
- [x] Migración Alembic `002_add_inventory_item_variants.py` en `master_data_service` (con guard `_table_exists`)
- [x] Migración Alembic `002_drop_inventory_item_variants.py` en `inventory_service` (drop one-way)
- [x] Modelo ORM `ItemVariant` creado en `master_data_service/master_app/models/item_variant.py`
- [x] CRUD endpoints `variants.py` en `master_data_service` con Security(require_scope) + foto upload
- [x] Endpoints `variants.py` en `inventory_service` convertidos a HTTP proxy (httpx)
- [x] Repository `sqlalchemy_master_data_repository.py`: `get_products` + `get_product_by_sku` con ORM JOIN `ItemVariant`
- [x] Anti-patrón `has_variants_table` eliminado
- [x] `main.py` en `master_data_service`: router variants registrado con prefix `/api/v1`
- [x] Endpoint `GET /api/v1/inventory/documents/{folio}` — reimpresión con precios point-in-time
- [x] Endpoint `GET /prices/products/{id}/price-at` — soft-close query en `master_data_service`
- [x] `MasterDataClient` ampliado con `get_product_price_at_date()` + `get_product_internal_metadata()`
- [x] `inventory_service/scripts/seed.py` — `ItemVariant` import/seeding removido, `InventoryLevel` lookup por constraint único
- [x] `unified_industrial_seed.py` — `seed_variants_master()` en master_data_db; bloque stale en Section 4 eliminado
- [x] `flows/seed_variants.py` — apunta a `master_data_db` via URL substitution
- [x] `CLAUDE.md` — corregidas DB names: `inventory_db`, `master_data_db`, `subscription_db`
- [x] Verificación typeahead: `?q=MPN-GAR` → Garrett Turbo + precio variante ✅
- [x] Inventory container boot limpio: ✅ SUCCESS × 2, sin errores
- [x] Code Graph: 0 errores, 14 servicios CLEAN
- [x] Ecosystem: 8/8 servicios OK

## Pendientes (deuda técnica activa)
- [ ] `POST /api/v1/pos/checkout` — E2E validation con flows de antigravity (pos.py consulta tablas inexistentes en inventory_db)
- [ ] `audit_logs` faltante en `hcm_db` y `subscription_db` (plan listo en `.claude/plans/`)
- [ ] `internal_id_pattern` faltante en `hr_tenant_configs`
- [ ] Rate limit por endpoint en WMS, MES, HR, Subscription
- [ ] `default_tax_rate` Planta US debería ser 0.0 (actualmente 0.16)
- [ ] Precio según partner seleccionado en typeahead (PriceAgreement context)

### Phase 118: Polymorphic Department Ticket Assignments & Visibility Filters
- [x] **Modelo de Tickets:** Añadido `assigned_department_id` UUID en `tickets_app/models/ticket.py`.
- [x] **Esquemas Pydantic / DTOs:** Actualizados `TicketCreate`, `TicketUpdate`, `TicketRead` y `TicketTriage` en `ticket_dto.py` con `assigned_department_id`.
- [x] **Servicio Core de Tickets:** Actualizado `create_ticket`, `update_ticket` y `get_tickets_with_visibility` en `ticket_service.py` para permitir `assigned_department_id`.
- [x] **Flujo de Triaje (`REASSIGN`):** Modificado `triage_ticket` en `ticket_service.py` para que al reasignar a un departamento, limpie de forma atómica todas las asignaciones individuales previas (`assigned_to_id`, `collaborator_id`, `external_contact_id`).
- [x] **Filtro de Visibilidad y Rutas:** Refactorizado `list_by_visibility` en `ticket_repository.py` para aceptar `department_id` y permitir a los operadores de piso visualizar en `/mine` los tickets asignados a su departamento.


### Fix: Colaborador JWT — 403 en `GET /products/{id}/variants`
- [x] **Root cause identificado:** `collaborator_login_command.py` no pasaba `modules` a `create_final_access_token` → JWT con `"modules": null` → Pydantic coerce a `[]` → `SubscriptionGuard` falla con 403 en cualquier endpoint `INVENTORY_CORE`
- [x] `backend/auth_service/auth_app/commands/collaborator_login_command.py` — agregado `modules=["auth_core", "inventory_core"]` al llamado de `create_final_access_token` (línea 173)
- [x] Confirmado que el flujo POS móvil (scan → `GET /api/v1/inventory/lookup`) no se veía afectado (sin auth, resuelve variante→producto directamente)
- [x] Confirmado que el path multi-empresa (T2 via `select_company_command.py`) ya tenía módulos correctos (venían de subscription service)

### Fix: Colaborador Auth - 403 Forbidden por Desajuste de Scopes
- [x] **Root Cause:** Los endpoints de `master_data` exigen el scope grueso `master_data:read`. Los tokens de colaboradores generados desde la base de datos de Auth contienen permisos granulares (ej: `master_data.product.read`, `master_data.price.read`). Esto causaba que fallara la validación exacta de subconjuntos de FastAPI.
- [x] `backend/common/security/dependencies.py` — Refactorizada la función `require_scope` para soportar resolución de namespaces de seguridad (comparación por prefijo/sufijo).
- [x] Permitido bypass automático para el sufijo `.manage` (mapeando a lectura y escritura).
- [x] Validado el flujo mediante pruebas de login de colaboradores y consulta exitosa a `/warehouses` y `/concepts` retornando `200 OK`.
- [x] **Remediación de Identidad:** Confirmado que el login fallido en el navegador de Carlos Ramírez con ID `003709` se debió a un mismatch con la base de datos de HCM, la cual requiere la credencial correcta `003709A`.

### Fix: UUID Coercion error (500 Error en `GET /api/v1/tickets/`)
- [x] **Root Cause:** En el payload del JWT (`TokenPayload`), los campos `company_id` y `sub` se definen como `Union[uuid.UUID, str]`. Pydantic los valida y los convierte a objetos de tipo `uuid.UUID` si son strings con formato UUID válido. Los endpoints de `tickets_service` y `viatra_service` intentaban aplicar `uuid.UUID(user.company_id)` y `uuid.UUID(user.sub)` directamente, lo cual arrojaba un error de atributo `AttributeError: 'UUID' object has no attribute 'replace'`.
- [x] `backend/tickets_service/tickets_app/routers/ticket_routes.py` — Implementada la función helper `to_uuid(val)` para manejar ambos casos de forma segura y reemplazadas todas las coerciones directas.
- [x] `backend/viatra_service/app/routers/payments.py` — Implementado helper y corregidos los llamados correspondientes.
- [x] `backend/viatra_service/app/routers/booking.py` — Implementado helper y corregidos los llamados correspondientes.
- [x] Validado el correcto funcionamiento del endpoint de tickets retornando `200 OK` en lugar de `500 Internal Server Error`.

### Stack: Rebuild completo
- [x] `docker compose up -d --build` — todas las imágenes reconstruidas con los cambios de Phase 116 + 117
- [x] Validación del ecosistema: 8/8 servicios OK via `validate_ecosystem.ps1`

### Fix: `audit_logs` faltante en `hcm_db` y `subscription_db`
- [x] **Root cause:** `audit_logs` solo existía en `dbname` (auth_service) e `inventory_db`. Los demás DBs aislados nunca tuvieron la migración.
- [x] **Impacto:** `SubscriptionGuard` no podía registrar `GOD_MODE_ACTIVATED` ni `ACCESS_DENIED_402` en endpoints HCM/Subscription (fallaba silenciosamente via fire-and-forget)
- [x] `backend/hcm_service/alembic/versions/001_add_audit_logs.py` — creado (revision: `001_add_audit_logs_hcm`, down_revision: `001_add_id_pattern`)
- [x] `backend/subscription_service/alembic/versions/001_add_audit_logs.py` — creado (revision: `001_add_audit_logs_sub`, down_revision: `000_subscription_baseline`)
- [x] Cadena HCM: `000_hcm_baseline` → `001_add_id_pattern` → `001_add_audit_logs_hcm` (conflicto de heads resuelto)
- [x] Verificado en DB: `SELECT table_name FROM information_schema.tables WHERE table_name = 'audit_logs'` → 1 row en `hcm_db` y `subscription_db`
- [x] Alembic heads: `hcm_db` en `001_add_audit_logs_hcm`, `subscription_db` en `001_add_audit_logs_sub`

### Fix: CLAUDE.md — DB de subscription_service incorrecta
- [x] Tabla sección 2: `subscription_service` figuraba como `dbname (shared)` → corregido a `subscription_db`
- [x] Confirmado con docker-compose: cada servicio tiene su propio DB aislado (salvo auth + notification que comparten `dbname`)

### Feature: Point-in-Time Price Lookup — `GET /api/v1/inventory/documents/{folio}`
- [x] **Diseño:** `InventoryTransaction` no almacena `unit_price` → se resuelve vía soft-close query en `product_prices` al momento del documento
- [x] `backend/inventory_service/inventory_app/schemas/document.py` — `DocumentLineRead` + `DocumentRead` (Pydantic response schemas)
- [x] `backend/master_data_service/master_app/api/v1/endpoints/prices.py` — endpoint interno `GET /prices/products/{product_id}/price-at?as_of=<datetime>` (soft-close query)
- [x] `backend/inventory_service/inventory_app/domain/interfaces/master_data_client.py` — método `get_product_price_at_date` agregado a la interfaz
- [x] `backend/inventory_service/inventory_app/infrastructure/clients/master_data.py` — implementación HTTP del método
- [x] `backend/inventory_service/inventory_app/api/v1/endpoints/documents.py` — endpoint `GET /api/v1/inventory/documents/{folio}` via `MasterDataClient`
- [x] `backend/inventory_service/inventory_app/main.py` — router registrado en `/api/v1/inventory`
- [x] Smoke test: 404 en folio inexistente ✅ · 200 con `items: []` en documento sin transacciones ✅
- [x] **Fix colateral:** `inventory_service` usa `inventory_db` (no `dbname`) — CLAUDE.md tabla sección 2 a corregir

## Pendiente

### Deuda técnica activa
- [ ] `POST /api/v1/pos/checkout` — validación end-to-end con flujos de antigravity
- [x] CLAUDE.md sección 2: `inventory_service` figura como `dbname (shared)` → corregir a `inventory_db`
- [ ] `internal_id_pattern` faltante en `hr_tenant_configs`
- [ ] Audit calls en endpoints HCM (RFID assign, collaborator CRUD) — tabla ya existe, falta el llamado
- [ ] WMS y MES no desplegados en dev stack
