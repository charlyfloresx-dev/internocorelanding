# Implementation History — 2026-06-01

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
