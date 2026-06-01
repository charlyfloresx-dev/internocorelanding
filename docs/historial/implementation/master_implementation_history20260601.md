# Implementation History — 2026-06-01

## Phase 164 — Rate Limiter Global + RTR DB Worker + Migration drop

### Rate Limiter — 4 servicios

Patrón idéntico al de `auth_service`. Tres líneas por `main.py`:

```python
# 1. imports
from common.security.limiter import limiter
from slowapi.errors import RateLimitExceeded

# 2. después de FastAPI()
app.state.limiter = limiter

# 3. exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={
        "status": "error",
        "message": "Límite de solicitudes excedido.",
        "meta": {"code": "RATE_LIMIT_EXCEEDED"}
    })
```

Sin `app.state.limiter`, los `@limiter.limit()` en endpoints internos lanzaban `AttributeError` y los límites globales (`2000/h · 100/min` configurados en `Limiter(default_limits=[...])`) no se aplicaban.

### Migration `a9e3b1c0d2f4` — Lock Postmortem

El `DROP TABLE refresh_tokens` bloqueó porque el auth_service tenía el PID 4864 con una transacción abierta (`SAVEPOINT sa_savepoint_1`) en estado `ClientRead`. SQLAlchemy con `pool_pre_ping=True` y `pool_size` por defecto retiene conexiones en el pool; si una transacción no se commitea/rollbackea antes de devolver la conexión al pool, el PID queda idle-in-transaction indefinidamente.

```sql
-- Diagnóstico
SELECT pid, query, state, wait_event FROM pg_stat_activity
WHERE state != 'idle' AND query NOT LIKE '%refresh_tokens%';
-- → PID 4864: SAVEPOINT sa_savepoint_1 | state: active | wait_event: ClientRead

-- Fix
SELECT pg_terminate_backend(4864);
-- → t (éxito). Todas las DROP TABLE encoladas ejecutaron en cascada.
```

Resultado: `still_exists = f`, `alembic_version_auth = a9e3b1c0d2f4`.

### DB Worker `purge_rtr_families.py`

Purga en dos pasos con SQL nativo para bypassar Event Listeners ORM:

```python
# Paso 1: borrar auditoría (Event Listener bloquea DELETE ORM en esta tabla)
await db.execute(text("""
    DELETE FROM refresh_token_rotation_audit
    WHERE family_id IN (
        SELECT id FROM refresh_token_families
        WHERE refresh_window_expires_at < :cutoff
    )
"""), {"cutoff": cutoff})

# Paso 2: borrar familias
await db.execute(text("""
    DELETE FROM refresh_token_families
    WHERE refresh_window_expires_at < :cutoff
"""), {"cutoff": cutoff})
```

`SAFETY_MARGIN_DAYS = 7` previene borrado de familias activas durante failover RDS.

---

## Phase 163 — RTR Frontend Semaphore

### Contexto
Con Phase D completa (backend emite RTR refresh_token desde select-company), el siguiente riesgo era del lado del cliente: si el AT expira y N requests concurrentes reciben 401 simultáneamente, sin semáforo todos intentan `/auth/refresh` al mismo tiempo → N rotaciones → REUSE_DETECTED → lockout falso de usuario.

### Angular — Bugs corregidos en `multi-tenant.interceptor.ts`

**Bug 1 — Headers perdidos en retry:**
```typescript
// ANTES (bug): req es el request original sin headers inyectados
const retryReq = req.clone({ headers: req.headers.set('Authorization', `Bearer ${t}`) });

// DESPUÉS: authReq ya tiene X-Company-ID y X-User-ID inyectados por el interceptor
const retryReq = authReq.clone({ headers: authReq.headers.set('Authorization', `Bearer ${t}`) });
```

**Bug 2 — Cola colgada en fallo de refresh:**
```typescript
// ANTES: catchError solo llamaba logout. refreshTokenSubject quedaba en null.
// filter(t !== null) nunca pasaba → requests en cola colgaban forever.
catchError((refreshErr) => {
  auth.isRefreshing.set(false);
  auth.logout();
  return throwError(() => refreshErr);
})

// DESPUÉS: REFRESH_ABORT desbloquea la cola inmediatamente
const REFRESH_ABORT = '__ABORT__';
// En la cola, el switchMap detecta el sentinel:
switchMap(t => {
  if (t === REFRESH_ABORT) return throwError(() => error);
  // ... retry normal
})
// En el catchError:
catchError((refreshErr) => {
  auth.isRefreshing.set(false);
  auth.refreshTokenSubject.next(REFRESH_ABORT); // FIX: desbloquea cola
  auth.logout();
  return throwError(() => refreshErr);
})
```

### Flutter — `auth_interceptor.dart` (nuevo)

Flutter no tenía ningún manejo de 401 ni refresh automático. Patrón elegido: `Completer<String>` (idiomático Dart, single-threaded safe).

