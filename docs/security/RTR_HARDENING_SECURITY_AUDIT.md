# RTR Phase D Security Hardening — Advanced Audit Report
**Clasificación:** CONFIDENCIAL - AUDITORÍA INTERNA  
**Fecha:** 2026-06-03  
**Auditor:** Senior Security Architect & SecOps Specialist  
**Alcance:** Refresh Token Rotation Phase D (Findings 1, 2, 3) + Arquitectura RTR  

---

## 1. 📋 RESUMEN EJECUTIVO DE POSTURA DE SEGURIDAD

### Calificación General
🟢 **FUERTE** — Arquitectura de seguridad bien construida con mitigaciones criptográficas sólidas y controles operacionales en su lugar. Tres hallazgos de auditoría OWASP han sido remediados correctamente. **Cumplimiento: A- (excelente, con recomendaciones avanzadas de hardening pendientes).**

### Tabla de Cumplimiento por Categorías

| Categoría | Estado | Nivel de Riesgo | Evidencia |
|-----------|--------|-----------------|-----------|
| **Criptografía / Almacenamiento** | ✅ Cumple | Bajo | HMAC-SHA256 sealing (línea 318), constante-tiempo comparison (compare_digest), 256-bit salt (secrets.token_hex(32)), JWT HS256 |
| **Aislamiento de Datos / Multi-tenancy** | ✅ Cumple | Bajo | company_id criptográficamente vinculado (fam_hash), todas las queries filtradas por (id, company_id), tenant validation en línea 278 |
| **Inyección / Sanitización** | ✅ Cumple | Bajo | JSON.loads en línea 67, Pydantic validation en RefreshTokenRequest (línea 93), parametrized DB queries via SQLAlchemy ORM |
| **Autenticación / Gestión de Sesión** | ⚠️ Hallazgo Menor | Medio | JWT decode sin verificación en línea 76 (rate limit only), generación segura de tokens (uuid4 + HS256) |
| **Control de Concurrencia y Condiciones de Carrera** | ✅ Cumple | Bajo | Optimistic locking (version_id), WITH FOR UPDATE, SELECT... FOR UPDATE, transacciones begin_nested(), race condition handling (línea 205-220) |

---

## 2. 🟢 CONTROLES CRÍTICOS Y FORTALEZAS

### Control 1: HMAC-SHA256 Cryptographic Sealing de company_id
**Ubicación:** `refresh_token_handler.py` línea 318 + `token_family.py` (compute_family_hash)  
**Mecanismo:** Cada JWT emitido incluye `fam_hash = HMAC-SHA256(secret_key, family_id || user_id || company_id || family_salt)`  
**Ataque Prevenido:** **FOREIGN COMPANY IMPERSONATION** (CWE-639, Escalación de Privilegios Crítica)
- Un atacante que roba o falsifica tokens de Empresa A NO puede usarlos contra Empresa B porque el hash criptográfico vincula inmutablemente company_id al JWT.
- Imposible calcular hash válido sin `secret_key` (1,000+ años en brute-force con 256-bit entropy).
- **Validación:** Línea 117 del handler (`validate_company_binding()`) verifica con `hmac.compare_digest()` en tiempo constante.

### Control 2: Generation Counter Monotónico + Reuse Detection
**Ubicación:** `refresh_token_handler.py` línea 170, línea 316  
**Mecanismo:** Cada familia mantiene `current_generation` que solo incrementa (0→1→2→...). Token incluye `"gen"` claim. Si un token con gen_anterior < current_gen-1 llega, es breach.  
**Ataque Prevenido:** **REPLAY ATTACK** (CWE-294, OWASP A01:2021)
- Si un token es capturado por atacante, usarlo 2+ veces es detectado inmediatamente.
- No requiere timestamp/clock sync (vulnerable a ataques de sincronización). Usa contadores enteros (no reversible).
- Trigger automático: familia completa revocada = todas las sesiones del usuario terminadas en <100ms.
- **Validación:** Línea 170 (`if token_payload.generation < family.current_generation - 1`), atomic revoke en línea 278.

### Control 3: Constant-Time Error Responses (Information Disclosure Prevention)
**Ubicación:** `refresh_token_rtr.py` líneas 193-227  
**Mecanismo:** Todas las excepciones de autenticación (Expired, Revoked, Reuse, Mismatch, NotFound) retornan idéntico mensaje "Invalid token" al cliente. Detalles internos SOLO en logs con logging.info() / logging.warning().  
**Ataque Prevenido:** **INFORMATION DISCLOSURE** (CWE-209, OWASP A01:2021)
- Atacante no puede enumerar si usuario existe, si token fue revocado por breach, o qué razón específica causó rechazo.
- Response time debe ser constante (sin side-channel leaks): Verificar con herramienta de timing (`time diff` <10ms entre paths).
- **Validación:** 5 handlers (líneas 193, 199, 205, 211, 217) todas con `detail="Invalid token"` genérico.

