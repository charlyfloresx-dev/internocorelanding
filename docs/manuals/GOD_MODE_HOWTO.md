# GOD MODE — Manual de Operación Break-Glass

> **Clasificación:** CONFIDENCIAL — Solo personal de infraestructura autorizado  
> **Aplicable a:** InternoCore SaaS Multi-Tenant  
> **Última actualización:** 2026-05-18 (Phase 113)

---

## ¿Qué es el GOD MODE?

El GOD MODE es un mecanismo de **acceso de emergencia (break-glass)** diseñado para situaciones donde el flujo normal de autenticación está comprometido o bloqueado (base de datos de usuarios caída, migración fallida, lock-out de administradores). Permite a personal de infraestructura con la clave maestra emitir una sesión de administración temporal de 5 minutos, completamente auditada.

> **No es** un atajo para tareas rutinarias. Cada activación queda registrada permanentemente en los logs de seguridad y es visible para todos los administradores del sistema.

---

## Arquitectura del Flujo

```
[Operador de infraestructura]
         |
         | (1) Navega a /admin/system-control
         |     → Protegido por permissionGuard (solo admin/owner)
         |
         v
[Panel GOD MODE — Frontend]
         |
         | (2) Ingresa CORE_ADMIN_MASTER_KEY en campo tipo "password"
         |     → Campo NO se persiste. Vive solo en memoria RAM del navegador.
         |     → 3 intentos máximos antes de bloquear la UI localmente.
         |
         v
POST /api/v1/admin/elevate
  Header: X-Admin-Master-Key: <clave>
  Header: X-Company-ID: <empresa objetivo> (opcional)
         |
         | (3) Backend valida la clave contra CORE_ADMIN_MASTER_KEY del entorno
         |     → Límite: 3 requests / hora / IP (SlowAPI)
         |     → Si falla: 401 ERR_INVALID_MASTER_KEY (loggea el intento)
         |     → Si pasa:
         |         - Genera JWT de 300s (5 min) con scopes:["*"]
         |         - Asigna JTI único para trazabilidad y revocación
         |         - Persiste en audit_logs: ip, user-agent, path, jti, timestamp
         |         - Emite logger.critical: [SECURITY_ALERT] GOD_MODE_ACTIVATED
         |
         v
[Sesión de Emergencia — Frontend]
         |
         | (4) Token almacenado SOLO en signal store (memoria)
         |     → Se autodestruye a los 300s (setTimeout)
         |     → Se destruye si el operador navega fuera del módulo
         |     → Todas las requests HTTP usan este token (interceptor)
         |
         v
[Operaciones de Emergencia]
         |
         | (5) El operador ejecuta las acciones necesarias:
         |     - Asignar usuario a empresa (forzado)
         |     - Actualizar rol de emergencia
         |     - Ver logs de seguridad
         |
         v
[Panel de Auditoría]
         | (6) GET /api/v1/admin/security-logs
         |     → Lista todos los eventos GOD_MODE_ACTIVATED
         |     → Muestra IP, User-Agent, JTI, timestamp
         |     → Filas rojas parpadeantes si < 24h
         |
         v
[Cierre de Sesión]
         | (7) El token expira automáticamente a los 300s
         |     O el operador pulsa "Cerrar sesión de emergencia"
         |     → Frontend limpia el signal store
         |     → (Futuro) DELETE Redis key godmode:{jti}
```

---

## Requisitos Previos

### Backend
- `CORE_ADMIN_MASTER_KEY` configurado en el `.env` del servidor (≥16 chars, no `GOD_MODE_ACTIVE`)
- Auth service corriendo y accesible
- Tabla `audit_logs` en la DB (migración aplicada)

### Frontend
- Rol `admin` u `owner` en el JWT activo (el `permissionGuard` bloquea el acceso a `/admin/system-control`)
- Conocer la `CORE_ADMIN_MASTER_KEY` — **nunca se almacena en el frontend ni en archivos de configuración del cliente**

---

## ¿De Dónde Sale la Clave Maestra?

La `CORE_ADMIN_MASTER_KEY` es un secreto de infraestructura. El operador la ingresa manualmente en el momento de la emergencia. Nunca viaja en el código fuente ni en archivos del cliente.

### Entorno de desarrollo local

```bash
# Leer del .env del proyecto
grep CORE_ADMIN_MASTER_KEY C:\API\interno\.env
```