```dart
// Semáforo con Completer
bool _isRefreshing = false;
Completer<String>? _refreshCompleter;

// En onError(401):
if (_isRefreshing) {
  newToken = await _refreshCompleter!.future; // espera al primary
} else {
  final completer = Completer<String>();
  _refreshCompleter = completer;
  _isRefreshing = true;
  try {
    newToken = await _doRefresh();
    completer.complete(newToken);   // libera a todos
  } catch (e) {
    completer.completeError(e);     // falla a todos
    rethrow;
  } finally {
    _isRefreshing = false;
    _refreshCompleter = null;
  }
}
// Retry con nuevo token:
err.requestOptions.headers['Authorization'] = 'Bearer $newToken';
err.requestOptions.extra['_retried'] = true; // anti-loop
final response = await _dio.fetch(err.requestOptions);
handler.resolve(response);
```

**Por qué `Completer` y no `BehaviorSubject`:** Dart es single-threaded (Isolates), no hay race conditions entre el check `_isRefreshing` y la asignación. Un `Completer` completa exactamente una vez y cualquier `await future` posterior al `complete()` resuelve inmediatamente. Sin necesidad de reinicializar subjects.

**Posición en DI:** ÚLTIMO en `addAll([Multi, Resilience, Log, Auth])` → Dio llama `onError` LIFO → `AuthInterceptor` es el PRIMERO en ver el 401.

**Guards contra loops:**
- `extra['_retried'] == true` → skip
- `path.contains('/auth/')` → skip (refresh call no se auto-refresca)

### Verificación en vivo
- Angular: Login T1 → T2 → `Session persisted with refresh_token` ✅
- Dashboard carga, Inventory Documents carga, WebSocket conectado ✅
- Flutter: app corriendo en Moto g04s, departamentos cargando desde API ✅

---

## Phase 159 RTR — Auditoría A+B: Correcciones de Seguridad

### Contexto
Tras la auditoría formal de Phase A (domain model + schema) y Phase B (repository + handler + endpoint) del Refresh Token Rotation stateless, se identificaron 2 bloqueantes ALTA + 4 gaps adicionales. Este registro documenta las correcciones aplicadas.

### B-01: company_id en Repository (BLOQUEANTE → RESUELTO)

**Problema:** Las 3 queries del repo (`get_family`, `rotate_family_atomically`, `revoke_family`) filtraban solo por `id`. Sin `company_id` en el WHERE, un token con `family_id` de empresa A podía acceder a familia de empresa B (IDOR cross-tenant).

**Solución aplicada:**
```python
# ANTES (vulnerable)
stmt = select(RefreshTokenFamily).where(RefreshTokenFamily.id == family_id)

# DESPUÉS (defense-in-depth)
stmt = select(RefreshTokenFamily).where(
    RefreshTokenFamily.id == family_id,
    RefreshTokenFamily.company_id == company_id
)
```

Los 3 métodos de la interfaz `IRefreshTokenRepository` actualizados con `company_id: UUID` como parámetro obligatorio. El handler pasa `token_payload.company_id` (extraído del JWT HMAC-sealed — nunca del cliente).

**Impacto de seguridad:** Previene IDOR en la capa de persistencia. Complementa la validación HMAC del handler — defense-in-depth de 2 capas.

---

### Stack Trace Leak (BLOQUEANTE → RESUELTO)

**Problema:** El catch-all del endpoint exponía errores SQLAlchemy al cliente:
```python
except Exception as e:
    detail=f"Internal error: {str(e)}"  # ← "ForeignKeyViolation on table refresh_token_families..."
```

**Solución:**
```python
except Exception:
    logger.error("Unhandled error in refresh_token_rtr", exc_info=True)  # visible en server logs
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An internal error occurred"   # opaco para el cliente
    )
```

---

### B-02 / StaleDataError (MEDIA → RESUELTO)

**Problema:** Intento de capturar `StaleDataError` como señal de optimistic lock conflict era incorrecto — SQLAlchemy en modo `version_id` nativo lanza `StaleDataError` automaticamente y no necesita captura manual.

**Solución:** Eliminado el try/except inválido. El optimistic locking es manejado por SQLAlchemy vía `__mapper_args__ = {"version_id_col": version_id}` en `BaseDomainEntity`. Handler actualizado para usar `family.version_id` en lugar de `family.version_counter`.

---

### GAP-1: family_salt Hex Validator (MEDIA → RESUELTO)

**Problema:** `TokenFamily.family_salt` aceptaba cualquier string — un salt malformado podría causar errores crípticos al generar HMAC en lugar de fallo explícito en creación.

**Solución:**
```python
@dataclass(frozen=True)
class TokenFamily:
    family_salt: str

    def __post_init__(self):
        if not re.fullmatch(r'^[0-9a-f]{64}$', self.family_salt):
            raise ValueError(f"family_salt must be 64 hex chars, got: {len(self.family_salt)} chars")
```

---

### GAP-2: version_counter vs version_id (MEDIA → RESUELTO)

**Problema:** Existían dos mecanismos de locking en paralelo: `version_id` (ORM-managed, en `BaseDomainEntity.__mapper_args__`) y `version_counter` (manual, columna separada). El handler usaba `version_counter` — el mecanismo menos robusto.