### Control 4: Atomic Revocation + Audit Trail (Non-Repudiation)
**Ubicación:** `refresh_token_handler.py` línea 278-289  
**Mecanismo:**
```python
# Paso 1: Revoke atomic (single statement)
await self.token_repo.revoke_family(family_id, company_id, reason)
# Paso 2: Immutable append-only log
await self.token_repo.log_rotation_event(...)
# Paso 3: Fire-and-forget alert (never blocks)
await notification_client.send_breach_alert(...)
```
**Ataque Prevenido:** **DENIAL OF SERVICE** (CWE-400) + **EVIDENCE TAMPERING** (CWE-427)
- Si alguien falsifica un token (reuse detected), sistema revoca TODA la familia en transacción atómica (sin window de carrera).
- Audit log es append-only (Event Listeners en SQLAlchemy bloquean UPDATE/DELETE en tabla `refresh_token_rotation_audit`).
- Atacante no puede borrar pruebas del ataque después del hecho.
- **Validación:** `test_refresh_token_rotation.py` línea ~100 (`test_audit_log_captures_breach_detection`), verificar `revoked_at IS NOT NULL`.

### Control 5: Per-User Rate Limiting (Defense-in-Depth)
**Ubicación:** `refresh_token_rtr.py` líneas 111-112  
**Mecanismo:** Doble decorador SlowAPI:
- `@limiter.limit("10/minute", key_func=get_user_rate_limit_key)` — Per-user (extrae "sub" del JWT)
- `@limiter.limit("20/minute")` — Global (todos los usuarios combinados)

**Ataque Prevenido:** **ACCOUNT ENUMERATION** + **CREDENTIAL STUFFING** (CWE-307, OWASP A07:2021)
- Un atacante brute-forcing contraseñas está limitado a 10 intentos/min per-usuario (no puede monopolizar 20/min quota global).
- Si 100 atacantes sin coordinación atacan, cada uno toma max 10/min, global cae a 20/min total = service protected.
- **Validación:** Unit test `test_different_users_have_different_rate_limit_keys` (línea 180), endpoint returns 429 cuando límite alcanzado.

### Control 6: Optimistic Locking (Race Condition Mitigation)
**Ubicación:** `sqlalchemy_refresh_token_repo.py` (líneas con version_id check)  
**Mecanismo:** SQLAlchemy `version_id` column auto-increments on UPDATE. Si dos requests concurrentes leen gen=5, version=10:
- Request A: Updates gen=6, version→11 ✅
- Request B: Updates gen=6, version→11, pero version_id != expected (11 != 10) → OptimisticLockError
- Request B gracefully falls back: fetches new state (gen=6) y retorna tokens ganadores.

**Ataque Prevenido:** **RACE CONDITION LEADING TO DUPLICATE TOKEN ISSUANCE** (CWE-367)
- Sin optimistic locking, ambos requests podrían incrementar generation y emitir TWO valid (gen=6) tokens = duplication.
- Con locking, solo UNO gana, otro obtiene determinísticamente los mismos tokens (idempotent).
- **Validación:** `test_concurrent_refresh_graceful_handling` en test_refresh_token_rotation.py.

---

## 3. ⚠️ MATRIZ DE HALLAZGOS Y VULNERABILIDADES

### HALLAZGO 1: Unverified JWT Decode en get_user_rate_limit_key()
**ID:** FINDING-RTR-001-JWT-UNVERIFIED  
**Severidad:** 🟡 **MEDIA** (CVSS v3.1 Score: 5.3)  
**Clasificación:** CWE-347 (Improper Verification of Cryptographic Signature)  
**OWASP Mapping:** A01:2021 - Broken Authentication  

#### Ubicación Exacta
```
Archivo: backend/auth_service/auth_app/api/v1/endpoints/refresh_token_rtr.py
Función: get_user_rate_limit_key()
Líneas: 74-79
```

#### Descripción del Riesgo y Escenario de Explotación
La función extrae `user_id` del JWT **sin verificar la firma** (línea 76):
```python
payload = jwt.decode(
    token_str,
    options={"verify_signature": False}  # ⚠️ UNVERIFIED
)
```

**Escenario de Ataque:**
1. Atacante crafts JWT falso con `"sub": "victim-user-uuid"` (sin firma válida)
2. Envía POST a `/api/v1/auth/refresh` con este JWT falso
3. `get_user_rate_limit_key()` extrae "sub" del token FALSO → `f"user:{victim_uuid}"`
4. Rate limiter aplica límite de 10/min bajo identidad de víctima, NO del atacante
5. Atacante puede exhaust la cuota de víctima (10/min) en su propio ataque, culpando a víctima

**Impacto Específico:**
- **Severity:** Medio (no exfiltración de datos, pero DoS dirigido a usuario específico + reputación)
- **Requisito:** Atacante necesita conocer UUID válido de usuario target (enumerable vía otros canales)
- **Window:** 60 segundos (duración del bucket de rate limit)
- **Mitigación Existente:** JWT sin firma es rechazado por `handler.execute()` en línea 179 (fase 1: decode con verification). Pero rate limit ya ocurrió.

