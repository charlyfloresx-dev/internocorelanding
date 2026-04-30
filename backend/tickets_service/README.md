# 🎫 Tickets Service (Puerto 8004)

El **Tickets Service** gestiona el **sistema de incidencias y soporte** de Interno Core. Permite a los colaboradores reportar fallas, solicitar asistencia técnica y dar seguimiento a la resolución de problemas dentro de la plataforma.

---

## 🏗️ Responsabilidades del Dominio

- **Creación de Tickets**: Reporte de incidencias con categoría, prioridad y evidencia adjunta.
- **Asignación y Escalamiento**: Routing automático al equipo responsable según categoría y SLA.
- **Estado del Ciclo de Vida**: `OPEN → IN_PROGRESS → RESOLVED → CLOSED`.
- **SLA Tracking**: Monitoreo de tiempos de respuesta y resolución con alertas de incumplimiento.
- **Historial de Interacciones**: Log completo de comentarios, reasignaciones y cambios de estado.
- **Multi-Tenant**: Cada ticket está aislado por `company_id`.

---

## 🔗 Integraciones

| Servicio | Propósito |
|----------|-----------|
| **Notification** | Notifica al asignado y al reportante en cada cambio de estado |
| **Auth** | Valida JWT para identificar reportante y asignado |
| **CMMS** | Tickets de mantenimiento pueden convertirse en Órdenes de Trabajo |

---

## ⚙️ Variables de Entorno

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/tickets_db
CORE_SECRET_KEY=changeme
SECRET_KEY=changeme
CORE_INTERNAL_API_KEY=...
```
