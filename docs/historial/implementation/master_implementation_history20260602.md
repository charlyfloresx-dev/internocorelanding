# Implementation History — 2026-06-02 (Phase 161 + Phase 167)

---

## Phase 167 — Landing v2 + Onboarding Wizard 8-Step

### Contexto
La landing page existente usaba un stock photo de Unsplash en el hero, referencias incorrectas a "SMK y Zodiac Aerospace" (en lugar del historial real), y el `onboarding.component.ts` tenía solo 3 pasos placeholder sin lógica real. Esta fase resuelve ambos puntos: rediseña la landing con patrones modernos de SaaS y construye el wizard completo de alta de empresa.

### Landing Page — Decisiones técnicas

#### motion@latest vía CDN (no framer-motion)
`framer-motion` es exclusivamente React. La landing es HTML vanilla sin build step. `motion` (mismo equipo de Framer, mismo engine subyacente) expone `window.Motion` con `animate`, `inView`, `stagger` desde CDN. Todos los fallbacks funcionan si CDN falla: las tarjetas tienen opacidad natural (el JS establece `opacity:[0,1]` como keyframe inicial, no CSS estático).

#### Dashboard Mockup en lugar de stock photo
El hero visual es un dashboard CSS/HTML con:
- KPIs animados (OEE%, WIP count) que fluctúan cada 4s via `setInterval`
- Barras de progreso con animación `@keyframes bar-grow` via CSS custom property `--w`
- Feed live que rota logs del audit stream (mismo formato que la sección Security)
- Perspectiva 3D via `perspective(1200px) rotateY(-8deg)` en hover

Ventaja: más relevante que una foto de planta genérica, demuestra el producto real.

#### CV real del arquitecto
Cambios del mock al dato real:
| Campo | Antes | Ahora |
|---|---|---|
| Empresas | "SMK y Zodiac Aerospace" | Safran Aerospace, DJO/Enovis, Outset Medical, SMK Electronics |
| Milestone 2 | Filosofía genérica | Outset Medical Clase III + DJO/Enovis sub-assembly routing |
| Skills | WMS & Pull Systems genérico | Trazabilidad FDA/AS9100 Serial·Lote·Caja·Validación por estación |
| Contacto | Sin | LinkedIn `cjfloresmontoya` + email real |
| Certs | Sin | Tulip Certified · Lean Six Sigma · AS9100 · ISO 9001 · ITT |

### Onboarding Wizard — Decisiones técnicas

#### Orden de pasos (dependencias de datos)
El orden de los 8 pasos respeta el grafo de dependencias del sistema:
```
Company (Auth) → Plan (Subscription) → Master Data (categorías+productos) → 
Partners (Master Data) → Warehouse (Inventory) → Collaborators (HCM) → 
Facility/MES → Notifications
```
No se puede crear un Warehouse sin Company; no se pueden asignar Collaborators sin Departments (auto-creados por seed). El wizard no puede saltar pasos críticos.

#### CSV bulk import — estrategia de error
Cada `await svc.method().catch(() => {})` — los errores de import masivo son **silenciados** intencionalmente. Razón: el usuario puede fallar en un campo y no queremos bloquear el wizard completo. El sistema continúa y el usuario puede importar de nuevo desde los catálogos individuales. Esta es una decisión de UX deliberada (onboarding ≠ data migration crítica).

#### CSV parser propio vs librerías
Se optó por un parser manual (44 líneas) en lugar de `papaparse` o similar. Razón: evitar una dependencia npm solo para el onboarding. El parser maneja el caso edge más común (campos con comas entre comillas) que es suficiente para los templates predefinidos que el sistema entrega.

#### Templates CSV con datos industriales reales
Los templates incluyen filas de ejemplo con productos reales (Cojinete SKF 6205, Aceite ISO 46), partners reales (Distribuidora SKF México, Ferretera Industrial TIJ) y empleados con RFID. Esto reduce drásticamente el tiempo de comprensión del formato — el usuario ve el patrón y puede adaptar su hoja de Excel directamente.

#### Pasos 7 y 8 skipeables
MES y Notifications tienen toggle "Omitir". Razón: el plan Operativo no incluye MES (sería confuso forzar esa pantalla). Notifications requiere credenciales Twilio que no todos tienen listas el día 1. Ambos están disponibles post-onboarding desde sus módulos respectivos.

### Archivos creados/modificados
```
src/landing/
  index.html                           ← Reescrito completo
  style.css                            ← Reescrito completo
  app.js                               ← Reescrito completo
  plans.html                           ← Reescrito completo
  ticket-access.html                   ← Reescrito completo
  locales/es.json                      ← Actualizado (DJO/Enovis, CTA, routing)
  locales/en.json                      ← Actualizado
  package.json                         ← Nuevo

frontend/src/app/
  core/services/onboarding.service.ts  ← Nuevo
  modules/auth/onboarding.component.ts ← Reescrito completo (3 pasos → 8 pasos)

CLAUDE.md                              ← Deuda ALTA "Landing Onboarding" agregada
REPO_LOG.md                            ← Phase 167 agregado
```

---

---

## Phase 161 — MES Labor Assignment Hardening & E2E Validation

### Objetivo
Estabilizar la suite de pruebas de asignación en masa de colaboradores a líneas/turnos de producción, resolver conflictos de concurrencia e integridad referencial y auditar el cumplimiento del Code Graph del repositorio.

### Decisiones Arquitectónicas

**1. Aislamiento e Integridad Referencial de Tests**
- Los tests de asignación anteriormente creaban registros de corridas de producción (`ProductionRun`) con llaves foráneas inventadas en `work_order_id` y `resource_id`. Con la activación del Muro de Hierro de Base de Datos y las FK reales de la base de datos PostgreSQL, esto violaba restricciones.
- Decisión: Instanciar explícitamente y de forma secuencial la jerarquía completa en el fixture de la base de datos (`Facility` -> `ProductionArea` -> `Resource` y `WorkOrder` con identificadores únicos basados en UUIDs) antes de insertar el `ProductionRun`.

**2. Bypass de Seguridad Seguro en Contextos de Integración**
- La API de asignación requiere autenticación JWT a través de la inyección de dependencias de FastAPI y el middleware `InternoCoreGlobalMiddleware`. Para evitar acoplamiento de infraestructura de claves y almacenamiento de Redis en pruebas puras de este endpoint de integración, se configuraron overrides locales.
- Mock de `get_current_active_user` retornando un payload con roles `OPERATOR` y permisos `mes:write` / `mes:read`, además del bypass mediante la cabecera `X-Admin-Master-Key` del middleware.

### Resultados
- Verificación del ecosistema: `validate_ecosystem.ps1` ejecutado con éxito total.
- 100% de éxito en tests de asignación (3 passed).
- Estado de cumplimiento general: 8 advertencias menores acumuladas en otras áreas (deuda técnica de `NAIVE_DATETIME_VIOLATION` pendiente en fases futuras).