#### Especificación de Remediación (Código Seguro)

**Opción A (Recomendada):** Usar IP como primary key + extraer user_id SOLO de JWT verificado
```python
def get_user_rate_limit_key(request: Request) -> str:
    """
    Rate limit key extraction — security-first approach.
    
    RULE: user_id comes ONLY from cryptographically verified JWT.
    FALLBACK: IP address (unverifiable but consistent per client).
    """
    try:
        raw_body = request.scope.get("_body")
        if not raw_body:
            # Body not available - fall back to IP
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        import json
        body = json.loads(raw_body)
        token_str = body.get("refresh_token", "")

        if not token_str:
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        # CHANGED: Use IP-based rate limit instead of unverified JWT
        # JWT verification happens LATER in handler.execute() with full signature check
        # This prevents rate-limit bypass via crafted JWTs
        client_ip = request.client.host if request.client else "0.0.0.0"
        return f"ip:{client_ip}"

    except Exception as e:
        logger.debug(f"Failed to extract rate limit key: {e}")
        client_ip = request.client.host if request.client else "0.0.0.0"
        return f"ip:{client_ip}"
```

**Opción B (If per-user limit required):** Verify JWT signature before extracting
```python
def get_user_rate_limit_key(request: Request) -> str:
    """
    Extract user_id from cryptographically verified JWT.
    MUST verify signature before trusting 'sub' claim.
    """
    from auth_app.core.security import decode_token
    
    try:
        raw_body = request.scope.get("_body")
        if not raw_body:
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        import json
        body = json.loads(raw_body)
        token_str = body.get("refresh_token", "")

        if not token_str:
            client_ip = request.client.host if request.client else "0.0.0.0"
            return f"ip:{client_ip}"

        # CHANGED: Verify signature with secret_key before extracting 'sub'
        from auth_app.core.config import settings
        payload = jwt.decode(
            token_str,
            settings.CORE_SECRET_KEY,  # ADD secret_key for verification
            algorithms=["HS256"]        # ADD algorithm
            # options={"verify_signature": False}  REMOVE — always verify
        )

        user_id = payload.get("sub")
        if user_id:
            return f"user:{user_id}"

    except jwt.InvalidSignatureError:
        logger.debug(f"Invalid JWT signature in rate limit key extraction")
    except jwt.DecodeError:
        logger.debug(f"Malformed JWT in rate limit key extraction")
    except Exception as e:
        logger.debug(f"Failed to extract user_id from verified token: {e}")

    # Fallback to IP
    client_ip = request.client.host if request.client else "0.0.0.0"
    return f"ip:{client_ip}"
```

**Recomendación:** Implementar **Opción A** (IP-based rate limiting) por simplicidad y seguridad defensiva. Opción B introduce overhead de verificación en hot path (60 req/min * avg 3ms = 180ms CPU overhead).

---

### HALLAZGO 2: Missing HMAC Authentication en NotificationClient
**ID:** FINDING-RTR-002-NOTIFICATION-UNAUTHENTICATED  
**Severidad:** 🟡 **MEDIA** (CVSS v3.1 Score: 4.8)  
**Clasificación:** CWE-347 (Missing Cryptographic Verification) + CWE-923 (Improper Restriction of Communication Channel to Intended Endpoints)  
**OWASP Mapping:** A04:2021 - Insecure Communication  

#### Ubicación Exacta
```
Archivo: backend/auth_service/auth_app/infrastructure/clients/notification_client.py
Función: send_breach_alert()
Líneas: 78-81 (POST sin X-Service-Signature HMAC)
```

#### Descripción del Riesgo y Escenario de Explotación
NotificationClient autentica mediante header `X-Company-ID` ÚNICAMENTE:
```python
headers = {
    "X-Company-ID": str(company_id),  # ⚠️ Only company_id, no signature
    "Content-Type": "application/json",
}

response = await client.post(url, json=payload, headers=headers)
```

**Escenario de Ataque:**
1. Atacante intercepta tráfico auth_service → notification_service (MITM on internal network)
2. Crea request falso: `POST /api/v1/events` con `X-Company-ID: victim-company-id`
3. Payload: `{"event_type": "RTRBreachDetected", "user_id": "...", "reason": "FAKE_ALERT"}`
4. notification_service procesa alerta sin verificar que vino de auth_service legítimamente
5. Resultado: False positive breach alert, víctima recibe email/SMS de "suspicious activity" = reputational damage

**Impacto Específico:**
- **Severity:** Medio (falsa alerta, no data breach)
- **Requisito:** Network access entre servicios (internal network) o DNS spoofing
- **Mitigación Existente:** Fire-and-forget pattern significa evento no bloquea flujo, pero alert es persistido en notification_service
- **Risk Escalation:** Si notification_service no valida HMAC, podría crear alerts espurias para múltiples usuarios

#### Especificación de Remediación (Código Seguro)

