# 🗺️ Mapa de Tests y Scripts — `inventory_service`

> **Propósito:** Referencia rápida para saber qué hace cada archivo, si necesita DB real, cómo correrlo, y cuándo usarlo.  
> **Regla de oro:** Solo `tests/test_ict_binational.py` corre con `pytest` de forma aislada (100% mock). El resto necesita DB real o contexto HTTP.

---

## 📁 `tests/` — Suite de Pytest

### ✅ `test_ict_binational.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Unit Test — 100% Mocks (pytest + pytest-mock) |
| **Requiere DB** | ❌ No |
| **Requiere Docker** | ❌ No |
| **Estado actual** | ✅ 2/2 pasan |
| **Qué valida** | Lógica de compliance aduanal del `TransferCommandHandler` |
| **Tests incluidos** | `test_A`: Falla controlada MX→US sin pedimento (`ERR_CUSTOMS_REQUIRED`) · `test_B`: Éxito con pedimento válido |
| **Comando** | `pytest tests/test_ict_binational.py -v` |
| **Cuándo usar** | ✅ Siempre — es la prueba más rápida y más relevante para el flujo ICT actual |

---

### ⚠️ `test_financial_regression.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script disfrazado de pytest |
| **Requiere DB** | ✅ Sí — usa `app.db.session` (conexión PostgreSQL real) |
| **Requiere Docker** | ✅ Sí |
| **Estado actual** | ❌ 1 FAIL (importa `TransferService` — módulo antiguo reemplazado por `TransferCommandHandler`) |
| **Qué valida** | WAC post-transferencia entre empresa A→B. Idempotencia de movimientos. |
| **Problema** | Importa `TransferService` que fue reemplazado. Script legado. |
| **Cuándo usar** | 🔴 NO correr hasta refactorizar imports. Ignorar por ahora. |

---

### ⚠️ `test_zero_trust_warehouse.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script disfrazado de pytest |
| **Requiere DB** | ✅ Sí — usa `app.db.session.AsyncSessionLocal + engine` |
| **Requiere Docker** | ✅ Sí |
| **Estado actual** | ❌ COLLECTION ERROR (PYTHONPATH) |
| **Qué valida** | Ownership de almacenes (Zero-Trust): Empresa B no puede acceder a almacén de Empresa A. Verifica AuditLog. |
| **Cuándo usar** | 🟡 Correr manualmente como script: `python tests/test_zero_trust_warehouse.py` en Docker |

---

### ⚠️ `test_intercompany_flow.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script disfrazado de pytest |
| **Requiere DB** | ✅ Sí — seed real (UUIDs hardcodeados de COMPANY_A/B) |
| **Requiere Docker** | ✅ Sí + datos pre-seed |
| **Estado actual** | ❌ COLLECTION ERROR (PYTHONPATH) |
| **Qué valida** | Flujo completo ICT real: initiate → complete con usuarios reales (Charly) |
| **Cuándo usar** | 🟡 Solo después de ejecutar `seed_ict_real.py`. Correr como script, no con pytest. |

---

### ⚠️ `test_fifo_report.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script disfrazado de pytest |
| **Requiere DB** | ✅ Sí — crea Warehouse, CustomsPedimento, Movement en DB real |
| **Requiere Docker** | ✅ Sí — se conecta a `localhost:5433` |
| **Estado actual** | ❌ COLLECTION ERROR (PYTHONPATH) |
| **Qué valida** | Algoritmo FIFO: priorización por fecha de pedimento más viejo, partición entre lotes |
| **Cuándo usar** | 🟡 Solo si se modifica `FIFODischargeService`. |

---

### 🟢 `test_concurrency.py`
| Campo | Detalle |
|---|---|
| **Tipo** | HTTP Stress Test (usa `httpx`) |
| **Requiere DB** | ❌ No directo — ataca el API en `localhost:8006` |
| **Requiere Docker** | ✅ Sí — necesita el servicio levantado |
| **Estado actual** | ✅ Coleccionado. Pasa trivialmente (no hay asserts reales, solo prints). |
| **Qué valida** | Optimistic Locking — 5 peticiones simultáneas al kardex para el mismo producto |
| **Cuándo usar** | 🟡 Stress test manual. Útil cuando se modifique la lógica de concurrencia. |

---

### 🟢 `test_referential_integrity.py`
| Campo | Detalle |
|---|---|
| **Tipo** | HTTP Validation Test (usa `httpx`) |
| **Requiere DB** | ❌ No directo |
| **Requiere Docker** | ✅ Sí |
| **Estado actual** | ✅ Coleccionado. Pasa trivialmente (assertions en prints). |
| **Qué valida** | Que el servicio rechaza movimientos con `product_id` inexistente |
| **Cuándo usar** | 🟡 Validación de integración tras cambios en endpoint de transacciones. |

---