El valor actual es `ROTATED_MASTER_KEY_GOD_MODE`. El equipo de desarrollo lo conoce porque tiene acceso al repo.

### Entorno de producción (AWS)

La clave vive en **AWS Secrets Manager**. Recuperarla antes de una emergencia:

```bash
aws secretsmanager get-secret-value \
  --secret-id interno-core/auth-service/prod \
  --region us-east-2 \
  --query 'SecretString' \
  --output text | python3 -c "import sys,json; print(json.load(sys.stdin)['admin_master_key'])"
```

Copiar el valor. No guardarlo en ningún lugar — ingresarlo directamente en el panel y desecharlo.

### Equipos con múltiples administradores

Guardar en un gestor de secretos compartido (1Password Teams, Bitwarden, HashiCorp Vault). Ejemplo en 1Password:

```
Vault: "Interno Core — Infraestructura"
Item:  "GOD MODE — Master Key (Producción)"
Field: password → <CORE_ADMIN_MASTER_KEY>
```

Solo los roles `owner` o `infrastructure` tienen acceso al vault. Al necesitarla, el operador abre 1Password, copia la clave, activa el panel, y ejecuta la operación. No la guarda en ningún otro lugar.

> **Rotar la clave después de cualquier uso en producción.** Actualizar en AWS Secrets Manager y en 1Password simultáneamente, luego reiniciar el contenedor `interno-auth-dev` para que tome el nuevo valor.

---

## Cómo Activar (Paso a Paso)

### 1. Navegar al Panel

```
https://tu-dominio.com/admin/system-control
```

Solo usuarios con rol `admin` o `owner` pueden acceder. Los demás son redirigidos a `/dashboard`.

### 2. Obtener la Clave

Según el entorno (ver sección anterior):
- **Local:** leer del `.env`
- **Producción:** recuperar de AWS Secrets Manager o 1Password
- Tenerla lista para pegar — no la copies a un bloc de notas

### 3. Ingresar la Clave Maestra

En el componente **"Consola de Emergencia"**:

1. Pega la `CORE_ADMIN_MASTER_KEY` en el campo de texto (tipo password — los caracteres están ocultos)
2. Pulsa **"Activar sesión de emergencia"**
3. Confirma en el diálogo: **"¿Está seguro de que desea elevar privilegios globales?"**

> Si ingresas la clave incorrecta 3 veces consecutivas, la UI se bloquea localmente. Recarga la página para intentar de nuevo (el rate limit del backend aplica por IP, no por recarga de página).

### 3. Sesión Activa

Cuando la sesión está activa verás:
- Banner rojo: **"SESIÓN DE EMERGENCIA ACTIVA — 4:58 restantes"** (cuenta regresiva)
- Todas las acciones tienen acceso completo (`scopes: ["*"]`)
- El JTI aparece en el banner para confirmar qué sesión está activa

### 4. Ejecutar Operaciones

Con la sesión activa puedes:
- Forzar asignación de usuario a empresa (`POST /api/v1/admin/users/force-assign`)
- Actualizar roles de emergencia (`PATCH /api/v1/admin/roles/force-update`)
- Ver logs de seguridad en tiempo real

### 5. Cerrar Sesión

La sesión se cierra automáticamente al expirar (300s). Para cerrarla manualmente:
1. Pulsa **"Cerrar sesión de emergencia"** en el banner
2. El frontend limpia el token de memoria inmediatamente

---

## Verificar el Audit Trail

Después de cualquier activación, verifica el registro en el panel de alertas:

```
GET /api/v1/admin/security-logs
Authorization: Bearer <tu-token-normal-de-admin>
```

O en el panel frontend `/admin/system-control` → pestaña **"Alertas de Seguridad"**.

Cada evento muestra:
- `timestamp` — cuándo se activó
- `ip_address` — desde dónde
- `user_agent` — qué navegador/sistema
- `metadata.jti` — identificador único de esa sesión (permite correlacionar con logs de contenedor)

### Buscar en logs del contenedor Docker

```bash
docker logs interno-auth-dev 2>&1 | grep "GOD_MODE_ACTIVATED"
```

Output esperado:
```
2026-05-18 18:45:12 [CRITICAL] security.god_mode: [SECURITY_ALERT] GOD_MODE_ACTIVATED via /elevate | ip=192.168.1.45 | ua=Mozilla/5.0... | company=<uuid> | jti=6858faaf-... | trace=51ad8d64-...
```