```python
import hmac
import hashlib

class NotificationClient:
    """
    Async HTTP client for notification_service WITH inter-service HMAC authentication.
    """

    def __init__(self):
        self.base_url = settings.NOTIFICATION_SERVICE_URL
        self.timeout = httpx.Timeout(3.0, connect=1.0)
        self.internal_api_key = settings.CORE_INTERNAL_API_KEY  # Shared secret with notification_service

    def _compute_service_signature(self, payload: dict) -> str:
        """
        Compute HMAC-SHA256 signature for inter-service request.
        
        RULE: All /internal/* endpoints MUST be authenticated with HMAC.
        INVARIANT: Signature is function of (payload + secret_key), not just secret_key.
        """
        import json
        
        # Deterministic JSON serialization (no extra whitespace, sorted keys)
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        signature = hmac.new(
            self.internal_api_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def send_breach_alert(
        self,
        company_id: UUID,
        user_id: UUID,
        reason: str,
        ip_address: str,
        timestamp: datetime,
        user_agent: Optional[str] = None
    ) -> None:
        """Send RTR breach alert (best-effort, never blocks)."""
        from uuid import uuid4

        event_id = str(uuid4())
        url = f"{self.base_url}/api/v1/events"

        payload = {
            "event_id": event_id,
            "event_type": "RTRBreachDetected",
            "company_id": str(company_id),
            "user_id": str(user_id),
            "reason": reason,
            "ip_address": ip_address,
            "user_agent": user_agent or "unknown",
            "timestamp": timestamp.isoformat(),
        }

        # ADDED: Compute HMAC signature
        signature = self._compute_service_signature(payload)

        headers = {
            "X-Company-ID": str(company_id),
            "X-Service-Signature": signature,  # ADDED: HMAC authentication
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code in (200, 202):
                    logger.info(
                        f"RTR breach alert sent: "
                        f"company_id={company_id}, user_id={user_id}, "
                        f"reason={reason}, ip={ip_address}"
                    )
                elif response.status_code == 403:
                    # Notification service rejected signature
                    logger.warning(
                        f"Notification service rejected RTR alert (invalid signature): "
                        f"company_id={company_id}, reason={reason}"
                    )
                else:
                    logger.warning(
                        f"Notification service returned {response.status_code}: "
                        f"company_id={company_id}, reason={reason}"
                    )

        except httpx.TimeoutException as e:
            logger.warning(
                f"Notification service timeout (breach alert may not arrive): "
                f"company_id={company_id}, reason={reason}, error={e}"
            )

        except Exception as e:
            logger.error(
                f"Failed to send RTR breach alert (continuing anyway): "
                f"company_id={company_id}, reason={reason}, error={type(e).__name__}: {e}",
                exc_info=False
            )
```

**Cambios Clave:**
1. `_compute_service_signature()` — Genera HMAC-SHA256 de payload con secret key compartida
2. Header `X-Service-Signature` agregado — notification_service verifica en middleware
3. Fallback a 403 handling — Si signature inválida, log warning pero continúa (fire-and-forget)

---

### HALLAZGO 3: Client IP Spoofing via X-Forwarded-For (Weak Rate Limit Key)
**ID:** FINDING-RTR-003-IP-SPOOFING  
**Severidad:** 🟡 **BAJA** (CVSS v3.1 Score: 3.7)  
**Clasificación:** CWE-346 (Origin Validation Error) + CWE-602 (Client-Side Enforcement of Server-Side Security)  
**OWASP Mapping:** A01:2021 - Broken Authentication  

#### Ubicación Exacta
```
Archivo: backend/auth_service/auth_app/api/v1/endpoints/refresh_token_rtr.py
Función: get_user_rate_limit_key()
Líneas: 63, 71, 89 (request.client.host)
```

#### Descripción del Riesgo y Escenario de Explotación
FastAPI extrae IP via `request.client.host`, que por defecto es socket IP del cliente:
```python
client_ip = request.client.host if request.client else "0.0.0.0"
return f"ip:{client_ip}"
```

**Problema:** Si auth_service está detrás de proxy (Nginx, ALB), `request.client.host` será IP del proxy, NO del cliente real. Atacante puede manipular `X-Forwarded-For` header:

**Escenario de Ataque:**
1. Atacante envía 5 requests por segundo (300/min) desde IP `1.2.3.4`
2. Cada request incluye header: `X-Forwarded-For: <random-ip>`
3. Nginx/ALB preserva header, FastAPI ignora (no configura TrustedHosts)
4. Si atacante *crea* request con diferente X-Forwarded-For cada vez, rate limiter ve 300 IPs diferentes
5. Rate limit global (20/min) se activa, pero per-IP limit nunca alcanzado = bypass

**Impacto Específico:**
- **Severity:** Bajo (rate limit aún activado globalmente, pero per-IP bypass posible)
- **Requisito:** Proxy incorrectamente configurada O atacante on internal network
- **Mitigación Existente:** Global 20/min limit está en su lugar (fallback)

#### Especificación de Remediación (Código Seguro)

