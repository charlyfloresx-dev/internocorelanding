# Master Implementation History — 2026-05-20 (Phase 119)

## Phase 119: inventory_item_variants SSOT Migration + Point-in-Time Document Reprint

### Contexto y Decisión Arquitectónica

`inventory_item_variants` era una tabla de datos maestros (catálogo de equivalentes por proveedor/MPN) que vivía equivocadamente en `inventory_db`. El `master_data_service` usaba un check dinámico `has_variants_table` que siempre devolvía `False` al intentar detectar la tabla en `master_data_db` donde no existía. Resultado: el typeahead `GET /products/?q=` nunca encontraba variantes por código de proveedor.

**Decisión:** Mover la tabla a `master_data_db` como SSOT. Las variantes son datos de catálogo, no datos de stock — pertenecen al master data domain.

### Implementación

#### Migraciones (two-phase)
1. `master_data_service/alembic/versions/002_add_inventory_item_variants.py`: DDL completo (21 columnas + 4 índices + UniqueConstraint). Guard `_table_exists` para idempotencia.
2. `inventory_service/alembic/versions/002_drop_inventory_item_variants.py`: `DROP TABLE IF EXISTS inventory_item_variants`. Downgrade intencional `pass` — migración irreversible.

#### ORM + CRUD en master_data_service
- `master_app/models/item_variant.py`: Modelo `ItemVariant(MultiTenantBase)`.
- `master_app/api/v1/endpoints/variants.py`: 3 endpoints. Upsert por `(company_id, internal_sku, mfg_part_number)`. Foto upload via `get_storage_provider()`. Guard: `Security(require_scope(["master_data:read/write"]))`.

#### Repository refactor — typeahead con JOIN
`sqlalchemy_master_data_repository.get_products` reescrito:
```python
# ORM LEFT JOIN
select(Product, price_subq, ItemVariant)
    .outerjoin(ItemVariant, and_(
        ItemVariant.product_id == Product.id,
        ItemVariant.company_id == Product.company_id,
    ))
    .where(or_(
        Product.sku.ilike(f"%{q}%"),
        Product.name.ilike(f"%{q}%"),
        ItemVariant.internal_sku.ilike(f"%{q}%"),
        ItemVariant.mfg_part_number.ilike(f"%{q}%"),
    ))
```
Cuando match viene de variante: `product.sku = variant.internal_sku`, nombre enriquecido, precio = `variant.unit_price`.

#### inventory_service — HTTP Proxy
`inventory_app/api/v1/endpoints/variants.py` convertido a thin proxy `httpx` hacia `master_data_service`. Sin dependencia en modelos locales.

#### Point-in-Time Document Reprint
- `GET /api/v1/inventory/documents/{folio}`: Lee `InventoryDocument` + `InventoryTransaction`s. Por cada `product_id` único llama `MasterDataClient.get_product_price_at_date(as_of=document.created_at)`.
- Soft-close query en master_data: `created_at <= as_of AND (valid_until IS NULL OR valid_until > as_of)`.

#### Seed Cleanup
- `inventory_service/scripts/seed.py`: Import `ItemVariant` y bloque de seeding eliminados. `InventoryLevel` lookup por `(company_id, warehouse_id, product_id)` en vez de `id` (evita conflicto de constraint tras cambio de ID derivado).
- `unified_industrial_seed.py`: Nueva función `seed_variants_master(session)` en Section 3 (master_data_db). Bloque stale en `seed_inventory()` eliminado.
- `flows/seed_variants.py`: `AsyncSessionLocal` reemplazado por factory que apunta a `master_data_db`.

### Verificación
```
GET /api/v1/products/?q=MPN-GAR
→ status: success
→ name: "Turbocharger Assembly (Garrett MPN-GAR-701)"
→ sku: "TRB-700"
→ last_price: "1200.0000" MXN ✅
```
Inventory boot: `✅ SUCCESS × 2` — sin errores. Code Graph: 0 errores.

---

## Asignación Polimórfica de Tickets a Departamentos & Filtros de Visibilidad (Phase 118)

