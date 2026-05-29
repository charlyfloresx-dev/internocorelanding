# Master Implementation History — 2026-05-29

## Phase 156 — MES Cold-Start: Seed de Configuración + Shift CRUD REST

### Problema resuelto
El `ResourceMonitorComponent` (Angular) mostraba "Sin datos" porque `mes_db` no tenía configuración de planta (Facilities, Resources, Shifts). La Phase 154 Part 3 conectó el frontend a los endpoints reales, pero la DB estaba vacía.

### Arquitectura ejecutada

```
mes_db (vacía antes de Phase 156)
│
├── Migration 010: UQ(code) → UQ(company_id, code) en mes_shifts
│   Razón: bug de diseño bloqueaba multi-tenant con códigos compartidos MAT/VES/NOC
│
└── scripts/seed_mes_config.py
    │
    ├── 3 × Facility      (PLT-TIJ, PLT-MXC, PLT-SDG)
    ├── 9 × ProductionArea (3 por empresa)
    ├── 12 × Resource      (CELDA-58D, CELDA-59A, TURRET-01, PRENSA-01 × 3 empresas)
    ├── 9 × Shift          (MAT/VES/NOC × 3 empresas — posible gracias a migration 010)
    ├── 18 × ShiftBreak    (2 por turno: Descanso + Comida 30min c/u)
    └── 15 × StandardTime  (ECM-600, TRB-700, BRK-800, FLI-900, SUS-100 × 3 empresas)
```

### Decisiones arquitectónicas

1. **IDs determinísticos** `uuid5(NAMESPACE_DNS, "mes156.<tipo>.<company_id>.<code>")`:
   - Idempotencia garantizada sin SELECT-before-INSERT (usa `session.get(model, id)`)
   - IDs estables entre ejecuciones → facilita debugging y referencias cruzadas

2. **Parámetro `db_url`** en `seed_mes_config()`:
   - Evita que tests locales usen `CORE_DATABASE_URL` del `.env` raíz que apunta a `dbname` (no `mes_db`)
   - Pattern: tests pasan `MES_TEST_DB_URL` explícitamente

3. **Fixture de test simplificada** (`seeded_db` → solo `yield db_session`):
   - El seed ya corrió en el startup del contenedor (`entrypoint.sh → seed.py`)
   - No re-ejecutar el seed en cada test — los datos ya están committed

4. **`shift.py` CRUD completo** — sin nueva capa de repositorio:
   - Los 7 nuevos endpoints usan `get_db` directamente (mismo patrón que `resource.py`)
   - `ShiftRead.from_orm()` serializa `start_time`/`end_time` como `"HH:MM"` string
   - `_parse_time()` helper para recibir `"HH:MM"` en POST/PATCH (evita timezone ambiguity)
   - `DELETE /{id}` = soft-delete (`is_active=False`), `DELETE /breaks/{id}` = hard-delete

### Workarounds / Deuda técnica generada

- **`ShiftBreak.shift_id` CASCADE**: ya implementado en migration 009 (`ondelete="CASCADE"`)
- **`mes_app.schemas.planning` PydanticUserError**: aún pendiente (campo `name` clash) — no afecta Phase 156
- **`ResourceConfigComponent` + `ShiftConfigComponent` Angular**: próxima tarea — la DB ya tiene datos, ahora hace falta la UI admin para gestionar celdas/turnos

### Tests

| Suite | Tests | Estado |
|---|---|---|
| `test_seed_mes_config.py` | 19 | ✅ |
| `test_shift_crud.py` | 13 | ✅ |
| Subtotal Phase 156 | 32 | ✅ |
| **Total acumulado MES** | **87** | **0 regresiones** |

### Archivos clave

| Archivo | Tipo | Descripción |
|---|---|---|
| `alembic/versions/010_fix_shift_code_unique_per_company.py` | NUEVO | Migración corrige UQ global → por empresa |
| `scripts/seed_mes_config.py` | NUEVO | Seed de configuración completa de planta |
| `scripts/seed.py` | MOD | Llama `seed_mes_config()` en startup |
| `mes_app/api/v1/endpoints/shift.py` | MOD | CRUD completo Shift + ShiftBreak |
| `tests/integration/test_seed_mes_config.py` | NUEVO | 19 tests de seed |
| `tests/integration/test_shift_crud.py` | NUEVO | 13 tests Shift CRUD |
