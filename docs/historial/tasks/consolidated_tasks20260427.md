# Consolidated Tasks — 2026-04-27

## ✅ Tareas Completadas (Done)

### 📂 Backend
- [x] **Kardex Mapping Fix**: Corregido el conflicto de atributos `_amount` / `unit_price` en el modelo `Movement` de SQLAlchemy.
- [x] **Entity Enrichment**: Agregados campos `total_amount` y `currency` a las entidades de respuesta de inventario.
- [x] **Auditoría Forense (Ledger)**: Implementado el endpoint `/api/v1/audit/` para trazabilidad inmutable de transacciones.
- [x] **Notification Read-Status Fix**: Corregida la persistencia del estado de lectura mediante debugging de `rowcount` y validación de commit.
- [x] **AWS Readiness**: Eliminados strings de `localhost` en la configuración de servicios para cumplir con el Code Graph audit.

### 🎨 Frontend
- [x] **Audit Log Viewer**: Creado componente industrial para visualización de logs forenses.
- [x] **Financial Valuation UI**: Corregida la visualización de totales en el grid de documentos de inventario.
- [x] **Company Currency Config**: Añadido selector de moneda base en el flujo de onboarding.
- [x] **Main Layout Fix**: Reparada la integración del `NotificationHubService` y el panel de notificaciones.

## 🔄 Tareas en Progreso (In Progress)
- [ ] **Manual Notification Creation**: Validando scripts de prueba para asegurar que las notificaciones se creen correctamente desde el backend ante eventos asíncronos.
- [ ] **Financial Valuation Widget**: Diseñando el widget de "Pendientes de Valuación" para el Dashboard.

## 🟡 Pendientes (Backlog)
- [ ] Exportación de logs de auditoría a CSV/PDF para reportes externos.
- [ ] Configuración de alertas críticas vía email/SMS.

**Fecha**: 2026-04-27