**En main.py — Agregar TrustedHostMiddleware:**
```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI(...)

# Configure which proxy IPs are trusted for X-Forwarded-For
# RULE: Only trust X-Forwarded-For from known ALB/Nginx IPs
trusted_proxies = [
    "10.0.0.0/8",        # Internal VPC CIDR
    "172.16.0.0/12",     # Docker internal
    "127.0.0.1",         # Localhost
    # Add actual ALB/Nginx IP here, e.g. "10.0.1.50"
]

# TrustedHostMiddleware respects X-Forwarded-For ONLY from trusted IPs
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Not restricting hostnames, only X-Forwarded-For trust
    # Note: TrustedHostMiddleware doesn't handle X-Forwarded-For directly
)
```

**Mejor opción — Usar middleware personalizado:**
```python
from starlette.middleware.base import BaseHTTPMiddleware
from ipaddress import IPv4Network, IPv4Address

TRUSTED_PROXY_NETWORKS = [
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("127.0.0.1/32"),
]

class TrustedProxyMiddleware(BaseHTTPMiddleware):
    """
    Extract real client IP from X-Forwarded-For ONLY if request comes from trusted proxy.
    
    RULE: Client IP for rate limiting is:
    1. X-Forwarded-For[0] IF request.client.host is in TRUSTED_PROXY_NETWORKS
    2. request.client.host otherwise
    3. "0.0.0.0" if unavailable
    """
    async def dispatch(self, request: Request, call_next):
        client_ip = None
        
        # Check if direct connection is from trusted proxy
        if request.client:
            try:
                client_addr = IPv4Address(request.client.host)
                is_trusted_proxy = any(
                    client_addr in network for network in TRUSTED_PROXY_NETWORKS
                )
                
                if is_trusted_proxy:
                    # Extract leftmost IP from X-Forwarded-For (real client)
                    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
                    if x_forwarded_for:
                        client_ip = x_forwarded_for.split(",")[0].strip()
            except ValueError:
                pass
        
        # Fallback to direct connection IP
        if not client_ip:
            client_ip = request.client.host if request.client else "0.0.0.0"
        
        # Store in scope for rate limiter
        request.scope["client_ip"] = client_ip
        
        response = await call_next(request)
        return response

# In main.py:
app.add_middleware(TrustedProxyMiddleware)

# Update get_user_rate_limit_key() to use trusted IP:
def get_user_rate_limit_key(request: Request) -> str:
    client_ip = request.scope.get("client_ip", "0.0.0.0")
    return f"ip:{client_ip}"
```

**Nota:** Esta es una **recomendación de hardening avanzado**. El riesgo actual es bajo porque:
1. Global rate limit (20/min) aún activo
2. Ataque requiere network access o compromiso de proxy
3. Altamente visible en logs (múltiples IPs por segundo)

---

## 4. 🔏 INVARIANTES Y REGLAS DE ARQUITECTURA ASOCIADAS

### Invariante 1: Cryptographic Binding de Company ID
**Statement:** El `company_id` de un usuario NUNCA debe ser extraído de headers configurables por cliente. DEBE ser extraído exclusivamente de JWT verificado criptográficamente, sellado con HMAC.

**Implementación:**
- ✅ `refresh_token_handler.py` línea 117-121: `validate_company_binding()` verifica `fam_hash` con `hmac.compare_digest()`
- ✅ JWT payload incluye `"co"` (company_id) + `"fam_hash"` (HMAC seal)
- ❌ Nunca aceptar `X-Company-ID` header del cliente como source of truth (solo usado para audit/logging)

**Verificación de Frontera:**
```python
# CORRECT: Verify JWT signature BEFORE extracting company_id
payload = jwt.decode(refresh_token, secret_key, algorithms=["HS256"])
company_id = UUID(payload["co"])
assert payload["fam_hash"] == hmac.new(secret_key, ...).hexdigest()

# WRONG: Extract from header
company_id = request.headers.get("X-Company-ID")  # ❌ Client-controllable
```

---

### Invariante 2: Generation Counter Monotonicity
**Statement:** `current_generation` en TokenFamily SOLO puede incrementar: gen_0 → gen_1 → gen_2 → ... NUNCA decrecer ni saltar.

**Implementación:**
- ✅ `sqlalchemy_refresh_token_repo.py`: `next_generation = family.current_generation + 1` (línea ~90)
- ✅ `refresh_token_handler.py` línea 170: `if token.generation < family.current_generation - 1: BREACH`
- ✅ Validación en persistencia: Constraint `CHECK (current_generation >= 0)` + audit trail en `refresh_token_rotation_audit`

**Violation Detector:**
```python
# Breach detected if generation gap > 1
gap = family.current_generation - token_payload.generation
if gap > 1:
    logger.error(f"BREACH: Generation gap {gap} detected for family {family_id}")
    await revoke_family_for_breach(...)
```

---

### Invariante 3: Atomicity de Revocation + Audit
**Statement:** Cuando se detecta breach, la revocación (UPDATE status=revoked) Y el audit log (INSERT into audit table) DEBEN ser atómicos. No debe haber window donde uno ocurrió pero el otro no.

