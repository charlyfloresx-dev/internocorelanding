# 📋 PENDIENTES — Resumen Ejecutivo (2026-06-03)

**Principio:** `best-effort` — Nada bloquea piso. Todo alerta/loguea para reconciliación.

---

## 🟢 COMPLETADAS (Semana 1)

| # | Tarea | Est. | Status | Fecha |
|---|-------|------|--------|-------|
| ✅ 1 | RTR Phase D — Integración Login | 1h | COMPLETADO | 2026-06-03 |

## 🔴 CRÍTICAS PENDIENTES (Semana 1)

| # | Tarea | Est. | Bloqueador | Acción |
|---|-------|------|-----------|--------|
| 2 | POS Checkout E2E Validation | 2h | inventory_service estable | Ejecutar `flow_pos_checkout.py` completo |
| 3 | Shift-End Auto-Logout (Labor) | 3h | APScheduler setup | Cron job + LaborDensityService.materialize_range() |
| 4 | Headcount Recompute (HCM→MES) | 2.5h | outbox pattern | PermissionDocumentPosted → MES recompute |
| 5 | NAIVE_DATETIME Fixes (10 instances) | 0.5h | identificadas | Replace `datetime.utcnow()` → `datetime.now(timezone.utc)` |
| | **SUBTOTAL SEMANA 1 PENDIENTE** | **~8.5h** | | |

---

## 🟠 OPERACIONALES (Próximas 4-12 semanas)

### A. HCM KARDEX (Phase 161+) — 42h total
| Phase | Tarea | Est. | PRs | Inicio |
|-------|-------|------|-----|--------|
| 2 | Competencias (Position, Skill, Certification) | 7.5h | 4 | Semana 3 |
| 3 | Kardex Transaccional (Documento, Evento, Elegibilidad) | 22h | 9 | Semana 5 |
| 4 | T&A Advanced (TimeRecord, WorkCalendar) | 4.5h | 2 | Semana 8 |
| 5 | Seguridad (Medical, PPE) | 4h | 2 | Semana 8 |
| 6 | Reporting | 2h | 1 | Semana 9 |

**Principio:** Kardex es validación, NO bloqueo. Si falla → log + continuar.

---

### B. Integraciones Cross-Service — 1.5h
| Tarea | Est. | Ubicación | Fallback |
|-------|------|-----------|----------|
| Master Data Clients (HCM, MES, WMS) | 1.5h | 3 servicios | Cache + timeout 3s |

**Principio:** Si master_data DOWN → usar cache. Log warning.

---

## 🟡 INFRASTRUCTURE & CLOUD (Semanas 10-12)

| Tarea | Est. | Criterio de Éxito |
|-------|------|-------------------|
| AWS WAF Configuration (RTR) | 2h | Bloquear >20 req/min |
| Observability Alerts (Grafana) | 1.5h | Alert si breach reuse >3x/5min |
| Cloud Deployment (Phase 180) | 6-8h | ECS + RDS + load test 1000 users |

---

## 🔵 TECH DEBT (Puede Esperar)

| Tarea | Est. | Impacto |
|-------|------|--------|
| Domain Purity Refactor (RTR) | 1h | Código limpio |
| WMS Service Deployment | 1.5h | Preparación |
| Mobile AVD E2E Testing | 2h | Validación |
| Price Agreement Context | 1h | Búsqueda mejorada |
| MES Routing Model | 3h | Feature futura |
| MES Metrics Completeness | 2h | Analytics |
| MES Tracking | 2h | Incidencia management |
| MES Enum Migration | 2h | Configurabilidad |
| Stripe Self-Service Checkout | 3h | Monetización |
| Mobile Offline Buffer (SQLite) | 5h | Resiliencia |

**Total Tech Debt:** ~22.5h

---

## 📊 Totales

```
CRÍTICAS BLOQUEADAS:     9h
OPERACIONALES (HCM):    42h
INTEGRACIONES:          1.5h
INFRASTRUCTURE:         9.5-11.5h
TECH DEBT:             22.5h
───────────────────────────
TOTAL:                ~84h (10-12 semanas @ 8h/semana)
```

---

## 🎯 PRÓXIMOS 7 DÍAS

| Día | Tarea | Est. | Dueño |
|-----|-------|------|-------|
| **Hoy** | RTR Phase D validation | 1h | Tech Lead |
| **Mañana** | POS Checkout E2E script | 2h | Inventory Arch |
| **Miércoles** | NAIVE_DATETIME fixes | 0.5h | Sonnet |
| **Jueves** | Shift-End Auto-Logout | 3h | MES Arch |
| **Viernes** | Headcount recompute | 2.5h | MES Arch |
| **Semana Siguiente** | HCM Phase 2 kick-off | 7.5h | HCM Lead |

---

## ✅ "Best-Effort" Pattern — Regla de Oro

```
OPERACIÓN CRÍTICA (Escaneo, Movimiento, Orden)
    │
    ├─ Intenta validación/integración
    │
    ├─ SI FALLA:
    │  ├─ LOG CRITICAL con contexto completo
    │  ├─ NOTIFICA admin/operador
    │  ├─ RETORNA: {"status": "created", "warning": "reconcile needed"}
    │  └─ ✅ CONTINÚA (no bloquea piso)
    │
    └─ SI ÉXITO: ✅ PROCEDE normalmente

NUNCA JAMÁS:
  ❌ raise Exception()  # en validación crítica
  ❌ abort operación    # por falta de dependencia
  ❌ silenciar errores  # log siempre
```

---

## 🚀 Estado Cloud Readiness

```
✅ Código: 0 CRITICAL violations (Code Graph)
✅ Timezone: UTC-aware (Phase 177)
✅ RTR: Stateless (Phase 159 A+B)
⏳ RTR Integración: Phase D pending
⏳ AWS WAF: pending
⏳ RDS Migration Scripts: pending
⏳ Secrets Management: pending
⏳ Load Testing: pending
```

**Estimado Go-Live:** Semana 12 (si todo en tiempo)

---

**Generado:** 2026-06-03  
**Próxima Revisión:** EOD Viernes (validaciones críticas completadas)