### ❌ `test_variant_search.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script |
| **Requiere DB** | ✅ Sí — busca SKU `MAT-001`, Marca `Alcoa`, MPN `AL-6061` en DB real |
| **Estado actual** | ❌ COLLECTION ERROR (PYTHONPATH) |
| **Qué valida** | `SQLAlchemyInventoryRepository.search_items_and_variants()` |
| **Cuándo usar** | 🟡 Solo si se modifica lógica de búsqueda. Correr como script manual. |

---

### ❌ `test_worker.py`
| Campo | Detalle |
|---|---|
| **Tipo** | Integration Script |
| **Requiere DB** | ✅ Sí — inserta `BackflushError` |
| **Estado actual** | ❌ COLLECTION ERROR — importa `async_session_factory` y `ReconciliationWorker` (MES futuro) |
| **Qué valida** | `ReconciliationWorker` — reintento de errores MES backflush |
| **Cuándo usar** | 🔴 No usar. Funcionalidad MES pendiente de implementar. |

---

## 📁 `scripts/` — Utilidades de Desarrollo (NO son pytest)

> **Todos los scripts usan `app.db.session` directamente.**
> **Comando tipo:** `docker exec inventory-service-api python scripts/<nombre>.py`

---

### 🌊 `scripts/flows/` — Core Flow Valdations
> Scripts modulares que simulan el ciclo de vida real en producción de cada tipo de movimiento. Inyectan `external_reference` con UUIDs dinámicos para cumplir la integridad `UNIQUE`.

| Flow Script | Detalle y Caso de Uso |
|---|---|
| `flow_1_entry.py` | ✅ **Entrada Manual**: Ingreso simple al almacén destino validando costeo y WAC inicial. Crea `IN-MANUAL`. |
| `flow_2_exit.py` | ✅ **Salida Manual**: Descarga de inventario directa. Crea `OUT-MANUAL`. |
| `flow_3_internal_transfer.py` | ✅ **Transferencia Interna**: Movimiento entre dos almacenes de la *Misma Empresa* (`origin_company_id == destination_company_id`). Requiere bypass temporal de SoD en Testing. |
| `flow_4_ict_enterprise_to_logistics.py` | ✅ **ICT Nacional**: Empresa B despacha a Empresa A en el mismo país sin aduanas. |
| `flow_5_ict_binational.py` | ✅ **ICT Binacional**: Traspaso transfronterizo completo. Exige Pedimento. Deja status financiero pendiente para el cierre de mes de `mes_service`. |

---

### 🌱 `seed_ict_real.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Siembra almacenes TIJ/SDY, stock de MAT-001, documentos ICT con folio `ICT-REAL-*`. Modificado para usar doble mirror `external_reference` (`OUT-{id}` & `IN-{id}`). |
| **Requiere** | DB real con tablas creadas. Corre después de `master_seed.py`. |
| **UUIDs** | `CO_LOGISTICS_ID`, `CO_ENTERPRISE_ID`, `CHARLY_ID`, `WH_TIJ_ID`, `WH_SDY_ID` |
| **Cuándo usar** | ✅ Pre-requisito obligatorio para poblar el Dashboard de ICT y preparar E2E. |

---

### 🧪 `test_full_ict_cycle.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Ciclo ICT completo de 3 empresas: Enterprise TJ → Logistics MX → Logistics US (SoD: 3 usuarios distintos) |
| **Requiere** | DB con seed ejecutado. Pedimento `244030001234567`. |
| **Cuándo usar** | ✅ Prueba de regresión E2E más completa del flujo binacional real. |
| **Comando** | `docker exec inventory-service-api python scripts/test_full_ict_cycle.py` |

---

### 🔍 `validate_mirror_ict.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Test E2E via HTTP: login → select-company → dispatch ICT → verifica documento espejo en Empresa B |
| **Requiere** | **Todos los servicios corriendo** (auth en 8001, inventory en 8006, master-data en 8003) |
| **Cuándo usar** | 🟡 Validación E2E completa. Requiere cluster completo funcional. |

---

### 📊 `verify_dashboard_api.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Inserta `Movement` records con fechas variadas, verifica filtrado del dashboard (últimas 24h, multi-tenant) |
| **Cuándo usar** | 🟡 Cuando se modifique `get_dashboard_summary` en el repository. |

---

### 🔒 `verify_forensic_audit.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Verifica que el listener SQLAlchemy bloquee UPDATE/DELETE en `Movement` (inmutabilidad del kardex) |
| **Cuándo usar** | 🟡 Si se modifica el sistema de audit listeners (`app.core.events`). |

---

### 💰 `verify_sealed_price.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Verifica el "Precio Sellado": que el precio dispatch no cambie al hacer receipt aunque cambie el WAC |
| **Cuándo usar** | 🟡 Tras cambios en `TransferCommandHandler.complete_transfer()`. |