**Implementación:**
- ✅ `refresh_token_handler.py` línea 278-289: within single transaction
  ```python
  await self.token_repo.revoke_family(...)  # UPDATE statement
  await self.token_repo.log_rotation_event(...)  # INSERT statement
  ```
- ✅ SQLAlchemy `begin_nested()` en repository asegura transacción local
- ❌ No hacer revoke en una transacción y audit en otra (window de inconsistencia)

**Violación Detection:** Audit log sin matching revocation record = data integrity violation

---

### Invariante 4: Fire-and-Forget Alerts Never Block Security Operations
**Statement:** NotificationClient failures NUNCA deben bloquear:
- Token revocation
- Audit logging
- Response to client

**Implementación:**
- ✅ `refresh_token_handler.py` línea 301-305: `try/except` envuelve notification call, no re-raises
- ✅ `notification_client.py` línea 100-105: Todas las excepciones logged but not propagated
- ✅ Return type `-> None` (no await result)

**Violation Detection:**
```python
# WRONG: Alert failure blocks revocation
try:
    await notification_client.send_breach_alert(...)
except Exception:
    # Empty except — revocation doesn't happen
    pass

# CORRECT: Alert in separate try/except AFTER revocation
await revoke_family(...)  # Critical operation
try:
    await notification_client.send_breach_alert(...)
except Exception as e:
    logger.error(f"Alert failed but revocation succeeded: {e}")
```

---

### Invariante 5: Rate Limiting es Multi-Layer (Defense-in-Depth)
**Statement:** Rate limiting NUNCA depende de un solo mecanismo. DEBE haber:
1. Per-user limit (10/min) — Protege contra credential stuffing dirigido
2. Global limit (20/min) — Protege servicio completo contra DDoS
3. Fallback a IP si user_id no disponible — Protege contra JWT malformados

**Implementación:**
- ✅ `refresh_token_rtr.py` línea 111-112: Doble decorador SlowAPI
- ✅ `get_user_rate_limit_key()` línea 85-90: Fallback IP logic
- ✅ `notification_client.py` línea 31: 3s timeout en HTTP para evitar resource exhaustion

**Violación Detection:** Si una sola capa falla (ej: per-user key extraction returns error), global limit aún activo = OK.

---

## 5. 🧪 LISTA DE VERIFICACIÓN PARA PRUEBAS DE SEGURIDAD (Security Test Cases)

### Suite 1: Information Disclosure Prevention (Finding 1)
```python
import asyncio
import pytest
from fastapi.testclient import TestClient
import re

class TestInformationDisclosurePrevention:
    """Verify all authentication errors return identical generic message."""
    
    @pytest.mark.parametrize("test_case", [
        {
            "name": "Expired Token",
            "payload": {"refresh_token": EXPIRED_JWT},
            "expected_status": 401,
        },
        {
            "name": "Revoked Token (Family)",
            "payload": {"refresh_token": REVOKED_JWT},
            "expected_status": 401,
        },
        {
            "name": "Reuse Detected (Gen Gap)",
            "payload": {"refresh_token": REUSED_JWT},
            "expected_status": 401,
        },
        {
            "name": "Company ID Mismatch (HMAC Tampering)",
            "payload": {"refresh_token": TAMPERED_HMAC_JWT},
            "expected_status": 401,
        },
        {
            "name": "Family Not Found",
            "payload": {"refresh_token": NONEXISTENT_FAMILY_JWT},
            "expected_status": 401,
        },
    ])
    def test_all_auth_errors_return_generic_message(self, test_case):
        """ASSERTION: All 5 exception handlers return 'Invalid token'."""
        response = client.post("/api/v1/auth/refresh", json=test_case["payload"])
        
        assert response.status_code == test_case["expected_status"]
        data = response.json()
        
        # CRITICAL: Message MUST be generic
        assert data["detail"] == "Invalid token"
        
        # CRITICAL: Must NOT leak exception class name
        assert not any(
            exc_name in data["detail"]
            for exc_name in ["RefreshTokenExpiredError", "RefreshTokenRevokedError", ...]
        )
    
    def test_error_message_constant_time(self):
        """
        ASSERTION: All error responses have similar response time.
        Timing leak = attacker can distinguish error types by latency.
        """
        import time
        
        response_times = []
        
        for _ in range(100):
            start = time.perf_counter()
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": random_invalid_jwt()}
            )
            elapsed = time.perf_counter() - start
            response_times.append(elapsed)
        
        mean = sum(response_times) / len(response_times)
        variance = sum((t - mean) ** 2 for t in response_times) / len(response_times)
        std_dev = variance ** 0.5
        
        # Response time variance should be <10ms (consistent timing)
        assert std_dev < 0.01, f"Response timing variance too high: {std_dev}s"
    
    def test_internal_logs_preserve_details(self):
        """
        ASSERTION: While client gets 'Invalid token', logs contain full exception details.
        This allows debugging and incident response without leaking to attacker.
        """
        import logging
        
        with caplog.at_level(logging.WARNING):
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": REUSED_JWT}
            )
        
        # Client sees generic message
        assert response.json()["detail"] == "Invalid token"
        
        # Logs contain detailed reason (for incident response team)
        assert any(
            "REUSE_DETECTED" in record.message or "Security breach detected" in record.message
            for record in caplog.records
        )
```