**Solución:** Handler migrado a `version_id` (el que SQLAlchemy trackea automáticamente). El campo `version_counter` queda como columna legacy sin uso en el flujo de locking — candidato a deprecación en Phase D.

---

### GAP-3: Append-Only Enforced en ORM (BAJA → RESUELTO)

**Problema:** `RefreshTokenRotationAudit` heredaba `is_active`/`deleted_at`/`version_id` de `MultiTenantBase` — técnicamente modificable via ORM, contradiciendo el invariante "append-only".

**Solución — Event Listeners:**
```python
from sqlalchemy import event

@event.listens_for(RefreshTokenRotationAudit, "before_bulk_update")
def prevent_audit_update(mapper, connection, target):
    raise RuntimeError("RefreshTokenRotationAudit is append-only — UPDATE prohibited")

@event.listens_for(RefreshTokenRotationAudit, "before_bulk_delete")
def prevent_audit_delete(mapper, connection, target):
    raise RuntimeError("RefreshTokenRotationAudit is append-only — DELETE prohibited")
```

Cualquier `session.query(RefreshTokenRotationAudit).update(...)` o `.delete(...)` lanza `RuntimeError` inmediatamente — enforced en capa ORM, independiente de la lógica de negocio.

---

### Defensa Multicapa Final

| Capa | Mecanismo | Previene |
|---|---|---|
| DB | Compound WHERE `(id, company_id)` | IDOR cross-tenant |
| Handler | HMAC `validate_company_binding()` | Token forging / tampering |
| VO | `__post_init__` hex validator | Salt malformado silencioso |
| ORM | Event Listeners append-only | Corrupción de audit log |
| Endpoint | Stack trace opaco | Information disclosure |

---

### Pendiente: Phase C + D

**Phase C (tests):** `test_refresh_token_rotation.py` con 7 clases / 12+ tests creado. Requiere levantar auth_service + PostgreSQL y ejecutar para confirmar que todos los flujos de los 8 fases del handler funcionan end-to-end.

**Phase D (login integration):** El endpoint `POST /api/v1/auth/refresh` existe y funciona, pero `create_family()` aún no está integrado al flujo `select-company`. Actualmente el login emite tokens sin familia RTR — el endpoint de refresh no tiene familias que rotar. Phase D cierra este gap.

---

## Phase 162 RTR — Phase C (Tests) + Phase D (Login Integration)

### Phase C: Diagnóstico del Hang y Resolución de Tests

**Problema raíz del hang:** `family_salt = "a" * 64` hardcodeado causa bloqueo indefinido por `transactionid` lock en PostgreSQL. La constraint UNIQUE en `family_salt` hace que cada nuevo test intente INSERT con el mismo salt, quedando bloqueado esperando que la transacción anterior (de tests anteriores cuyos procesos Python fueron matados) haga commit o rollback. Los procesos killed no cierran conexiones PostgreSQL — estas quedan en estado `idle in transaction` hasta que PostgreSQL las termine.

**Fix:** `family_salt=os.urandom(32).hex()` — único por test, sin conflicto con runs anteriores.

**Problema de timezones:** `datetime.utcnow().timestamp()` en sistema con timezone local != UTC genera `iat` en el futuro desde la perspectiva del JWT validator (que usa `datetime.now(timezone.utc)`). En México UTC-7, `datetime.utcnow().timestamp()` da un timestamp 7 horas mayor al actual.

**Fix:** `datetime.now(timezone.utc)` en `_issue_refresh_token`, `_issue_access_token`, `rotate_family_atomically`, `revoke_family`.

**MissingGreenlet:** SQLAlchemy marca atributos con `server_default` o `onupdate` como expired tras `flush()`. Acceder a `model.updated_at` sin `await db.refresh(model)` previo causa `MissingGreenlet` — la sesión async intenta un lazy load sincrónico.

**Fix:** `await self.db.refresh(model)` inmediatamente tras `flush()` en `rotate_family_atomically()` y `revoke_family()`.

**tenant_id faltante:** `RefreshTokenRotationAudit` hereda `MultiTenantBase` (tiene `tenant_id NOT NULL`). `log_rotation_event()` no seteaba `tenant_id`. Fix: `tenant_id=company_id`.

### Phase D: Integración al Login

**Punto de inserción:** `SelectCompanyCommandHandler.handle()` — reemplaza patrón `create_refresh_token() + RefreshToken DB record` con `rtr_repo.create_family() + handler._issue_refresh_token(family)`.

**Collaborators excluidos:** `RefreshTokenFamily.user_id FK → users.id`. Los colaboradores industriales tienen UUID propios del HCM que no existen en `users`. Devuelven `refresh_token: None` (acceso por short-lived access tokens únicamente).

**Tabla legacy deprecada:** `refresh_tokens` (modelo `RefreshToken`) — migration `a9e3b1c0d2f4` la elimina. La tabla nunca fue usada por el nuevo endpoint `/auth/refresh` (RTR), solo por `select_company_command.py` que ya migró a RTR families.
