# Consolidated Tasks — 2026-05-17

## Resumen de la Jornada
Estabilización del flujo de identidad industrial (Collaborator Login) y corrección de múltiples bugs críticos en el ecosistema de microservicios.

---

## ✅ Bugs Resueltos

### 1. Collaborators no se persistían en `hcm_db` (Savepoint Corruption)
- **Archivo:** `backend/scripts/unified_industrial_seed.py`
- **Síntoma:** El seed mostraba `DONE Collaborator: ... (Merged)` y `Committed!` pero la tabla `collaborators` tenía 0 filas.
- **Causa Raíz:** El `AuditService.log_action()` dentro de `_safe_add()` fallaba porque `hcm_db` no tiene la tabla `audit_logs`. Al fallar el SQL, PostgreSQL marcaba el savepoint como "aborted", provocando un rollback silencioso del `merge()` aunque Python atrapaba la excepción.
- **Fix:** Aislar la llamada de auditoría en su propio savepoint anidado (`async with session.begin_nested()`), de modo que si falla, el savepoint padre (donde vive el merge real) sobrevive intacto.
- **Impacto:** Afectaba a TODOS los microservicios sin tabla `audit_logs` (hcm_db, subscription_db, etc.).

### 2. `supervisor_id` con Foreign Key inválida (NoForeignKeysError)
- **Archivos:** 
  - `backend/hcm_service/hcm_app/models/collaborator.py`
  - `backend/hcm_service/alembic/versions/000_hcm_baseline.py`
- **Síntoma:** HCM Service crasheaba al arrancar con `NoForeignKeysError` en la relationship `supervisor`.
- **Causa Raíz:** Se eliminó la FK constraint de `supervisor_id` en la migración (por diseño: el supervisor es un UUID libre), pero el modelo ORM aún esperaba un FK implícito.
- **Fix:** Agregar `primaryjoin="Collaborator.id == Collaborator.supervisor_id"` a la relationship y mantener `foreign_keys=[supervisor_id]` explícito.
- **Nota:** El supervisor puede tener muchos colaboradores a su cargo (1:N libre sin FK rígida).

### 3. GET requests bloqueados en modo READ-ONLY (403 Forbidden)
- **Archivo:** `backend/common/security/dependencies.py`
- **Síntoma:** Tras login de colaborador con suscripción `PAST_DUE`, todas las peticiones (incluyendo GET) devolvían `403 Forbidden - User is in READ-ONLY mode`.
- **Causa Raíz:** `get_current_active_user()` bloqueaba indiscriminadamente si `readonly=True`, sin distinguir entre lecturas y mutaciones.
- **Fix:** Inyectar `Request` de FastAPI y solo bloquear si `request.method not in ("GET", "OPTIONS", "HEAD")`.

### 4. Mensajes en inglés en HCM internal endpoint
- **Archivo:** `backend/hcm_service/hcm_app/api/v1/endpoints/internal.py`
- **Síntoma:** Respuestas de error en inglés ("Collaborator not found or credentials invalid").
- **Fix:** Traducir todos los mensajes a español ("Colaborador no encontrado o credenciales inválidas").

### 5. Columna `translation_key` faltante en migración HCM
- **Archivo:** `backend/hcm_service/alembic/versions/000_hcm_baseline.py`
- **Síntoma:** Error `column collaborators.translation_key does not exist` en queries del modelo.
- **Fix:** Agregar `sa.Column('translation_key', sa.String(length=100), nullable=True)` al baseline y ejecutar `ALTER TABLE` en la DB live.

### 6. Pérdida del Bottom Navigation Shell en la restauración de sesión móvil
- **Archivo:** `c:\API\interno\src\interno_billing_app\lib\features\auth\presentation\setup_screen.dart`
- **Síntoma:** En la auto-autenticación al abrir la app con sesión activa, no se cargaban ni la barra ni los iconos de navegación inferior, dejando al usuario en una pantalla aislada.
- **Causa Raíz:** Se navegaba directamente a `HomeScreen()` como destino en lugar de a `MainNavigationScreen()`.
- **Fix:** Cambiar la redirección de auto-login para que consuma `MainNavigationScreen()`, la cual encapsula e inicializa correctamente la pila IndexedStack y las pestañas del menú.

### 7. Congelamiento o fallo al cambiar de almacén desde el perfil
- **Archivo:** `c:\API\interno\src\interno_billing_app\lib\features\home\presentation\home_screen.dart`
- **Síntoma:** Al presionar "Cambiar Almacén" en el perfil de usuario (tab), la app intentaba hacer un pop del contexto, lo cual fallaba o cerraba la app debido a estar dentro del shell de navegación.
- **Fix:** Reemplazar el `Navigator.pop(context)` por un redireccionamiento limpio `pushReplacement` hacia `WarehouseSelectionScreen` pasando el `companyId` guardado en SharedPreferences.