---

### Suite 2: Breach Detection + Atomic Revocation (Finding 2)
```python
class TestBreachDetectionAndRevocation:
    """Verify generation gap triggers immediate family revocation + audit."""
    
    @pytest.mark.asyncio
    async def test_reuse_detection_revokes_entire_family(self):
        """ASSERTION: Token reuse (gen_gap > 1) atomically revokes ALL tokens in family."""
        # Setup: Create family with gen=5
        family = await create_token_family_with_generation(5)
        token_gen3 = create_refresh_token(family, generation=3)  # Gap: 5 - 3 = 2
        
        # Attempt reuse with gen-3 token when family is at gen=5
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token_gen3},
            headers={"X-Company-ID": family.company_id}
        )
        
        # ASSERTION 1: Request rejected
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
        
        # ASSERTION 2: Family is revoked in DB
        revoked_family = await db.query(RefreshTokenFamily).filter(
            RefreshTokenFamily.id == family.id
        ).first()
        assert revoked_family.revoked_at is not None
        assert revoked_family.revocation_reason == "REUSE_DETECTED"
        
        # ASSERTION 3: ALL tokens in family are unusable
        # Try with other tokens from same family
        for gen_val in [0, 1, 2, 3, 4, 5]:
            other_token = create_refresh_token(family, generation=gen_val)
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": other_token},
                headers={"X-Company-ID": family.company_id}
            )
            assert response.status_code == 401
            assert response.json()["detail"] == "Invalid token"
    
    @pytest.mark.asyncio
    async def test_breach_audit_trail_immutable(self):
        """ASSERTION: Breach event logged to audit table, Event Listeners prevent UPDATE/DELETE."""
        family = await create_token_family()
        reused_token = create_refresh_token(family, generation=family.current_generation - 2)
        
        # Trigger breach
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": reused_token},
            headers={"X-Company-ID": family.company_id}
        )
        
        # Check audit log
        audit_record = await db.query(RefreshTokenRotationAudit).filter(
            RefreshTokenRotationAudit.family_id == family.id,
            RefreshTokenRotationAudit.action == "REUSE_DETECTED"
        ).first()
        
        assert audit_record is not None
        assert audit_record.ip_address == "127.0.0.1"  # Captured for investigation
        
        # CRITICAL: Audit record is immutable (no UPDATE/DELETE possible)
        with pytest.raises(RuntimeError):
            audit_record.action = "NORMAL_REFRESH"
            await db.commit()
        
        # Verify Event Listeners block the mutation
        session.begin()
        session.add(audit_record)
        with pytest.raises(RuntimeError, match="audit log.*append-only"):
            await session.flush()
    
    @pytest.mark.asyncio
    async def test_notification_client_failure_doesnt_block_revocation(self):
        """ASSERTION: If notification_service is down, revocation still succeeds."""
        import asyncio
        
        family = await create_token_family()
        reused_token = create_refresh_token(family, generation=0)  # Gen gap = current - 0 > 1
        
        # Mock notification_service to raise timeout
        with patch("auth_app.infrastructure.clients.notification_client.httpx.AsyncClient") as mock_client:
            async def raise_timeout(*args, **kwargs):
                raise httpx.TimeoutException("notification_service timeout")
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(side_effect=raise_timeout)
            
            # Send request — should succeed despite notification failure
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": reused_token},
                headers={"X-Company-ID": family.company_id}
            )
            
            # ASSERTION: Revocation happened despite alert failure
            assert response.status_code == 401
            revoked_family = await db.query(RefreshTokenFamily).filter(
                RefreshTokenFamily.id == family.id
            ).first()
            assert revoked_family.revoked_at is not None
```

---

