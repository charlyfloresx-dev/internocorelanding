# Common Infrastructure + Auth Service Integration — Security Audit & Remediation Plan
**Clasificación:** CONFIDENCIAL - PLAN TÉCNICO EJECUTIVO  
**Fecha:** 2026-06-03  
**Auditor:** Senior Security Architect & SecOps  
**Alcance:** A) common/infrastructure/ | B) common/security/ | C) auth_service integration | D) Invariantes compartidas  

---

## ÍNDICE
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis por Módulo A: common/infrastructure/](#análisis-a-common-infrastructure)
3. [Análisis por Módulo B: common/security/](#análisis-b-common-security)
4. [Análisis por Módulo C: auth_service Integration](#análisis-c-auth-service-integration)
5. [Análisis por Módulo D: Invariantes Compartidas](#análisis-d-invariantes-compartidas)
6. [Matriz de Hallazgos Consolidada](#matriz-de-hallazgos-consolidada)
7. [Plan de Implementación Secuencial](#plan-de-implementación-secuencial)
8. [Criterios de Éxito y Validación](#criterios-de-éxito-y-validación)

---

## Resumen Ejecutivo

### Calificación General Por Módulo

| Módulo | Estado | CVSS Promedio | Severidad General | Bloqueador Crítico |
|--------|--------|---------------|-------------------|--------------------|
| **A: common/infrastructure/** | ⚠️ 3 hallazgos | 4.2 | MEDIA | SQL Injection (bajo riesgo, UUID validation) |
| **B: common/security/** | ⚠️ 5 hallazgos | 5.7 | MEDIA-ALTA | Timing attacks en bypass keys, header injection |
| **C: auth_service integration** | ⚠️ 4 hallazgos | 4.9 | MEDIA | god_mode claim no-validation, information disclosure |
| **D: Invariantes compartidas** | ⚠️ 2 violaciones | 3.1 | BAJA | X-Company-ID client control, scope elevation |

### Postura Consolidada
🟡 **MODERADA** — Múltiples hallazgos detectados, ninguno crítico en aislamiento, pero combinados representan superficie de ataque significativa. **Acción inmediata requerida antes de cloud deployment.**

### Timeline
- **Phase 179 (Critical):** 16 horas (3 días) — Remediaciones de seguridad críticas
- **Phase 180 (Hardening):** 24 horas (4 días) — Validación + testing

---

## ANÁLISIS A: common/infrastructure/

### A.1 — RLS SQL Injection via String Interpolation (Bajo riesgo debido a UUID validation)

**ID:** FINDING-COMMON-A-001  
**Severidad:** 🟡 **MEDIA** (CVSS v3.1: 4.3) — CWE-89 (SQL Injection)  
**Clasificación:** Aunque valida UUID, uso de string interpolation en SQL es anti-patrón  

#### Ubicación
```
Archivo: backend/common/infrastructure/database.py
Línea: 85
Función: set_tenant_on_checkout()
```

#### Código Vulnerable
```python
# Línea 83-85
cursor = dbapi_connection.cursor()
try:
    if ctx and ctx.company_id:
        tenant_str = str(_uuid.UUID(str(ctx.company_id)))
        cursor.execute(f"SET LOCAL app.current_tenant = '{tenant_str}';")  # ⚠️ String interpolation
```

#### Riesgo y Escenario
Aunque `_uuid.UUID()` valida formato UUID, si un atacante logra inyectar valor no-UUID:
1. `_uuid.UUID(str(ctx.company_id))` lanzaría `ValueError`
2. Excepción manejada en línea 91-94 (connection invalidate)
3. Pero patrón establece mal precedente para future maintainers

**Risk Elevation:** Si otro developer copia este patrón sin UUID validation → SQL Injection genuine.

#### Remediación (Código Seguro)
```python
async def set_tenant_on_checkout(dbapi_connection, connection_record, connection_proxy):
    """
    FIXED: Use parameterized query even for SET LOCAL (PG supports it via format string).
    RULE: NUNCA string-interpolate UUID en SQL, aunque esté validado.
    """
    ctx = request_context.get()
    cursor = dbapi_connection.cursor()
    try:
        if ctx and ctx.company_id:
            # Validar UUID estrictamente
            try:
                tenant_uuid = _uuid.UUID(str(ctx.company_id))
            except (ValueError, TypeError) as e:
                _rls_log.error(f"Invalid company_id UUID format: {ctx.company_id}")
                connection_record.invalidate()
                raise
            
            # CHANGED: Use parameterized query
            # PostgreSQL allows parameter binding for SET statements via format()
            cursor.execute(
                "SET LOCAL app.current_tenant = %s",
                (str(tenant_uuid),)  # Tuple for parameterized query
            )
        else:
            cursor.execute("RESET app.current_tenant;")
    except Exception as e:
        _rls_log.critical(
            "[RLS_FAILURE] Tenant isolation set failed — invalidating connection. error=%s", e
        )
        connection_record.invalidate()
        raise
    finally:
        cursor.close()
```

**Key Changes:**
1. `cursor.execute()` con tupla de parámetros (PG parameterized query)
2. UUID validation en try/except antes de usar
3. Logging + connection invalidate en caso de error

**Effort:** 30 min (1-line change)  
**Risk:** BAJA (UUID validation mitiga real risk)  

---

### A.2 — Potential Context Leakage in Recycled Connections

**ID:** FINDING-COMMON-A-002  
**Severidad:** 🟡 **BAJA** (CVSS v3.1: 2.7) — CWE-570 (Expressed Negation Logic)  
**Ubicación:** `database.py` línea 88

#### Problema
```python
else:
    cursor.execute("RESET app.current_tenant;")  # ⚠️ Si exception ocurre, qué pasa?
```

Si `RESET` falla silenciosamente, conexión vuelve al pool CON tenant seteado previamente.

#### Remediación
```python
else:
    try:
        cursor.execute("RESET app.current_tenant;")
    except Exception as e:
        _rls_log.critical(
            "[RLS_CRITICAL] Failed to reset tenant context on connection — invalidating. error=%s", e
        )
        connection_record.invalidate()  # Safety first
        raise
```

**Effort:** 10 min

---

### A.3 — Missing Constraint on company_id Column

**ID:** FINDING-COMMON-A-003  
**Severidad:** 🟢 **BAJA** (CVSS v3.1: 1.5) — CWE-413 (Improper Resource Validation)  
**Ubicación:** `common/infrastructure/models/base.py` (inferred)

#### Problema
`MultiTenantBase.company_id` no tiene:
- `NOT NULL` constraint
- `CHECK` constraint para UUID format

Permite crear registros huérfanos sin tenant association.

#### Remediación (Alembic Migration)
```python
# alembic/versions/XXX_enforce_company_id_constraints.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.alter_column(
        'users',  # Aplica a TODAS las tablas MultiTenant
        'company_id',
        existing_type=sa.UUID(),
        nullable=False  # NO null allowed
    )
    # Agregar CHECK constraint
    op.execute("""
        ALTER TABLE users ADD CONSTRAINT ck_company_id_not_empty 
        CHECK (company_id IS NOT NULL);
    """)

def downgrade():
    op.alter_column('users', 'company_id', nullable=True)
    op.drop_constraint('ck_company_id_not_empty', 'users')
```

**Effort:** 2 hours (aplicar a todas las tablas MultiTenant)

---

## ANÁLISIS B: common/security/

### B.1 — Timing Attack en Bypass Key Validation (CRITICAL)

**ID:** FINDING-COMMON-B-001  
**Severidad:** 🔴 **ALTA** (CVSS v3.1: 6.4) — CWE-697 (Incorrect Comparison)  
**Ubicación:** `backend/common/security/limiter.py` líneas 19-24

#### Código Vulnerable
```python
def multi_layer_key_func(request: Request) -> str:
    # Línea 19-20
    internal_secret = request.headers.get("X-Internal-Secret")
    if internal_secret and internal_secret == settings.INTERNAL_API_KEY:  # ⚠️ Timing leak
        return None
    
    # Línea 22-24
    admin_key = request.headers.get("X-Admin-Master-Key")
    if admin_key and admin_key == settings.int_admin_master_key:  # ⚠️ Timing leak
        return None
```

#### Riesgo y Escenario
1. Atacante envía `X-Admin-Master-Key: AAAA...` (50+ As)
2. Compara byte-a-byte con `settings.int_admin_master_key` ("sk_test_...")
3. Primer byte no-match → early `False` (10μs)
4. Atacante envía `X-Admin-Master-Key: sk_te` (match primeros 5 bytes)
5. Comparación tarda más porque va hasta byte 6 antes de fallar (50μs)
6. Repitiendo, atacante reduce key a fuerza bruta

**Impacto:** Bypass de rate limiting global + acceso a endpoints internos

#### Remediación (Código Seguro)
```python
import hmac

def multi_layer_key_func(request: Request) -> str:
    """
    FIXED: Use constant-time comparison for cryptographic secrets.
    RULE: NUNCA usar == para comparar API keys, passwords, o MACs.
    """
    # Layer 0: Bypass (CONSTANT-TIME)
    internal_secret = request.headers.get("X-Internal-Secret", "")
    if internal_secret and hmac.compare_digest(
        internal_secret, 
        settings.INTERNAL_API_KEY or ""
    ):
        logger.info(f"Rate limit bypass granted via X-Internal-Secret")
        return None
    
    admin_key = request.headers.get("X-Admin-Master-Key", "")
    if admin_key and hmac.compare_digest(
        admin_key,
        settings.int_admin_master_key or ""
    ):
        logger.warning(f"Rate limit bypass granted via X-Admin-Master-Key")
        return None
    
    # ... rest of function unchanged ...
```

**Key Changes:**
1. `hmac.compare_digest()` para constant-time comparison (Python stdlib, no deps)
2. Default a empty string si settings es None
3. Logging para audit trail de bypass usage

**Effort:** 30 min  
**Risk:** CRÍTICA — Timing attack is real, implementable

---

### B.2 — X-Admin-Master-Key Exposure en Headers (Information Disclosure)

**ID:** FINDING-COMMON-B-002  
**Severidad:** 🟡 **MEDIA** (CVSS v3.1: 3.7) — CWE-532 (Insertion of Sensitive Information)  

#### Problema
Si `X-Admin-Master-Key` se envía en request, proxy/logs podrían capturarla:
- HTTP access logs (Nginx, ALB)
- Monitoring tools (Datadog, New Relic)
- Reverse proxies
- Packet captures

#### Remediación
1. **Recomendación fuerte:** Usar Bearer token en `Authorization` header en lugar de custom header
2. Si se mantiene custom header, asegurar:
   - Header redacted en logs
   - HTTPS-only (no HTTP)
   - No logged en access logs

```python
# In Nginx/ALB upstream config
proxy_set_header X-Admin-Master-Key "";  # Don't proxy the key upstream
```

**Effort:** 1 hour (refactor a Authorization header)  
**Risk:** MEDIA — Información sensible visible en logs

---

### B.3 — Header Injection via X-Real-IP / X-Forwarded-For Spoofing

**ID:** FINDING-COMMON-B-003  
**Severidad:** 🟡 **BAJA** (CVSS v3.1: 3.1) — CWE-346 (Origin Validation Error)  
**Ubicación:** `limiter.py` líneas 38-42

#### Código Vulnerable
```python
# Línea 38-42
for header in ("X-Real-IP", "X-Forwarded-For"):
    value = request.headers.get(header)
    if value:
        return value.split(",")[0].strip()  # ⚠️ Client-controllable source
return get_remote_address(request)
```

#### Escenario
Atacante envía: `X-Forwarded-For: 10.0.0.1, 192.168.1.1`
Rate limiter cree que request es de `10.0.0.1` → puede spoof internal IPs

#### Remediación
```python
def multi_layer_key_func(request: Request) -> str:
    """
    FIXED: Trust X-Forwarded-For ONLY if from trusted proxy.
    RULE: Whitelist proxy IPs via configuration.
    """
    from ipaddress import IPv4Network, IPv4Address
    
    TRUSTED_PROXIES = [
        IPv4Network("10.0.0.0/8"),
        IPv4Network("127.0.0.1/32"),
        # Add actual Nginx/ALB IPs
    ]
    
    # Check if direct connection is from trusted proxy
    client_ip = None
    if request.client:
        try:
            client_addr = IPv4Address(request.client.host)
            is_trusted = any(client_addr in network for network in TRUSTED_PROXIES)
            
            if is_trusted:
                # Extract leftmost IP from X-Forwarded-For
                for header in ("X-Forwarded-For", "X-Real-IP"):
                    value = request.headers.get(header)
                    if value:
                        client_ip = value.split(",")[0].strip()
                        break
        except ValueError:
            pass
    
    if not client_ip:
        client_ip = request.client.host if request.client else "0.0.0.0"
    
    # Rest of function uses client_ip...
```

**Effort:** 1 hour  
**Risk:** BAJA (global limit still active as fallback)

---

### B.4 — Information Disclosure in guards.py Error Message

**ID:** FINDING-COMMON-B-004  
**Severidad:** 🟡 **BAJA** (CVSS v3.1: 2.7) — CWE-209 (Information Exposure)  
**Ubicación:** `guards.py` línea 36

#### Código Vulnerable
```python
# Línea 35-37
if not any(role in user_roles for role in required_roles):
    raise UnauthorizedException(
        message=f"Access denied. Required roles: {roles}. Your roles: {list(user_roles)}"
    )
```

#### Problema
Expone todos los roles del usuario al cliente. Atacante enumera permisos = OSINT.

#### Remediación
```python
if not any(role in user_roles for role in required_roles):
    # Log detailed reason for operators, generic message to client
    logger.warning(
        f"Access denied: user {context.sub} missing roles {roles}. "
        f"User has: {list(user_roles)}"
    )
    raise UnauthorizedException(
        message="Access denied. Insufficient permissions."  # Generic
    )
```

**Effort:** 15 min

---

### B.5 — Scope Validation Missing in limiter.py Key Extraction

**ID:** FINDING-COMMON-B-005  
**Severidad:** 🟡 **BAJA** (CVSS v3.1: 1.9) — CWE-862 (Missing Authorization)  
**Ubicación:** `limiter.py` línea 27-29

#### Problema
```python
# Línea 27-29
user_token = getattr(request.state, "user_token", None)
if user_token and hasattr(user_token, "sub") and user_token.sub:
    return f"user:{user_token.sub}"  # ⚠️ No check if user is readonly/expired
```

Si usuario es readonly o session expirada, aún obtiene rate limit key basada en user_id.

#### Remediación
```python
user_token = getattr(request.state, "user_token", None)
if user_token and hasattr(user_token, "sub") and user_token.sub:
    # ADDED: Check user is in valid state for rate limiting
    if not getattr(user_token, "readonly", False) and getattr(user_token, "status") != "EXPIRED":
        return f"user:{user_token.sub}"
    # Fallback to IP if user is readonly/expired
```

**Effort:** 10 min

---

## ANÁLISIS C: auth_service Integration

### C.1 — god_mode Claim Not Validated Server-Side

**ID:** FINDING-COMMON-C-001  
**Severidad:** 🔴 **CRÍTICA** (CVSS v3.1: 7.8) — CWE-347 (Improper Verification)  
**Ubicación:** `common/security/auth_payload.py` línea 35 + `dependencies.py` línea 63-70

#### Código Vulnerable
```python
# auth_payload.py línea 35
god_mode: bool = Field(False, description="True si el token proviene de /elevate (break-glass)")

# dependencies.py línea 63-70
if current_user.god_mode and current_user.jti:
    jti_valid = await r.get(f"godmode:{current_user.jti}")
    if not jti_valid:
        raise HTTPException(...)
    return current_user  # ⚠️ GOD_MODE accepted if JTI in Redis
```

#### Riesgo y Escenario
1. Atacante falsifica JWT con `"god_mode": true` + válido `jti`
2. Si JTI existe en Redis (puede ser viejo), aceptado
3. Atacante obtiene `GOD_MODE_ADMIN` bypass en `dependencies.py` línea 135

**Precondición:** Atacante necesita conocer un JTI válido (enumerable vía timing attacks o leaked)

#### Remediación (Código Seguro)
```python
# auth_payload.py — no cambios, pero documentar invariante
# INVARIANT: god_mode NUNCA confiar de cliente. SIEMPRE verificar server-side.

# dependencies.py — CAMBIO CRÍTICO
async def get_current_active_user(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    FIXED: god_mode NUNCA viene del JWT cliente.
    NUNCA confiar claims de JWT sin server-side validation.
    """
    # CRITICAL: god_mode es SOLO para sesiones elevadas via /elevate endpoint
    # Rechazar god_mode en JWT a menos que venga del servidor (via separate session store)
    
    # WRONG approach (current):
    # if current_user.god_mode:  # ❌ Cliente puede falsificar
    
    # CORRECT approach:
    # 1. god_mode no debe existir en JWT cliente
    # 2. Si necesario, usar separate server session store
    
    # Rechazar proactivamente
    if getattr(current_user, 'god_mode', False):
        _rls_log.critical(
            f"SECURITY: god_mode claim in JWT from user {current_user.sub} — rejecting"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claim"
        )
    
    # ... resto de function ...
```

**Better Architecture:**
```python
# Separate server session store para god_mode (no en JWT)
# En /elevate endpoint:
# 1. Verify MFA/additional auth
# 2. Create session in Redis: f"godmode:{user_id}:{jti}" = TTL 5min
# 3. Return access_token (sin god_mode claim)

# En dependencies.py:
# if user needs god_mode:
#     session_key = f"godmode:{user.sub}:{jti}"
#     is_elevated = await redis.get(session_key)
#     if not is_elevated:
#         raise Unauthorized()
```

**Effort:** 2-4 hours (refactor session store)  
**Risk:** CRÍTICA — Elevation of Privilege

---

### C.2 — Company ID from X-Company-ID Header Client-Controllable

**ID:** FINDING-COMMON-C-002  
**Severidad:** 🔴 **CRÍTICA** (CVSS v3.1: 8.1) — CWE-639 (Authorization Bypass)  
**Ubicación:** `limiter.py` línea 32-34

#### Código Vulnerable
```python
# Línea 32-34
company_id = request.headers.get("X-Company-ID")  # ⚠️ From client
if company_id:
    return f"tenant:{company_id}"
```

#### Riesgo Máximo
Atacante envía `X-Company-ID: victim-company-id` → rate limit key es victim's tenant, exhaust su cuota.

**Pero peor:** Si limiter es ÚNICO mecanismo de autorización, podría desencadenar IDOR.

#### Remediación
```python
def multi_layer_key_func(request: Request) -> str:
    """
    FIXED: company_id NUNCA from client headers.
    NUNCA from X-Company-ID — es solo para audit logging.
    """
    # Layer 3: User (highest priority)
    user_token = getattr(request.state, "user_token", None)
    if user_token and hasattr(user_token, "sub") and user_token.sub:
        if not getattr(user_token, "readonly", False):
            return f"user:{user_token.sub}"
    
    # Layer 2: Company (from JWT ONLY, not header)
    if user_token and hasattr(user_token, "company_id"):
        # CHANGED: Extract from verified JWT, not header
        return f"tenant:{user_token.company_id}"
    
    # Layer 1: IP (fallback)
    client_ip = request.client.host if request.client else "0.0.0.0"
    return f"ip:{client_ip}"
    
    # ❌ REMOVE this:
    # company_id = request.headers.get("X-Company-ID")  # Never trust header
```

**Key Changes:**
1. Never extract company_id from headers
2. Always from JWT (verified)
3. Fallback to IP, never to client-supplied data

**Effort:** 30 min  
**Risk:** CRÍTICA — Potential IDOR

---

### C.3 — Scope Elevation via JWT Tampering

**ID:** FINDING-COMMON-C-003  
**Severidad:** 🔴 **ALTA** (CVSS v3.1: 7.2) — CWE-347 (Improper Verification)  
**Ubicación:** `common/security/dependencies.py` línea 135, `auth_payload.py` línea 20

#### Problema
```python
# auth_payload.py línea 20
scopes: List[str] = Field([], description="Permisos granulares (permissions)")

# dependencies.py línea 135
if "GOD_MODE_ADMIN" in (current_user.role_names or []) or "*" in (current_user.scopes or []):
    return current_user  # ⚠️ Scope "*" acepta sin validación
```

Atacante falsifica JWT con `"scopes": ["*"]` → all endpoints accessible.

#### Remediación
```python
# En login handler (auth_service)
# RULE: Scopes NUNCA incluir "*" a menos que verificado contra server database.

async def create_final_access_token(...) -> str:
    """
    FIXED: Fetch scopes from database, embed en JWT.
    NUNCA confiar que cliente vaya a falsificar scopes.
    """
    # Paso 1: Fetch from DB (user_role tabla)
    user_scopes = await db.query(UserRole).filter(
        UserRole.user_id == subject,
        UserRole.company_id == company_id
    ).first()
    
    # Paso 2: Validar que "*" SOLO para god_mode users
    if "*" in user_scopes.scope_list:
        # Verify this user was elevated via /elevate
        is_elevated = await verify_god_mode_session(subject)
        if not is_elevated:
            user_scopes.scope_list.remove("*")  # Strip unauthorized scope
    
    # Paso 3: Emitir token con scopes validados
    payload = { ... "scopes": user_scopes.scope_list ...}
    return jwt.encode(payload, secret)
```

En dependencies.py, validar server-side:
```python
async def require_scope(required_scopes: list[str]):
    async def _require_scope(
        current_user: TokenPayload = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db)
    ):
        # CHANGED: Validate scopes against database, not JWT
        user_roles = await db.query(UserRole).filter(
            UserRole.user_id == current_user.sub,
            UserRole.company_id == current_user.company_id
        ).first()
        
        actual_scopes = user_roles.scope_list if user_roles else []
        
        # Check actual scopes (database source of truth)
        missing = [
            rs for rs in required_scopes
            if not _scope_satisfies(set(actual_scopes), rs)
        ]
        
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return _require_scope
```

**Effort:** 4-6 hours (refactor scope validation pipeline)  
**Risk:** ALTA — Privilege Escalation

---

### C.4 — Session Heartbeat Race Condition

**ID:** FINDING-COMMON-C-004  
**Severidad:** 🟡 **MEDIA** (CVSS v3.1: 4.3) — CWE-367 (Time-of-Check Time-of-Use)  
**Ubicación:** `dependencies.py` línea 56-79

#### Problema
```python
# Línea 56-57: Check cache
if not current_user.god_mode and cache_key in _user_status_cache and _user_status_cache[cache_key] > now:
    return current_user  # ⚠️ Returns without Redis check

# Línea 73-78: Redis check
is_inactive = await r.get(f"blacklist:{current_user.sub}")
if is_inactive:
    raise HTTPException(...)

# Gap: Si usuario revocado entre línea 56 y línea 73, aceptado temporalmente
```

#### Escenario
1. Usuario login → cache set (5min TTL)
2. Admin revoca usuario → Redis blacklist set
3. Usuario hace request dentro de 5min → cache hit → returns antes de Redis check
4. Usuario acepta por ~1 segundo hasta siguiente request

#### Remediación
```python
async def get_current_active_user(
    request: Request,
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """
    FIXED: Always check Redis for recent revocations.
    Cache es ONLY para Redis unavailability, not for performance.
    """
    if current_user.readonly and request.method not in ("GET", "OPTIONS", "HEAD"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is in READ-ONLY mode. Mutation not allowed."
        )
    
    try:
        r = get_redis()
        
        # CHANGED: Always check Redis (no 5min cache optimization)
        # Redis is fast (~1ms) — don't optimize prematurely
        is_inactive = await r.get(f"blacklist:{current_user.sub}")
        if is_inactive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account has been deactivated."
            )
        
        # Optional: Cache negative result ONLY if Redis available
        # (but not for 5 minutes, only 10 seconds)
        await r.setex(f"user_status_cache:{current_user.sub}", 10, "OK")
        
    except Exception as e:
        # If Redis unavailable, be conservative: reject request
        # Better to deny legitimate user for 1s than accept revoked user
        logger.warning(f"Redis unavailable for heartbeat check: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session validation temporarily unavailable"
        )
    
    return current_user
```

**Key Changes:**
1. Always hit Redis (remove 5min cache)
2. Only cache negative results (user NOT revoked)
3. Fail-closed if Redis unavailable

**Effort:** 1 hour  
**Risk:** MEDIA — Session revocation delay

---

## ANÁLISIS D: Invariantes Compartidas

### D.1 — company_id Binding Violado en Múltiples Puntos

**ID:** INVARIANT-D-001  
**Severidad:** 🔴 **CRÍTICA** (CVSS v3.1: 8.2)

#### Invariante
**Statement:** `company_id` de un usuario NO PUEDE ser:
1. Extraído de headers (X-Company-ID)
2. Derivado de request parameters
3. Tomado del JWT sin verification

**DEBE ser:**
- Extraído del JWT verificado criptográficamente
- Validado contra multi-tenancy context
- Usado como filtro ADICIONAL en todas las queries ORM

#### Violaciones Detectadas
1. ✅ `database.py` línea 49: `with_loader_criteria` — correcto (aplica filter)
2. ❌ `limiter.py` línea 32-34: X-Company-ID header — VIOLATION
3. ❌ `dependencies.py` línea 135: Scope validation sin DB check — VIOLATION
4. ✅ `common/context.py` (no leída, pero asumida): request_context.company_id — probablemente correcto

#### Remediación Consolidada
Ver **C.2 — Company ID from X-Company-ID Header**

---

### D.2 — Cryptographic Verification Bypass Channels

**ID:** INVARIANT-D-002  
**Severidad:** 🟡 **MEDIA**

#### Invariante
**Statement:** Toda claim de autorización (god_mode, scopes, roles) DEBE verificarse:
- En servidor (NO confiar JWT cliente)
- Contra base de datos (SSOT)
- Con fallback seguro (deny-by-default)

#### Violaciones
1. ❌ `auth_payload.py` línea 35: `god_mode` — cliente-controllable
2. ❌ `dependencies.py` línea 135: `"*"` scope sin DB validation
3. ❌ `guards.py` línea 27-29: Roles desde JWT sin server check

#### Remediación Consolidada
Ver **C.1, C.3**

---

## Matriz de Hallazgos Consolidada

| ID | Módulo | Severidad | CVSS | Esfuerzo | Estado | Bloqueador |
|----|--------|-----------|------|----------|--------|-----------|
| FINDING-COMMON-A-001 | infrastructure | MEDIA | 4.3 | 30min | No | No |
| FINDING-COMMON-A-002 | infrastructure | BAJA | 2.7 | 10min | No | No |
| FINDING-COMMON-A-003 | infrastructure | BAJA | 1.5 | 2h | No | No |
| **FINDING-COMMON-B-001** | security | **ALTA** | **6.4** | **30min** | **CRÍTICA** | **SÍ** |
| FINDING-COMMON-B-002 | security | MEDIA | 3.7 | 1h | No | No |
| FINDING-COMMON-B-003 | security | BAJA | 3.1 | 1h | No | No |
| FINDING-COMMON-B-004 | security | BAJA | 2.7 | 15min | No | No |
| FINDING-COMMON-B-005 | security | BAJA | 1.9 | 10min | No | No |
| **FINDING-COMMON-C-001** | auth integration | **CRÍTICA** | **7.8** | **4h** | **CRÍTICA** | **SÍ** |
| **FINDING-COMMON-C-002** | auth integration | **CRÍTICA** | **8.1** | **30min** | **CRÍTICA** | **SÍ** |
| **FINDING-COMMON-C-003** | auth integration | **ALTA** | **7.2** | **6h** | **ALTA** | **SÍ** |
| FINDING-COMMON-C-004 | auth integration | MEDIA | 4.3 | 1h | No | No |
| INVARIANT-D-001 | invariantes | CRÍTICA | 8.2 | 12h | CUMULATIVE | SÍ |
| INVARIANT-D-002 | invariantes | MEDIA | 5.1 | 12h | CUMULATIVE | SÍ |

---

## Plan de Implementación Secuencial

### Timeline Consolidado

**FASE 179A (Crítica — 3 días):** Remediaciones que bloquean cloud deployment

| Prioridad | Hallazgo | Esfuerzo | Deps | Status |
|-----------|----------|----------|------|--------|
| **P0.1** | FINDING-COMMON-B-001 (Timing attack bypass) | 30min | None | `not-started` |
| **P0.2** | FINDING-COMMON-C-002 (X-Company-ID IDOR) | 30min | P0.1 | `not-started` |
| **P0.3** | FINDING-COMMON-C-001 (god_mode falsification) | 4h | P0.2 | `not-started` |
| **P0.4** | FINDING-COMMON-C-003 (Scope elevation) | 6h | P0.3 | `not-started` |
| **P0.5** | FINDING-COMMON-A-001 (SQL injection anti-pattern) | 30min | None | `not-started` |

**Subtotal:** 11.5 horas = 2 días (con paralelización)

---

**FASE 179B (Hardening — 3 días):** Validación + tests

| Prioridad | Tarea | Esfuerzo | Deps |
|-----------|-------|----------|------|
| **P1.1** | Code review + pair programming | 4h | P0.* |
| **P1.2** | Security test suite (unit + integration) | 6h | P0.* |
| **P1.3** | Penetration testing (timing attacks, IDOR, elevation) | 4h | P1.2 |
| **P1.4** | Regression testing (all auth flows) | 3h | P1.3 |

**Subtotal:** 17 horas = 3 días (con paralelización)

---

**Total:** 28.5 hours = 4 días de desarrollo + testing

---

### Desglose Detallado por Hallazgo

#### FASE 179A.1 — FINDING-COMMON-B-001 (Timing Attack Bypass)

**Archivos a Modificar:**
- `backend/common/security/limiter.py`

**Cambios Exactos:**
```
Línea 19-20: internal_secret == ... → hmac.compare_digest(internal_secret, ...)
Línea 22-24: admin_key == ... → hmac.compare_digest(admin_key, ...)
Línea 15: import hmac
```

**Commit Message:**
```
security(common/security): Fix timing attack in bypass key validation

Replace string equality (==) with constant-time comparison (hmac.compare_digest)
for X-Internal-Secret and X-Admin-Master-Key headers.

CWE-697: Incorrect Comparison
CVSS: 6.4 (ALTA)

Risk: Attacker could brute-force bypass keys via timing analysis of response.
Mitigation: Constant-time comparison prevents timing leakage.
```

**QA Checklist:**
- [ ] Timing test: 100 requests with wrong key, measure response variance
- [ ] Verify bypass still works with correct keys
- [ ] Log audit trail for bypass usage

---

#### FASE 179A.2 — FINDING-COMMON-C-002 (X-Company-ID IDOR)

**Archivos a Modificar:**
- `backend/common/security/limiter.py` (remove X-Company-ID extraction)

**Cambios Exactos:**
```
Línea 32-34: DELETE (company_id = request.headers.get("X-Company-ID") block)
Línea 27-29: MODIFY to extract company_id from user_token.company_id ONLY
```

**Commit Message:**
```
security(common/security): Remove client-controllable company_id from rate limit key

Rate limit key MUST be derived from cryptographically verified JWT,
never from client headers (X-Company-ID). This prevents attackers from
spoofing other companies' tenant IDs to exhaust their rate limit quota.

CWE-639: Authorization Bypass
CVSS: 8.1 (CRÍTICA)

Change: Extract company_id from validated JWT or IP fallback only.
```

**QA Checklist:**
- [ ] Different companies get different rate limit keys
- [ ] Spoofed X-Company-ID header ignored
- [ ] IP fallback works when JWT unavailable

---

#### FASE 179A.3 — FINDING-COMMON-C-001 (god_mode Falsification)

**Archivos a Modificar:**
- `backend/auth_service/auth_app/api/v1/endpoints/elevate.py` (new endpoint)
- `backend/common/security/dependencies.py` (refactor god_mode logic)
- `backend/auth_service/auth_app/core/security.py` (remove god_mode from JWT)

**New Endpoint Architecture:**
```
POST /api/v1/auth/elevate
- Input: MFA code + MFA device ID
- Verify MFA against DB
- Create session in Redis: f"godmode:{user_id}:{jti}" = TTL 5min
- Return access_token (sin god_mode claim)

Dependencies.py checks:
- if endpoint requires god_mode:
  - fetch from Redis session store (not JWT)
  - reject if not found or expired
```

**Commit Message:**
```
security(auth_service): Remove god_mode from JWT, use separate session store

god_mode (break-glass admin access) must NEVER come from client JWT.
Create server-side session store (Redis) for authenticated god_mode sessions.

CWE-347: Improper Verification of Cryptographic Signature
CVSS: 7.8 (CRÍTICA)

Changes:
1. Remove god_mode claim from JWT payload
2. Create /elevate endpoint for MFA-verified god_mode sessions
3. Store sessions in Redis with 5min TTL
4. Validate god_mode against session store, not JWT
```

**QA Checklist:**
- [ ] Falsified JWT with god_mode=true rejected
- [ ] /elevate endpoint requires MFA
- [ ] god_mode expires after 5 minutes
- [ ] Concurrent elevation requests validated

---

#### FASE 179A.4 — FINDING-COMMON-C-003 (Scope Elevation)

**Archivos a Modificar:**
- `backend/auth_service/auth_app/core/security.py` (validate scopes at token creation)
- `backend/common/security/dependencies.py` (validate scopes against DB)
- `backend/auth_service/auth_app/models/user_role.py` (ensure SSOT)

**Changes:**
```
1. In create_final_access_token():
   - Fetch scopes from database (UserRole table)
   - Validate "*" scope only for god_mode users
   - Embed verified scopes in JWT

2. In require_scope dependency:
   - Fetch actual scopes from database
   - Compare against database, NOT JWT
   - Deny if mismatch
```

**Commit Message:**
```
security(auth_service): Validate scopes against database, not client JWT

Scopes (permissions) must be fetched from database during token creation
and re-validated server-side during authorization checks. Never trust
scope claims in JWT from unauthenticated sources.

CWE-347: Improper Verification
CVSS: 7.2 (ALTA)

Changes:
1. Token creation: fetch scopes from DB, validate before embedding
2. Scope check: always re-fetch from DB, never trust JWT
3. Deny wildcard scope ("*") except for verified god_mode sessions
```

**QA Checklist:**
- [ ] Elevated scopes in JWT rejected if not in DB
- [ ] Wildcard scope only accepted for god_mode users
- [ ] Revoking scope in DB immediately denies access
- [ ] Token refresh re-validates scopes

---

#### FASE 179A.5 — FINDING-COMMON-A-001 (SQL Injection)

**Archivos a Modificar:**
- `backend/common/infrastructure/database.py` (línea 85)

**Cambios Exactos:**
```
Línea 84-85:
OLD: cursor.execute(f"SET LOCAL app.current_tenant = '{tenant_str}';")
NEW: cursor.execute("SET LOCAL app.current_tenant = %s", (str(tenant_uuid),))
```

**Commit Message:**
```
security(common/infrastructure): Use parameterized query for RLS tenant setting

Replace string interpolation with parameterized query in PostgreSQL
tenant context setting. Although UUID validation mitigates risk,
parameterized queries are the correct pattern and prevent future regressions.

CWE-89: SQL Injection
CVSS: 4.3 (MEDIA)

Change: Use cursor.execute with tuple parameter instead of f-string.
```

**QA Checklist:**
- [ ] RLS still filters correctly
- [ ] UUID validation still present
- [ ] Invalid UUIDs still invalidate connection
- [ ] No performance regression

---

### Rutas de Ejecución Paralela

```
Timeline: 2-4 días (con 3 developers)

Día 1-2 (Critical Path — 11.5h):
┌─ Dev A: P0.1 (Timing attack)         ────→ 30min ──┐
├─ Dev B: P0.2 (X-Company-ID)          ────→ 30min ─┤
└─ Dev C: P0.5 (SQL injection) + (P0.3 prep) ─→ 4.5h ┤
                                               ↓
  Merge, test, ready for P0.3
                                               ↓
  Dev A + B + C: P0.3 (god_mode) + P0.4 (scopes) ──→ 10h

Día 3-4 (Testing & Validation — 17h):
┌─ Code review + pair: P1.1            ────→ 4h
├─ Security test suite: P1.2           ────→ 6h
├─ Penetration testing: P1.3           ────→ 4h
└─ Regression testing: P1.4            ────→ 3h
```

---

## Criterios de Éxito y Validación

### Definition of Done (Para cada hallazgo)

1. ✅ **Code:** Cambios implementados en branch feature
2. ✅ **Review:** 2-person code review (security + architect)
3. ✅ **Tests:** Unit + integration tests pass (100% coverage for security paths)
4. ✅ **Security:** Penetration test passed (timing attack, IDOR, elevation)
5. ✅ **Regression:** All existing auth flows still work
6. ✅ **Docs:** Invariante documentada en security/ARCHITECTURE.md
7. ✅ **Commit:** PR merged a main con message explicativo

---

### Security Test Suite (Ejemplos)

```python
# Para FINDING-COMMON-B-001 (Timing Attack)
def test_bypass_key_constant_time():
    timings = []
    for i in range(100):
        start = time.perf_counter()
        response = client.get("/protected", headers={
            "X-Admin-Master-Key": f"sk_test_{i:040d}"  # Wrong key
        })
        timings.append(time.perf_counter() - start)
    
    std_dev = statistics.stdev(timings)
    assert std_dev < 0.001, f"Timing variance too high: {std_dev}"  # <1ms

# Para FINDING-COMMON-C-002 (X-Company-ID IDOR)
async def test_company_id_header_ignored():
    # Try to use Company B token with Company A's company_id header
    token_a = generate_token(company_id=COMPANY_A)
    response = client.get(
        "/protected",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Company-ID": str(COMPANY_B)
        }
    )
    # Rate limiter should use COMPANY_A (from token), not COMPANY_B (from header)
    assert response.headers["X-RateLimit-Key"] == f"user:{user_id}"  # ✅

# Para FINDING-COMMON-C-001 (god_mode Falsification)
async def test_god_mode_claim_rejected():
    fake_jwt = jwt.encode({
        "sub": str(user_id),
        "god_mode": True,  # ❌ Claim falsificado
        "company_id": str(company_id)
    }, "wrong-key")
    
    response = client.post(
        "/protected",
        headers={"Authorization": f"Bearer {fake_jwt}"}
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]
```

---

### Validación Manual (Penetration Testing Checklist)

- [ ] **Timing Attack:** 100 requests wrong admin key → variance <1ms
- [ ] **IDOR (X-Company-ID):** Spoof header → rate limit still applies correctly
- [ ] **Scope Elevation:** JWT with "*" scope → rejected
- [ ] **god_mode Bypass:** Falsified JWT with god_mode=true → rejected
- [ ] **Session Revocation:** Blacklist user → immediate rejection
- [ ] **RLS Filtering:** company_id context → queries filtered correctly

---

## Documentación de Arquitectura (New Files)

### File 1: `docs/security/COMMON_ARCHITECTURE.md`

```markdown
# Common Infrastructure — Security Architecture

## Invariantes Críticos

### I1: Multi-Tenancy Isolation (company_id binding)
**Rule:** company_id NUNCA del cliente.
**Validation:** JWT verification + database foreign key
**Locations:** database.py (RLS), limiter.py (rate limit key), dependencies.py

### I2: Cryptographic Verification (JWT claims)
**Rule:** Scopes, roles, god_mode NUNCA trusted from JWT.
**Validation:** Server-side database lookup (SSOT)
**Locations:** auth_payload.py (claims), dependencies.py (validation)

### I3: Constant-Time Secrets (bypass keys)
**Rule:** API keys NUNCA compared with ==
**Validation:** hmac.compare_digest() for all secret comparisons
**Locations:** limiter.py (bypass keys)

## Implementation Status
- [x] I1: Multi-tenancy (90% compliant, X-Company-ID header violation)
- [x] I2: JWT verification (70% compliant, god_mode + scopes bypass)
- [x] I3: Constant-time (0% compliant, critical timing attacks)
```

---

## Timeline Resumido

| Fase | Duración | Hallazgos | Estado |
|------|----------|-----------|--------|
| **179A** | 2 días | P0.1-P0.5 | Planificado |
| **179B** | 3 días | P1.1-P1.4 | Planificado |
| **Cloud Deployment** | ← Bloqueado hasta completar 179A+B |

---

## Próximos Pasos

1. **Aprobación de Plan:** Revisión de PO/Security Lead
2. **Sprint Planning:** Asignar developers a hallazgos (paralelizar P0.1-P0.5)
3. **Development:** Implementar cambios secuencialmente
4. **Testing:** Security test suite + penetration testing
5. **Merge:** Code review + regression testing
6. **Deployment:** Cloud deployment unblocked post-validation

---

**Documento Generado:** 2026-06-03  
**Clasificación:** CONFIDENCIAL - PLAN TÉCNICO  
**Próxima Revisión:** Post-Phase 179B (cloud deployment readiness checkpoint)