### Contexto
Para dotar de flexibilidad a la gestión industrial de mesa de ayuda (Tickets Service), se requiere que los tickets puedan ser asignados directamente a departamentos completos (`assigned_department_id`), y no solo a usuarios, colaboradores individuales o contactos externos. Adicionalmente, se debe garantizar la consistencia en el flujo de triaje (`REASSIGN`) limpiando asignaciones previas, y permitir a los operadores de piso ver en sus bandejas los tickets asignados a su departamento o área.

---

## Decisiones Arquitectónicas Clave (Phase 118)

### 1. Polimorfismo en la Asignación de Tickets
- **Modelo Relacional Desacoplado:** El modelo `Ticket` en `tickets_service` almacena la referencia `assigned_department_id` (UUID, indexado) de forma opcional sin llaves foráneas estrictas hacia la base de datos de HCM. Esto respeta la independencia de microservicios y simplifica los límites de almacenamiento.
- **DTOs Pydantic:** Se actualizaron `TicketCreate`, `TicketUpdate`, `TicketRead` y `TicketTriage` de forma transversal con el nuevo campo opcional `assigned_department_id`.

### 2. Triaje Inteligente de Asignaciones (`REASSIGN`)
- **Limpieza Atómica:** Cuando un supervisor reasigna un ticket a un departamento en particular (`action == REASSIGN` con `assigned_department_id`), el backend limpia de forma automática y atómica las asignaciones individuales previas:
  - `assigned_to_id = None`
  - `collaborator_id = None`
  - `external_contact_id = None`
- Esto previene estados ambiguos (ej. un ticket asignado a un técnico pero a la vez a la cola de un departamento) y regresa el ticket limpiamente a la cola del departamento en estatus `ASSIGNED`.

### 3. Filtros de Visibilidad por Área para Operadores
- **Consulta Dinámica (`list_by_visibility`):** El repositorio SQLAlchemy amplía su método de visibilidad para aceptar `department_id: Optional[UUID] = None`.
- Si el usuario no es administrador y se le asocia un `department_id`, el motor de base de datos incluye `Ticket.assigned_department_id == department_id` dentro del bloque de condiciones OR de visualización. Esto faculta a los operadores para que vean los tickets de su departamento en su bandeja `/mine`.
- El endpoint `/mine` en `ticket_routes.py` propaga el query parameter opcional de manera transparente.

---

## Namespace Scope Matching Security Bridge (Collaborator Auth Stabilized)

### Contexto
Los colaboradores de planta (roles industriales como operadores de almacén) ingresan al sistema con tokens JWT hidratados a partir de sus permisos granulares registrados en la base de datos (por ejemplo, `master_data.product.read`). Sin embargo, los endpoints de la API de Datos Maestros (puerto 8003) exigen scopes genéricos de servicio (como `master_data:read`). Esta discrepancia causaba errores `403 Forbidden` al intentar consultar almacenes y conceptos desde el frontend.

Esta sesión resolvió la brecha mediante la introducción de una validación basada en namespaces dentro del inyector de seguridad global (`require_scope`).

---

## Decisiones Arquitectónicas Clave

### 1. Resolución de Namespaces de Seguridad
**Problema:** Los endpoints declaran un scope grueso (`servicio:accion`, e.g., `master_data:read`) pero el token JWT del usuario tiene una lista de permisos granulares (`servicio.entidad.accion`, e.g., `master_data.product.read`).  
**Solución:** Modificar la función `require_scope` en `backend/common/security/dependencies.py` para comparar scopes usando lógica de namespaces si no se encuentra una coincidencia exacta:
- Si el scope requerido es `master_data:read`, se divide en su namespace (`master_data`) y acción (`read`).
- Se verifica si alguno de los scopes del usuario coincide con el patrón `namespace.<entidad>.accion`.
- De esta manera, `master_data.product.read` satisface `master_data:read`.