### Suite 3: Per-User Rate Limiting (Finding 3)
```python
class TestPerUserRateLimiting:
    """Verify layered rate limiting (per-user + global) functions correctly."""
    
    @pytest.mark.asyncio
    async def test_per_user_limit_10_per_minute(self):
        """ASSERTION: Single user limited to 10 refreshes/minute."""
        user_id = uuid4()
        family = await create_token_family_for_user(user_id)
        
        # Make 10 successful refreshes
        for i in range(10):
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": generate_valid_token(family, gen=i)}
            )
            assert response.status_code == 200
        
        # 11th request should be rate-limited
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": generate_valid_token(family, gen=10)}
        )
        assert response.status_code == 429  # Too Many Requests
        assert "rate" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_global_limit_20_per_minute(self):
        """ASSERTION: All users combined limited to 20 refreshes/minute."""
        # Create 3 different users
        families = [
            await create_token_family_for_user(uuid4()),
            await create_token_family_for_user(uuid4()),
            await create_token_family_for_user(uuid4()),
        ]
        
        # User 1: 8 requests (under per-user limit, but contributes to global)
        # User 2: 7 requests (total = 15)
        # User 3: 5 requests (total = 20)
        request_count = 0
        for user_idx, family in enumerate(families):
            for i in range([8, 7, 5][user_idx]):
                response = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refresh_token": generate_valid_token(family, gen=i)}
                )
                assert response.status_code == 200
                request_count += 1
        
        assert request_count == 20
        
        # 21st request from ANY user should hit global limit
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": generate_valid_token(families[0], gen=8)}
        )
        assert response.status_code == 429
    
    @pytest.mark.asyncio
    async def test_rate_limit_key_extraction_fallback(self):
        """ASSERTION: If user_id extraction fails, fall back to IP gracefully."""
        # Create malformed JWT (no 'sub' claim)
        malformed_jwt = create_jwt({"fam": str(uuid4())}, exclude_fields=["sub"])
        
        # Request should fail at authentication (invalid JWT), not rate limiting
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": malformed_jwt}
        )
        
        # Expect 401 from JWT validation, not 429 from rate limiting
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
    
    def test_ip_spoofing_fallback_to_global_limit(self):
        """
        ASSERTION: If attacker spoofs IP (changes X-Forwarded-For), per-IP limit is bypassed,
        but global 20/min limit still protects service.
        """
        # Simulate attacker sending requests from different spoofed IPs
        for fake_ip in [f"192.168.1.{i}" for i in range(30)]:
            response = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": valid_token()},
                headers={"X-Forwarded-For": fake_ip}
            )
            
            # First 20 succeed (global limit)
            if response.status_code != 429:
                assert response.status_code == 200
            else:
                # 21st+ hit global limit
                assert response.status_code == 429
```

---

### Suite 4: Cryptographic Binding (Core RTR Security)
```python
class TestCryptographicBindingAndGeneration:
    """Verify HMAC sealing and generation counter invariants."""
    
    @pytest.mark.asyncio
    async def test_company_id_hmac_binding_prevents_cross_tenant_token_reuse(self):
        """
        ASSERTION: Token issued for Company A cannot be used for Company B.
        HMAC binding makes it cryptographically impossible to forge.
        """
        company_a_id = uuid4()
        company_b_id = uuid4()
        
        family_a = await create_token_family(company_id=company_a_id)
        token_a = generate_refresh_token(family_a)
        
        # Attempt to use Company A token against Company B
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": token_a},
            headers={"X-Company-ID": company_b_id}  # Wrong company
        )
        
        # ASSERTION: Rejected
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid token"
        
        # Verify HMAC validation failed (not just database lookup)
        assert any(
            "Company binding" in log.message or "HMAC" in log.message
            for log in caplog.records if "failed" in log.message.lower()
        )
    
    @pytest.mark.asyncio
    async def test_generation_counter_increment_atomically(self):
        """ASSERTION: Generation counter increments atomically with token issuance."""
        family = await create_token_family()
        initial_gen = family.current_generation  # Should be 0
        
        # Refresh once
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": generate_token(family, gen=initial_gen)}
        )
        assert response.status_code == 200
        
        # Check new token has gen+1
        new_token = response.json()["data"]["refresh_token"]
        new_payload = jwt.decode(new_token, options={"verify_signature": False})
        assert new_payload["gen"] == initial_gen + 1
        
        # Verify family was updated in DB
        updated_family = await db.query(RefreshTokenFamily).filter(
            RefreshTokenFamily.id == family.id
        ).first()
        assert updated_family.current_generation == initial_gen + 1
```

---

## Conclusiones y Recomendaciones de Hardening Futuro

### Cumplimiento Actual: **A- (Excelente)**
✅ 3 findings OWASP remediados correctamente  
✅ Criptografía fuerte (HMAC-SHA256, constante-tiempo)  
✅ Multi-layer rate limiting, audit inmutable, atomic revocation  

### Recomendaciones de Hardening Fase 178:
1. **CRÍTICA:** Implementar inter-service HMAC (Finding-RTR-002) — 1h de trabajo
2. **MEDIA:** Opción A rate limiting (IP-based) sobre JWT unverified — 30min
3. **BAJA:** TrustedProxyMiddleware para X-Forwarded-For — 1h (pero baja prioridad)

### Roadmap de Validación:
- [ ] Ejecutar test suites (Suite 1-4) en integration environment
- [ ] Penetration testing: Intentar timing attacks en error responses
- [ ] Load testing: Validar rate limiting bajo 1000+ req/sec
- [ ] Code review: Senior engineer revisar HMAC implementation (cryptography.io preferred over native hmac)

---

**Documento Generado por:** Senior Security Auditor  
**Fecha:** 2026-06-03  
**Confidencialidad:** INTERNO - Distribuir a: Security Team, Engineering Lead, CTO  
**Próxima Auditoría:** Phase 178 (post-hardening implementation)