---

## API Reference

### `POST /api/v1/admin/elevate`

Intercambia la master key por un token de emergencia de 5 minutos.

**Headers requeridos:**
```
X-Admin-Master-Key: <CORE_ADMIN_MASTER_KEY>
Content-Type: application/json
```

**Headers opcionales:**
```
X-Company-ID: <uuid>   # Si se omite, el token no tiene company scope
```

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 300,
    "metadata": {
      "scope": ["*"],
      "role": "admin",
      "jti": "6858faaf-407b-4cff-9d8b-f7f9cadaf411",
      "warning": "Esta sesión está siendo estrictamente auditada en el log del servidor."
    }
  }
}
```

**Errores:**
| Código | `code` | Causa |
|---|---|---|
| 401 | `ERR_INVALID_MASTER_KEY` | Clave incorrecta |
| 422 | (Pydantic) | Header `X-Admin-Master-Key` ausente |
| 429 | `ERR_RATE_LIMIT` | Más de 3 intentos / hora / IP |

---

### `GET /api/v1/admin/security-logs`

Retorna eventos de seguridad GOD MODE del audit trail.

**Headers requeridos:**
```
Authorization: Bearer <token-admin-normal-o-god-mode>
X-Company-ID: <uuid>
```

**Query params:**
```
limit: int (default: 50, max: 200)
```

**Response 200:**
```json
{
  "status": "success",
  "message": "4 security events found.",
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "SECURITY_ALERT",
      "message": "GOD_MODE_ACTIVATED",
      "ip_address": "192.168.1.45",
      "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...",
      "timestamp": "2026-05-18T18:45:12Z",
      "metadata": {
        "jti": "6858faaf-407b-4cff-9d8b-f7f9cadaf411",
        "company_id": "00000000-0000-0000-0000-000000000001",
        "correlation_id": "51ad8d64-bc80-45f1-b9f4-2d66a44dc47c",
        "expires_in": 300
      }
    }
  ]
}
```

---

## Criterios de Aceptación QA

| # | Criterio | Cómo verificar |
|---|---|---|
| 1 | Fail-closed: string vacío o clave incorrecta → UI bloqueada tras 3 intentos | Ingresar clave incorrecta 3 veces; verificar que el botón se deshabilita |
| 2 | Limpieza de memoria: cerrar pestaña destruye el token | F12 → Memory heap antes/después de cerrar; el string JWT no debe aparecer |
| 3 | Trazabilidad: cada activación genera log `[SECURITY_ALERT] GOD_MODE_ACTIVATED` | `docker logs interno-auth-dev 2>&1 \| grep GOD_MODE` |
| 4 | Audit trail: evento visible en `/security-logs` con IP real | Panel de alertas → verificar IP pública del cliente |
| 5 | Expiración automática: sesión termina a los 300s | Observar cuenta regresiva; verificar que las requests fallan con 401 después de 300s |
| 6 | Rate limit: 4to intento en la misma hora → 429 | Activar 3 veces con clave correcta, 4to intento debe retornar 429 |

---

## Consideraciones de Seguridad Operacional

1. **Rotar `CORE_ADMIN_MASTER_KEY` después de cualquier activación de emergencia** — especialmente si la causa fue una brecha de seguridad.
2. **Nunca compartir la clave por canales no cifrados** (Slack, email) — usar un gestor de secretos (1Password, AWS Secrets Manager).
3. **Revisar los security-logs después de cada turno** — si aparecen activaciones no autorizadas, es una señal de compromiso.
4. **En AWS/producción:** el acceso al panel `/admin/system-control` debe estar adicionalmente restringido por IP (Security Group o WAF rule).

---

## Troubleshooting

| Síntoma | Causa probable | Solución |
|---|---|---|
| `422 Unprocessable Entity` | Header `X-Admin-Master-Key` ausente | Verificar que el frontend envía el header |
| `401 ERR_INVALID_MASTER_KEY` | Clave incorrecta o `CORE_ADMIN_MASTER_KEY` no configurado | Verificar valor en `.env` del servidor |
| `429 Too Many Requests` | Rate limit alcanzado | Esperar 1 hora desde la IP |
| Token expira en < 5 min | Reloj del servidor desincronizado | `docker exec interno-auth-dev date` — verificar UTC |
| No aparece en security-logs | Tabla `audit_logs` no existe en DB | `docker exec interno-auth-dev alembic upgrade head` |
