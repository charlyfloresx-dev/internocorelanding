# InternoCore: Master Implementation History - 2026-05-12

## Phase 99: Muro de Hierro (Rate Limiting) — COMPLETADA

### Visión General
Capa de protección perimetral en el Monolito Unificado para prevenir DoS, abusos de scanners industriales y asegurar consumo justo entre inquilinos (Fair Usage).

### Componentes
- **Provider**: `slowapi` (basado en `limits`)
- **Storage**: Redis v7-alpine en el stack Docker
- **Identificación Multi-layer**: User (JWT) > Tenant (X-Company-ID) > IP (fallback)

### Configuración
- Global Burst: 100 req/min
- Hourly Quota: 2,000 req/hora
- Fail-Open Strategy: Si Redis es inalcanzable, se permite el flujo (disponibilidad > bloqueo)

---

## Phase 100: Big Bang — 1M Records Stress Test — EN PROGRESO

### Objetivo
Validar integridad transaccional y rendimiento de la base de datos bajo inyección masiva de 1,000,000 de registros Kardex (`inventory_transactions`).

### Arquitectura del Bypass Administrativo
```
Request → multi_layer_key_func()
  ├── X-Internal-Secret matches? → return None (EXENTO)
  ├── X-Admin-Master-Key matches? → return None (EXENTO)
  ├── JWT user_id present? → return "user:{uuid}" (LIMITADO)
  ├── X-Company-ID present? → return "tenant:{uuid}" (LIMITADO)
  └── fallback → return IP (LIMITADO)
```

### Endpoint de Carga Masiva
- **Ruta**: `POST /api/v1/inventory/bulk-load`
- **Autenticación**: `X-Internal-Secret` header (must match `CORE_INTERNAL_API_KEY`)
- **Inserción**: SQLAlchemy `insert()` con `executemany` para inserción atómica
- **Mapeo de Tipos**: String → `TransactionType` Enum (IN, OUT, ADJUSTMENT, TRANSFER, RESERVE, RELEASE, BACKFLUSHING)

### Problemas Encontrados y Resueltos
| Problema | Causa Raíz | Solución |
|---|---|---|
| `Limiter.__init__() got unexpected keyword argument 'request_filter'` | `slowapi` no soporta `request_filter` | Mover lógica de bypass dentro de `multi_layer_key_func` retornando `None` |
| `.env` variables `None` en Python | PowerShell `Set-Content -Encoding utf8` inyecta BOM (`\xef\xbb\xbf`) | Strippear BOM bytes + usar `dotenv_values()` en vez de `load_dotenv()` |
| `load_dotenv(override=True)` no funciona | PowerShell cachea env vars vacías que bloquean override | Usar `dotenv_values()` dict merge directamente |
| Enum `UniqueViolationError` en arranque | Workers concurrentes de uvicorn crean el mismo tipo ENUM | **Pendiente**: Implementar `IF NOT EXISTS` o Alembic |
| Empty exception messages | `str(e)` vacío en algunos httpx errors | Usar `type(e).__name__: {str(e)}` para diagnóstico completo |

### Script de Carga (`big_bang_inventory_loader.py` v2)
- **Batch Size**: 1,000 registros (reducido de 10,000)
- **Concurrencia**: 3 batches simultáneos (reducido de 5)
- **Timeout**: 120s por batch (aumentado de 60s)
- **Pre-flight Check**: Verifica `/health` antes de iniciar
- **Datos Industriales**: Balance acumulado realista, cantidades con signo (OUT = negativo)