### 2. Equivalencia y Superconjunto del Sufijo `manage`
En el esquema de permisos de InternoCore, `manage` representa el superconjunto de operaciones de escritura y lectura.
- El algoritmo mapea de forma dinámica la acción `manage` para satisfacer tanto la validación de `read` como `write`.
- Por ejemplo, si el token posee `inventory.stock.manage`, cumplirá automáticamente con solicitudes que requieran `inventory.stock:read` o `inventory.stock:write`.

### 3. Preservación del Modo Fallback y Wildcard (`*`)
- Se conserva la compatibilidad con el comodín de super-administrador (`*`) que salta cualquier requerimiento.
- Si no hay coincidencias de namespace ni comodines, el sistema falla de manera cerrada (fail-closed) retornando `403 Forbidden`.

### 4. Corrección de Identidad Física de Colaboradores (`internal_id`)
- **Problema:** En los logs de errores se observaba el uso del ID `"003709"` para iniciar sesión por PIN de Carlos Ramírez, resultando en `401 Unauthorized`.
- **Análisis:** En la base de datos de HCM, el registro de Carlos tiene el ID `"003709A"`.
- **Solución:** Se documentó e instruyó la alineación de credenciales. La autenticación con el ID correcto `003709A` (o `301` para Ana García) opera de manera perfecta.

### 5. Coerción Segura de Identificadores (UUID Coercion Fix)
- **Problema:** Los campos `company_id` y `sub` del payload del token son validados por Pydantic como `Union[uuid.UUID, str]`. Si el token tiene un formato UUID válido, Pydantic los hidrata directamente como objetos `uuid.UUID`. Al invocar `uuid.UUID(user.company_id)` o `uuid.UUID(user.sub)` en `tickets_service` y `viatra_service`, Python lanzaba `AttributeError: 'UUID' object has no attribute 'replace'`.
- **Solución:** Se introdujo la función helper `to_uuid(val)` para interceptar el tipo: si ya es un objeto `uuid.UUID`, lo retorna tal cual; en caso de ser un string, realiza la inicialización. Se reemplazaron todas las coerciones directas obsoletas.

---

## Archivos Creados

No se requirieron archivos nuevos permanentes. Se utilizaron scripts temporales de prueba (`debug_roles.py` y `test_scope_fix.py`) que fueron limpiados tras certificar el éxito del flujo.

## Archivos Modificados

| Archivo | Cambio |
|---|---|
| `backend/common/security/dependencies.py` | Refactorizado `require_scope` con el helper `_scope_satisfies` para namespaces y equivalencia de `manage` |
| `backend/tickets_service/tickets_app/routers/ticket_routes.py` | Introducido `to_uuid` y reemplazadas las llamadas a `uuid.UUID` en parámetros de usuario |
| `backend/viatra_service/app/routers/payments.py` | Introducido `to_uuid` y reemplazados llamados correspondientes |
| `backend/viatra_service/app/routers/booking.py` | Introducido `to_uuid` y reemplazados llamados correspondientes |
| `backend/common/SERVICE_LOG.md` | Documentada la fase 114 de seguridad |
| `REPO_LOG.md` | Registrada la Phase 117 de unificación e identidad en planta |
| `docs/historial/tasks/consolidated_tasks20260520.md` | Agregadas las tareas de remediación completadas |

---

## Flujo de Validación E2E Certificado

El script de prueba E2E ejecutó con éxito el siguiente ciclo:
```
1. POST /auth/collaborator-login {"internal_id": "301", "identity_identifier": "1234", ...}
   → 200 OK
   → JWT con scopes: ['inventory.document.create', 'inventory.stock.read', 'master_data.price.read', 'master_data.product.read', 'pos.checkout']
   
2. GET /api/v1/warehouses [Requiere: master_data:read]
   → Validador: ¿master_data.product.read satisface master_data:read?
   → Sí (Namespace: master_data, Acción: read)
   → 200 OK (3 almacenes retornados)

3. GET /api/v1/concepts [Requiere: master_data:read]
   → Validador: ¿master_data.product.read satisface master_data:read?
   → Sí
   → 200 OK (6 conceptos estándar retornados)
```