### 8. Ancho insuficiente del panel lateral de administración de precios (Web)
- **Archivo:** `c:\API\interno\frontend\src\app\modules\catalog\product-catalog.component.ts`
- **Síntoma:** El panel lateral (drawer) de precios se visualizaba muy angosto en pantallas grandes, dificultando la visualización y edición cómoda de múltiples listas de precios y campos logísticos.
- **Fix:** Agregar la propiedad `width: 'md:w-[750px] w-full'` a los cuatro disparadores del drawer en el catálogo de productos.

### 9. Error de Compilación "Not a constant expression" al restaurar sesión móvil
- **Archivo:** `c:\API\interno\src\interno_billing_app\lib\features\auth\presentation\setup_screen.dart`
- **Síntoma:** Al compilar para Android, Gradle fallaba con error de análisis estático al intentar crear la ruta de `MainNavigationScreen()`.
- **Causa Raíz:** Falta de importación de `main_navigation_screen.dart` dentro del módulo de autenticación.
- **Fix:** Importar la clase correspondiente y corregir el constructor eliminando el modificador de constante no disponible.

### 10. Despliegue de Código Crudo de Barras / QR en la Lista del Carrito
- **Archivo:** `c:\API\interno\src\interno_billing_app\lib\features\home\presentation\sales_screen.dart`
- **Síntoma:** Cuando un operador escaneaba un código de barras o código QR erróneamente (como el QR de configuración), la lista mostraba el texto crudo del código (un dump JSON) en lugar del nombre del artículo, con un precio por defecto sin estructurar.
- **Fix:** Rediseñar la fila del carrito con un layout de doble línea que muestra el Nombre del Producto (`item['name']`) en texto destacado y el código (`item['code']`) como un subtítulo de bajo contraste, aplicando controles `TextOverflow.ellipsis`.

---

## 🔧 Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `backend/scripts/unified_industrial_seed.py` | Savepoint aislado para AuditService |
| `backend/hcm_service/hcm_app/models/collaborator.py` | FK removida + primaryjoin en supervisor |
| `backend/hcm_service/alembic/versions/000_hcm_baseline.py` | translation_key + FK constraint removida |
| `backend/common/security/dependencies.py` | Readonly solo bloquea mutaciones |
| `backend/hcm_service/hcm_app/api/v1/endpoints/internal.py` | Mensajes traducidos a español |
| `backend/auth_service/auth_app/api/v1/endpoints/auth.py` | Generación de QR dinámico basado en ?api_url |
| `backend/auth_service/auth_app/api/v1/endpoints/health.py` | Endpoint /api/v1/health para pings móviles |
| `frontend/src/app/core/services/auth.service.ts` | Envío de API URL del cliente al solicitar QR |
| `src/interno_billing_app/.../login_screen.dart` | Conexión test GET a /health con SnackBar |
| `src/interno_billing_app/.../setup_screen.dart` | Import de MainNavigationScreen y corrección de const |
| `src/interno_billing_app/.../sales_screen.dart` | Layout premium de doble línea para el carrito (Nombre/Código) |
| `frontend/.../product-catalog.component.ts` | Ancho de drawer a 750px en triggers de precios y catálogo |

---

## 📋 Pendientes

- [x] Generación dinámica de QR URL para evitar IPs internas de Docker y soportar múltiples entornos de red (parámetro query `api_url` desde el frontend).
- [x] Conexión y Ping de Health instantáneo al escanear QR en la App móvil (Dio test GET a `/api/v1/health` antes de guardar configuración).
- [x] Regla Soft-Close implementada en `product_service.py` — filtro `valid_until IS NULL` en todos los queries de resolución de precio. Documentada en `06_PRICES_AND_FISCAL_CATALOGS.md` y `PRICING_AND_CONTRACTS.md`.
- [ ] **[PENDIENTE] Point-in-Time Price Lookup para Reconstrucción de Documentos**: Implementar sobrecarga `as_of_date` en `ProductService.lookup_product_by_code()` y en `PriceAgreement` lookup. Al reabrir/reimprimir un documento (`InventoryDocument`, `SaleOrder`, `Invoice`), pasar `as_of_date = documento.created_at` para recuperar el precio vigente en esa fecha usando la query:
  ```python
  and_(ProductPrice.created_at <= as_of_date, or_(ProductPrice.valid_until.is_(None), ProductPrice.valid_until > as_of_date))
  ```
  Afecta: `product_service.py`, `document_service.py`, cualquier handler que reconstruya líneas de documento histórico.
- [ ] Agregar tabla `audit_logs` a los baselines de Alembic de microservicios satélite (hcm, subscription, tickets, inventory) para habilitar auditoría forense completa en cada DB.
- [ ] Columna `internal_id_pattern` faltante en tabla `hr_tenant_configs` (el seed del HCM falla en ese punto, pero el servicio arranca correctamente).
- [ ] Revisar el `default_tax_rate` de Planta US (actualmente 0.16, debería ser 0.0 para operaciones en USA).
- [ ] Validar que el flujo completo Login → Select Company → Dashboard funcione end-to-end con el colaborador Carlos Ramírez.
