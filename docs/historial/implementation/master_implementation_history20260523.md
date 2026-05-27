# Historial Maestro de Implementación: 2026-05-23

Jornada de auditoría estratégica y documentación. Phase 129.

---

## 1. Auditoría Landing Page vs Plan Operativo (Phase 129)

### Metodología
Cruce de `src/landing/index.html` + `src/landing/plans.html` contra historial de implementación
(2026-05-21 a 2026-05-22) y CLAUDE.md sección 13 (Deuda Técnica).

### Hallazgos por Módulo

| Módulo | Prometido en Landing | Estado Real | Gap |
|---|---|---|---|
| **Auth & Security** | Zero-Trust, RBAC, RTR | ✅ Completo | Ninguno |
| **Master Data** | SSOT, sin duplicidad | ✅ Completo | Ninguno |
| **Inventory** | Kardex, FIFO, Density Guard | ✅ Completo | Flows 1-9 validados |
| **Subscription** | Stripe, bloqueos L7 | ✅ Completo | Self-service checkout pendiente |
| **HCM Identity** | RFID/PIN, certificaciones, TRESS sync | ⚠️ Parcial | Certifications UI + TRESS no implementados |
| **Notifications / ANDON** | WhatsApp, SMS, pantallas industriales | ⚠️ Parcial | ANDON real-time, SMS sin canal activo |
| **MES Engine** | OEE, work orders, producción en piso | ❌ Pendiente | Carpeta existe, nginx no desplegado |
| **WMS Logistics** | Pull System, Density Guard avanzado | ❌ Pendiente | Carpeta existe, nginx no desplegado |
| **CMMS Assets** | Mantenimiento preventivo, ToolCrips | ❌ Pendiente | Sin arquitectura activa |

### Features No Comunicados en Landing (gap de marketing)

- **Flutter INTERNO POS** — App nativa Android con QR provisioning y carrito industrial
- **Price Agreements B2B** — Contratos con partners, resolución multi-capa (Phase 44)
- **Soft-Close Pricing** — Historial inmutable de precios, point-in-time (Phase 119)
- **RFID Dual-Hash O(1)** — Autenticación biométrica industrial (Phase 39)
- **Multi-tenant RLS** — Postgres row-level security por tenant (Phase 35)
- **Currency SSOT** — Banxico FIX + Frankfurter fallback (CLAUDE.md)

### Decisiones ADR derivadas de la auditoría

**ADR-04: Despliegue MES/WMS priorizados en siguiente sprint**
- Contexto: Landing promete Plan Industrial con MES y WMS. Ambos servicios existen en `backend/` pero están comentados en nginx.conf upstream.
- Decisión: Activar `mes_service` y `wms_service` en nginx en próxima fase, comenzando con endpoints de salud + rutas básicas.
- Consecuencia: Habilita ventas del Plan Industrial ($350/mes).

**ADR-05: CMMS como módulo de MES (no servicio independiente)**
- Contexto: `cmms_service/` existe pero vacío. Crear un microservicio completo es costoso.
- Decisión: Implementar CMMS como módulo (`/api/v1/production/maintenance`) dentro de `mes_service`.
- Consecuencia: Reduce overhead de infraestructura, acelera entrega.

---

## 2. How-To WhatsApp (referencia consolidada)

### Documentos existentes (ya creados)
- `docs/howto/whatsapp_pairing_and_notifications.md` — Pairing + test-send (Phase 124)
- `docs/howto/whatsapp_group_setup.md` — Descubrimiento de grupos + mappings (Phase 128)

### Stack verificado en producción dev
```
Angular /admin/whatsapp  
→ Nginx :8000 /api/v1/whatsapp/*  
→ notification_service :8009 (whatsapp_routes.py — ADR-02 JWT Iron Wall)  
→ whatsapp-gateway :3011 (Node.js Singleton + CompanyQueue 1.5-3s anti-ban)  
→ WhatsApp Web (sesión en volumen docker_whatsapp_sessions_dev)
```

### Endpoint de prueba activo
`POST /api/v1/whatsapp/test-send` — requiere JWT admin, acepta `{ to, message }`.
Número real de prueba: `+526641667684` (normalizado → `526641667684@c.us`).

---

## 3. Estado Final Phase 129

| Check | Resultado |
|---|---|
| Auditoría landing completa | ✅ 9 módulos evaluados |
| ADR-04 y ADR-05 registrados | ✅ Backlog priorizado |
| How-To WhatsApp existente | ✅ `docs/howto/` — 2 documentos |
| Consolidated tasks creado | ✅ `consolidated_tasks20260523.md` |
| REPO_LOG actualizado | ✅ Phase 129 entrada añadida |
