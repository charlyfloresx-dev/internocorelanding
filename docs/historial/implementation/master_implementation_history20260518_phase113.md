# Master Implementation History — 2026-05-18 (Phase 113)
## Sprint 1: Security Hardening + GOD MODE Panel

---

## Hallazgos Auditados y Decisiones

### 1. Eliminación del default `GOD_MODE_ACTIVE`

**Antes:**
```python
int_admin_master_key: str = Field(default="GOD_MODE_ACTIVE", ...)
# + en subscription_guard.py:
master_key = getattr(settings, "int_admin_master_key", "GOD_MODE_ACTIVE")
# + en middleware.py:
bypass_tenant = request.headers.get("X-Admin-Master-Key") == "GOD_MODE_ACTIVE"
```

**Problema:** 3 lugares distintos con el string `"GOD_MODE_ACTIVE"` hardcodeado. Cualquier entorno sin `CORE_ADMIN_MASTER_KEY` en su `.env` era bypasseable con una clave conocida públicamente.

**Después:**
- `config.py`: `Field(...)` sin default. Falla al arrancar si no está configurado.
- `subscription_guard.py`: `settings.int_admin_master_key` directo.
- `middleware.py`: `_settings.int_admin_master_key` con import explícito.

### 2. RLS — Fail-Open → Fail-Closed

**Antes:**
```python
cursor.execute(f"SET app.current_tenant = '{ctx.company_id}';")  # f-string sin validar
except Exception as e:
    pass  # conexión contaminada vuelve al pool
```

**Después:**
```python
tenant_str = str(_uuid.UUID(str(ctx.company_id)))  # lanza ValueError si no es UUID válido
cursor.execute(f"SET LOCAL app.current_tenant = '{tenant_str}';")
except Exception as e:
    connection_record.invalidate()  # no vuelve al pool
    raise  # 500 explícito > data leak silencioso
```

**Decisión:** Usar `SET LOCAL` en lugar de `SET` — `SET LOCAL` aplica solo a la transacción actual, `SET` persiste en la sesión. `SET LOCAL` es más seguro en pooling.

### 3. BOLA en POS — Por qué los `text()` raw bypasean el ORM interceptor

El `do_orm_execute` de `database.py` solo intercepta queries construidos con el ORM de SQLAlchemy. Los `text()` raw van directamente al driver asyncpg sin pasar por el interceptor. Esto significa que para cualquier `text()`, el filtro de tenant debe estar en el SQL explícitamente.

**Fix aplicado:** `AND company_id = :cid` en product query + validación previa de warehouse contra tenant.

### 4. Arquitectura del Panel GOD MODE

```
Frontend /admin/system-control
    ↓ input[type=password] — en memoria, no localStorage
    ↓ confirmación doble
    ↓ 3 intentos máx (GodModeStore.isLocked)
    ↓
POST /api/v1/admin/elevate
    Header: X-Admin-Master-Key (no en body)
    ↓
    Rate limit: 3/hour SlowAPI
    Validate: settings.int_admin_master_key
    Audit: AuditService.log_action(action="GOD_MODE_ACTIVATED", ip, ua, jti)
    Token: create_god_mode_token() → (JWT 300s, jti)
    ↓
Response: { access_token, expires_in: 300, metadata.jti, warning }
    ↓
Frontend GodModeStore:
    token.set(access_token)       → en memoria
    expiresAt.set(now + 300_000)  → auto-clear via setTimeout
    ↓
GodModeInterceptor: inyecta Bearer token en lugar del normal
    ↓
GET /api/v1/admin/security-logs
    Auth: Bearer <god_token>  (scopes: ["*"])
    → audit_logs WHERE action LIKE 'GOD_MODE%'
    → tabla con parpadeo rojo si < 24h
```

### 5. Decisión sobre `create_god_mode_token()` vs `create_admin_god_token()`

Se creó `create_god_mode_token()` separada por:
- Retorna `(token, jti)` — el jti es necesario para el panel de revocación
- TTL 300s en lugar de 1800s
- Claim `god_mode: True` identificable en logs
- Claim `typ: "access"` mantenido — para no romper el middleware que valida typ

`create_admin_god_token()` se conservó con `bypass_tenant: True` para la ruta `/handshake` legacy que ya existe en producción.

---

## Invariante de Seguridad Nuevo

> Toda activación de GOD MODE debe generar exactamente un registro en `audit_logs` con `action="GOD_MODE_ACTIVATED"`, `client_ip`, `user_agent`, y `new_value.jti`. El logger `security.god_mode` emite adicionalmente un `CRITICAL` para sistemas de SIEM que lean logs de contenedor.
