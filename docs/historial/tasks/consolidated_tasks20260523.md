# Consolidado de Tareas: 2026-05-23

Jornada de auditoría estratégica: Phase 129 — Landing vs Operativo + How-To WhatsApp Reference.

---

## Phase 129 — Auditoría Landing Page vs Plan Operativo ✅ COMPLETADO

### Auditoría Cruzada

- `[x]` Revisión completa de `src/landing/index.html` y `src/landing/plans.html`
- `[x]` Cruce con historial de fases (20260521–20260522) y CLAUDE.md sección 13
- `[x]` Identificación de gaps entre lo prometido en landing y lo implementado
- `[x]` Elaboración de tabla de estado por módulo (✅ / ⚠️ / ❌)

### Estado de Módulos (resultado de auditoría)

| Módulo | Estado | Notas |
|---|---|---|
| Auth & Security | ✅ Implementado | T1/T2, RTR, RFID/PIN, God Mode |
| Master Data | ✅ Implementado | SSOT, Pricing Matrix, lookup POS |
| Inventory (Kardex) | ✅ Implementado | Flows 1-9 validados, Density Guard |
| Subscription / Billing | ✅ Implementado | Stripe, PAST_DUE readonly, entitlements |
| HCM Identity | ⚠️ Parcial | RFID/PIN OK · Certifications UI pendiente |
| Notifications / WhatsApp | ⚠️ Parcial | Email + WhatsApp canal local ✅ · ANDON industrial pendiente |
| MES Engine | ❌ Pendiente | Carpeta existe, no desplegado en nginx |
| WMS Logistics | ❌ Pendiente | Carpeta existe, no desplegado en nginx |
| CMMS Assets | ❌ Pendiente | Sin arquitectura activa |

### Prioridades Derivadas (backlog)

- `[ ]` **P1 — Activar MES en nginx**: desplegar `mes_service` + rutas `/api/v1/production/*` (Plan Industrial lo promete)
- `[ ]` **P1 — Activar WMS en nginx**: desplegar `wms_service` + rutas `/api/v1/warehouse/*` (diferenciador aduanero)
- `[ ]` **P2 — Bootstrap CMMS**: decisión arquitectónica — ¿servicio propio o módulo de MES?
- `[ ]` **P2 — Certificaciones HCM**: endpoints `/api/v1/collaborators/{id}/certifications`
- `[ ]` **P3 — ANDON industrial**: pantallas WebSocket tiempo real para piso de planta
- `[ ]` **P3 — Landing: agregar Flutter POS**: producto real no comunicado (diferenciador)
- `[ ]` **P3 — Landing: agregar Price Agreements B2B**: funcionalidad no comunicada

---

## How-To WhatsApp (referencia)

- `[x]` How-To completo en `docs/howto/whatsapp_pairing_and_notifications.md` — creado Phase 124
- `[x]` How-To de grupos en `docs/howto/whatsapp_group_setup.md` — creado Phase 128
- `[x]` Endpoint `POST /api/v1/whatsapp/test-send` activo en notification_service
- `[x]` Sesión WhatsApp conectada — grupo `ALERTAS_INTERNO` registrado (Phase 128)

---

## Pendientes Acumulados (cross-phase)

- `[ ]` Agregar `+526641667684` al seed `unified_industrial_seed.py` para `charly@interno.com`
- `[ ]` Fix `GET /products/{id}/variants` 403 para rol `collaborator` — agregar `inventory:read` en `select_company_command.py`
- `[ ]` Rate limiting en endpoints de `subscription_service` y `master_data_service`
- `[ ]` `default_tax_rate` Planta US = 0.0 (actualmente 0.16)
- `[ ]` `POST /api/v1/pos/checkout` validación end-to-end con flows antigravity
