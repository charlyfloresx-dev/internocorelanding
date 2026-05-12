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

## Phase 100: Big Bang — 1M Records Stress Test — COMPLETADA

### Objetivo
Validar integridad transaccional y rendimiento de la base de datos bajo inyección masiva de 1,000,000 de registros Kardex (`inventory_transactions`).

### Resultados Finales
- **Volumen Inyectado**: 1,000,000 de registros.
- **Tiempo Total**: 39.9 segundos.
- **Rendimiento (Throughput)**: ~25,058 registros/segundo.
- **Integridad Forense**: Verificados 1M de registros en `inventory_transactions` vía SQL directo.

### Arquitectura del Bypass Administrativo
```
Request → multi_layer_key_func()
  ├── X-Internal-Secret matches? → return None (EXENTO)
  ├── X-Admin-Master-Key matches? → return None (EXENTO)
  ├── JWT user_id present? → return "user:{uuid}" (LIMITADO)
  ├── X-Company-ID present? → return "tenant:{uuid}" (LIMITADO)
  └── fallback → return IP (LIMITADO)
```

### Problemas Encontrados y Resueltos
| Problema | Causa Raíz | Solución |
|---|---|---|
| `RemoteProtocolError` en Loader | Monolito aún en proceso de arranque/uvicorn handshake | Reintento manual tras validación de `/health` |
| `AttributeError: ADJUST` | Typo en endpoint `/bulk-load` (esperaba `ADJUST` en vez de `ADJUSTMENT`) | Corregido mapeo en `inventory.py` y reiniciado contenedor |
| UnicodeEncodeError en Windows | Emojis (✓, ✗) en prints del script cargador | Reemplazados por ASCII ([OK], [FAIL]) para compatibilidad con PS |
| `UniqueViolationError` en Enums | Workers de uvicorn (4) compitiendo por `create_all` | Se ignoró para la prueba (noise), pero se marcó para corrección vía Alembic |
| Nuclear Docker Clean | Necesidad de purgar redes e imágenes residuales | Ejecución de `docker system prune` y remoción manual de volúmenes `interno_*` |

### Script de Carga (`big_bang_inventory_loader.py` v2.1)
- **Batch Size**: 1,000 registros
- **Concurrencia**: 3 batches simultáneos
- **Timeout**: 120s por batch
- **Pre-flight Check**: Verifica `/health` antes de iniciar
- **ASCII Mode**: Logging seguro para Windows CMD/PowerShell