---

### ✔️ `verify_seed.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Quick check: cuenta variants y movements en DB, verifica stock de MAT-001 en WH-TIJ |
| **Cuándo usar** | ✅ Diagnóstico rápido post-seed. |
| **Comando** | `docker exec inventory-service-api python scripts/verify_seed.py` |

---

### 📦 `verify_wac_integrity.py`
| Campo | Detalle |
|---|---|
| **Qué hace** | Audita WAC de MAT-001 en WH-SDY (Empresa B). Espera 150u @ $20.00 (mezcla 50@10 + 100@25) |
| **Cuándo usar** | ✅ Post-ICT cycle para confirmar integridad financiera. |

---

### ⚙️ `transit_worker.py` *(NO es test, es servicio background)*
| Campo | Detalle |
|---|---|
| **Qué hace** | Worker que escanea movimientos en tránsito y genera alertas/tickets en SLA 24h/48h |
| **Cuándo usar** | 🔴 No es un script de prueba. Activar solo cuando `tickets_service` esté integrado. |

---

## 📋 Resumen Ejecutivo

| # | Archivo | Tipo | Pytest OK? | Estado | Prioridad |
|---|---------|------|:---:|--------|-----------|
| 1 | `tests/test_ict_binational.py` | Unit (mock) | ✅ | ✅ 2/2 | 🔴 Siempre correr |
| 2 | `tests/test_concurrency.py` | HTTP stress | ✅ | ✅ trivial | 🟡 Solo stress test |
| 3 | `tests/test_referential_integrity.py` | HTTP | ✅ | ✅ trivial | 🟡 Validación HTTP |
| 4 | `tests/test_financial_regression.py` | Integration | ❌ | ❌ Legado | 🔴 Refactorizar |
| 5 | `tests/test_zero_trust_warehouse.py` | Integration | ❌ | ❌ PYTHONPATH | 🟡 Correr como script |
| 6 | `tests/test_intercompany_flow.py` | Integration | ❌ | ❌ PYTHONPATH | 🟡 Correr como script |
| 7 | `tests/test_fifo_report.py` | Integration | ❌ | ❌ PYTHONPATH | 🟡 Solo cambios FIFO |
| 8 | `tests/test_variant_search.py` | Integration | ❌ | ❌ PYTHONPATH | 🟡 Solo cambios búsqueda |
| 9 | `tests/test_worker.py` | Integration | ❌ | ❌ MES Futuro | 🔴 No usar |
| 10 | `scripts/seed_ict_real.py` | Seed | N/A | ✅ | ✅ Pre-requisito E2E |
| 11 | `scripts/test_full_ict_cycle.py` | E2E DB | N/A | ✅ | ✅ Test regresión E2E |
| 12 | `scripts/validate_mirror_ict.py` | E2E HTTP | N/A | ✅ | 🟡 Cluster completo |
| 13 | `scripts/verify_seed.py` | Diagnóstico | N/A | ✅ | ✅ Quick check |
| 14 | `scripts/verify_wac_integrity.py` | Diagnóstico | N/A | ✅ | ✅ Post-ICT check |
| 15 | `scripts/verify_dashboard_api.py` | Diagnóstico | N/A | 🟡 | 🟡 Dashboard changes |
| 16 | `scripts/verify_forensic_audit.py` | Diagnóstico | N/A | 🟡 | 🟡 Audit changes |
| 17 | `scripts/verify_sealed_price.py` | Diagnóstico | N/A | 🟡 | 🟡 Pricing changes |
| 18 | `scripts/transit_worker.py` | Worker | N/A | 🔴 Futuro | 🔴 No usar |

---

## ⚡ Comandos del Día a Día

```bash
# El único pytest que siempre debe pasar
docker exec inventory-service-api python -m pytest tests/test_ict_binational.py -v

# Diagnóstico rápido de datos post-seed
docker exec inventory-service-api python scripts/verify_seed.py

# Ciclo ICT completo (necesita seed previo)
docker exec inventory-service-api python scripts/seed_ict_real.py
docker exec inventory-service-api python scripts/test_full_ict_cycle.py

# Verificación financiera post-ICT
docker exec inventory-service-api python scripts/verify_wac_integrity.py

# E2E con cluster completo
docker exec inventory-service-api python scripts/validate_mirror_ict.py
```

---

## 🔧 Fix Rápido — Tests con Error PYTHONPATH

Los tests de integración fallan porque pytest no agrega el raíz del servicio al path.
**Solución:** Crear `tests/conftest.py`:

```python
# tests/conftest.py
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
```

**Antes de eso:** `test_financial_regression.py` importa `TransferService` (eliminado).
Necesita actualizarse a `TransferCommandHandler` antes de ser útil.

---

*Generado: 2026-04-03 | inventory_service — Fase 41.5*
