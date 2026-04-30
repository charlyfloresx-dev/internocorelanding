# 👥 HCM Service — Human Capital Management (Puerto 8009)

El **HCM Service** es el **motor de validación de capacidades humanas** del ecosistema Interno Core. No es un simple archivo de empleados: es el servicio que determina quién puede operar qué máquina, en qué turno y con qué certificación vigente. Actúa como el **"Gatekeeper" del factor humano** para el MES, CMMS y ERP.

> **Rename Log:** Este servicio fue previamente conocido como `hr_service`. Renombrado a `hcm_service` (2026-04-30) para reflejar su rol como **Human Capital Management** bajo la arquitectura industrial de Interno Core.

---

## 🏗️ Arquitectura del Dominio

El HCM se divide en 4 dominios funcionales, implementados en fases:

### Fase 1 — Identidad y Estructura Organizacional
Gestión de la entidad **Collaborator** (sustituyendo el término "Operador") con soporte pleno de Multitenancy. Cada colaborador existe dentro de un `company_id` y puede pertenecer a múltiples empresas a través del Auth Service.

- **Collaborator**: Entidad central. Hereda `MultiTenantBase` + `AuditBase`. Referencia `user_id` del Auth Service.
- **Department**: Área organizacional por empresa.
- **Position**: Puesto de trabajo. Define los `Skills` requeridos para desempeñar el rol.
- **ContractType**: Tipos de contrato (Indefinido, Temporal, Subcontratado).

### Fase 2 — Motor de Competencias (Skills Engine)
El HCM se convierte en el **"Gatekeeper"** de la operación industrial. El MES y el CMMS consultan este servicio antes de permitir que un colaborador inicie una tarea de alto riesgo o una Orden de Producción.

- **Skill**: Catálogo de habilidades (Operación Torno CNC, Soldadura MIG, etc.) con nivel `TRAINEE → EXPERT`.
- **CollaboratorSkill**: Nivel actual del colaborador en cada skill.
- **Certification**: Certificaciones formales con `issued_at` / `expires_at` y alertas de vencimiento.
- **TrainingRecord (Kardex)**: Historial de cursos y horas acumuladas ("Horas de Vuelo").

**API Interna crítica (SLA < 100ms):**
```
GET /internal/validate-access/{collaborator_id}/{skill_required}
→ { is_valid: bool, reason: str, expires_at: datetime | null }
```

### Fase 3 — Control de Tiempo y Disponibilidad (T&A)
El HCM alimenta al ERP y a la planeación de producción con datos de disponibilidad en tiempo real.

- **Shift**: Definición de turnos (matutino, vespertino, nocturno, rotativo).
- **ShiftAssignment**: Asignación colaborador-turno por período.
- **TimeRecord**: Entradas/Salidas desde scanner RFID o biométrico WebAuthn.
- **WorkCalendar**: Días hábiles, festivos y paros programados por planta.

**API de planeación para el MES:**
```
GET /internal/man-hours?line_id={id}&date={YYYY-MM-DD}
→ { available_hours: float, collaborators: int, by_shift: [...] }
```

**Integración con Industrial Scanner:**
- Endpoint `POST /clock-in` y `POST /clock-out` para lectores RFID.
- Salt de seguridad: `CORE_HCM_RFID_SALT` para hashing de IDs de tarjeta.

### Fase 4 — Seguridad, EHS y Domain Events
Implementación de **Zero Trust** para datos médicos y arquitectura **Event-Driven** para limpieza automática de procesos operativos.

- **MedicalRecord**: Expediente médico bajo protocolo Zero Trust. Solo accesible con rol `MEDICAL_STAFF`.
- **PPERecord**: Registro de entrega de Equipo de Protección Personal por puesto. El costo se carga al centro de costos en el ERP.

**Domain Events:**

| Evento | Suscriptores |
|--------|-------------|
| `CollaboratorStatusChanged(INACTIVE)` | MES desasigna estación; CMMS reasigna OT pendientes |
| `CertificationExpired` | Notification Service → alerta a supervisor y colaborador |
| `NewCollaboratorOnboarded` | Auth Service → crea `UserCompanyRole` |
| `PPEDelivered` | ERP → genera línea de costo en el centro de costos del puesto |

---

## 🔗 Integraciones con el Ecosistema

| Servicio | Dirección | Propósito |
|----------|-----------|-----------|
| **Auth Service** | HCM ← Auth | Obtiene `user_id` para vincular al Collaborator |
| **MES** | MES → HCM | Valida `SkillLevel` antes de iniciar una Orden de Producción |
| **CMMS** | CMMS → HCM | Valida `AccessPermit` antes de asignar una Orden de Mantenimiento |
| **ERP** | HCM → ERP | Envía costos de mano de obra (`Money VO`) y cargos de EPP |
| **Notification Service** | HCM → Notif. | Dispara alertas de vencimiento de certificaciones |

---

## ⚙️ Variables de Entorno Requeridas

```env
DATABASE_URL=postgresql+asyncpg://user:password@postgres-db:5432/hcm_db
CORE_SECRET_KEY=...
CORE_INTERNAL_API_KEY=...
CORE_HCM_RFID_SALT=...  # Salt para hashing de tarjetas RFID del checador
PYTHONPATH=/app
```

---

## 🗄️ Base de Datos

- **DB Name:** `hcm_db` (aislada de `auth_db` y demás servicios)
- **ORM:** SQLAlchemy Async
- **Migrations:** Alembic

---

## 🏭 Ecosistema Interno Core

| Módulo | Dominio |
|--------|---------|
| CRM | Clientes |
| ERP | Finanzas y Compras |
| MES | Ejecución en Piso |
| WMS | Inventario y Almacén |
| QMS | Calidad |
| CMMS | Mantenimiento |
| **HCM** ← *Este servicio* | **El Factor Humano y sus Competencias** |
