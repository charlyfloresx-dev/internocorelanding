# Implementation History — 2026-05-30

## Phase 161 — StandardTime sequence_number (Manufacturing Route)

### Problema
`StandardTime` no tenía orden definido entre operaciones del mismo ítem. No había forma de representar CORTE→SOLDADURA→ENSAMBLE con precedencia.

### Diseño
Campo `sequence_number INTEGER NOT NULL DEFAULT 10` con semántica de múltiplos de 10 (permite insertar pasos sin re-numerar). Migración con backfill determinista vía `ROW_NUMBER() OVER (PARTITION BY company_id, item_code ORDER BY operation_name) * 10`.

### Implementación
1. **Migration** `011_st_sequence_number` — ADD nullable → UPDATE ROW_NUMBER → ALTER NOT NULL
2. **Model** `standard_time.py` — `sequence_number: Mapped[int] = mapped_column(Integer, default=10, server_default='10')`
3. **Endpoint** `/route/{item_code}` — retorna operaciones de un ítem ordenadas por sequence_number
4. **Schemas** `StandardTimeCreate/Update/Read` — campo `sequence_number` incluido
5. **list_standard_times** — `order_by(item_code, sequence_number)` en lugar de solo item_code
6. **Angular form** — campo `sequence_number` con `step=10`, layout flex con `operation_name`
7. **Angular table** — badge circular teal con número de secuencia
8. **Route chain visualization** — renderizado al pie del tab cuando filtro activo

### Tests
- `test_sequence_number_defaults_to_10`
- `test_sequence_number_persists_custom_value`
- `test_route_ordered_by_sequence_number` (inserta ENSAMBLE=30, CORTE=10, INSPECCION=40, SOLDADURA=20 → espera [10,20,30,40])
- `test_update_sequence_number`

---

## Fix — Seed Self-Healing default_tax_rate

### Problema
`master_data_service/scripts/seed.py` creaba empresas con `default_tax_rate` ORM default (0.16) al hacer hard reset, antes de que `unified_industrial_seed.py` corrija los valores. Planta US debería ser 0.0.

Adicionalmente: migración `internal_id_pattern` faltaba en master_data_service desde Phase 118, rompiendo el seed con `UndefinedColumnError`.

### Solución
1. `companies_to_seed` ahora incluye clave `"tax"` explícita por empresa
2. On-create: `default_tax_rate=co["tax"]`
3. Self-healing: `elif Decimal(str(existing.default_tax_rate)) != co["tax"]` → corrección silenciosa
4. Migración `g001_add_company_internal_id_pattern.py` para cerrar gap Phase 118

### Limitación
`auth_service/scripts/seed.py` tiene el mismo riesgo — diferido hasta terminar Phase 159 RTR. El self-healing de master_data_service lo compensa parcialmente (corre después de auth_service seed y sobreescribe el valor incorrecto para los campos que maneja).

---

## Auditoría Phase A RTR

### Resultado
PASA con 3 gaps menores documentados, ninguno bloquea Phase B.

### Hallazgo crítico verificado
`hmac.compare_digest()` en `validate_company_binding()` — timing attack mitigation presente. El punto más importante del checklist está aprobado.

### Hallazgo notable
La implementación HMAC ata 4 campos en lugar de 2 del spec: `f"{family_id}||{company_id}||{user_id}||{family_salt}"`. Previene un vector adicional de ataque cross-family.

### Gaps pendientes (todos post-Phase 159)
| Gap | Archivo | Fix |
|---|---|---|
| GAP-1 | `domain/value_objects/token_family.py` | `__post_init__` con `re.fullmatch(r'^[0-9a-f]{64}$', ...)` |
| GAP-2 | `models/refresh_token_family.py` | Clarificar uso de `version_counter` vs `version_id` en handler |
| GAP-3 | `models/refresh_token_family.py` | Event listener SQLAlchemy en `RefreshTokenRotationAudit` para bloquear UPDATE/DELETE |
