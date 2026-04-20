# Auditoría y Plan de Integración: Frontend Legacy → Frontend (Angular 19+)

## 🔍 Resultados de la Auditoría

### 1. Estado de Infraestructura Core
- **Handshake de 3 Pasos:** ✅ Implementado en el nuevo `AuthService` (T1/T2).
- **Zoneless Mode:** ✅ Activado globalmente en el nuevo `frontend`.
- **Gestión de Estado:** ✅ Migrado exitosamente a Angular Signals.
- **Multitenancy:** ✅ Interceptor unificado inyectando `X-Company-Id`.

### 2. Brechas Identificadas (Lo que falta en el nuevo Frontend)
- **Módulos Faltantes:**
  - `Production`: Dashboard OEE, Monitor de Línea, Registro de Paros.
  - `Onboarding`: Flujo de bienvenida para nuevos tenants (`is_new`).
  - `System`: Gestión de Snapshots y recuperación.
  - `Tickets`: Sistema de soporte integrado.
  - `Users`: Gestión delegada de usuarios por tenant.
- **Servicios Críticos Ausentes:**
  - `SystemHealthService`: El "pulso" de la UI y el bloqueo de escritura (`isReadOnly`).
  - `PrintService`: Centralización de lógica de tickets y etiquetas térmicas.
  - `OnboardingService`: Orquestación del wizard inicial.
  - `DiagnosticLogService`: Telemetría forense para depuración en planta.

### 3. Diferencias en Lógica de Negocio
- **Identidad Triple:** El legado tiene una implementación estricta de `UUID / Secuencia / Folio`. El nuevo frontend requiere asegurar que todas las tablas de inventario y producción respeten esta jerarquía.
- **Modo Offline-First:** El legado implementó un sistema de caché en `localStorage` para `MasterData` y `WMS` que permite lectura sin conexión. El nuevo frontend aún no lo tiene.

---

## 🚀 Plan de Implementación (Fases)

### Fase 1: Cimientos y Telemetría (Inmediato)
1.  **Portar `SystemHealthService`:** Implementar el monitoreo de microservicios y el signal global `isReadOnly`.
2.  **Integrar `HealthBadge`:** Añadir el indicador visual de salud en el `HeaderComponent`.
3.  **Sincronizar `domain.types.ts`:** Asegurar paridad total de interfaces entre legacy y new.

### Fase 2: Módulo de Producción (Core MES)
1.  **Migrar `ProductionService`:** Adaptar la lógica de `production-data.service.ts` (Legacy) al nuevo estándar, conectando con las APIs reales de producción.
2.  **Dashboard OEE:** Portar los componentes de gráficas (Pareto, Tendencias) y KPIs.
3.  **Monitor de Línea:** Integrar la vista real-time de órdenes de trabajo y escaneo QR.

### Fase 3: Identidad y Onboarding
1.  **Flujo T3 (Onboarding):** Implementar el guard y el componente de bienvenida cuando `is_new === true`.
2.  **Gestión de Usuarios:** Portar la UI de invitación y roles por empresa.

### Fase 4: Refinamiento Industrial
1.  **Identidad Triple:** Revisar componentes de inventario para mostrar `Folio` como label principal y `Secuencia` en tablas.
2.  **Lock de Escritura:** Aplicar `[readonly]` o `disabled` basado en el estado del documento (`CONFIRMED`) y el estado del sistema (`isReadOnly`).
3.  **Print Engine:** Unificar la lógica de impresión en un servicio compartido.

---

## 🛠 Directrices de Migración
- **Zero Simulation:** Todo componente migrado debe conectarse a `HttpClient` directamente, usando el `AuthService` para el contexto.
- **Pure Signals:** Queda prohibido el uso de `Subject/BehaviorSubject` del legado; todo debe ser `signal` o `computed`.
- **Nginx Ready:** Asegurar que todo ruteo funcione con `HashLocationStrategy` para evitar 404s en el contenedor Docker.
