# HCM Service — Human Capital Management (Interno Core)

> **Contexto:** El HCM reemplaza al `hr_service`. No es un "archivo de empleados"; es el **motor de validación de capacidades** del ecosistema industrial. Determina quién puede tocar qué máquina, en qué turno, con qué certificación vigente.

---

## Ecosistema Interno Core

| Módulo | Dominio |
|--------|---------|
| CRM | Clientes |
| ERP | Finanzas y Compras |
| MES | Ejecución en Piso |
| WMS | Inventario y Almacén |
| QMS | Calidad |
| CMMS | Mantenimiento |
| **HCM** | **El Factor Humano y sus Competencias** |

---

## Especificación Técnica General

```
El módulo HCM es el proveedor de "Atributos de Capacidad" para el resto del sistema.

- CollaboratorService expone API interna para que MES/CMMS validen si un empleado
  tiene AccessPermit y SkillLevel necesario antes de iniciar una tarea.
- ShiftService informa al módulo de Planeación cuántas Man-Hours hay disponibles
  por línea de producción en un día específico.
- Cada cambio en el estatus del colaborador (baja/incapacidad) dispara un
  Domain Event que limpia asignaciones pendientes en Órdenes de Trabajo.
```

---

## Fase 1: Identidad y Refactorización de Dominio (Core)

**Objetivo:** Migrar del concepto "RRHH" a una estructura robusta de Capital Humano compatible con Multitenancy.

### Entidades principales

- [ ] **Collaborator** (reemplaza a `Operator`): Hereda `MultiTenantBase` + `AuditBase`. `company_id` obligatorio en todas las transacciones.
- [ ] **Department**: Entidad maestra multitenant. Define el área organizacional.
- [ ] **Position**: Puesto de trabajo. Vinculado a `Department` y a la **Matriz de Skills requerida**.
- [ ] **ContractType**: Tipos de contrato (Indefinido, Temporal, Subcontratado).

### Value Objects

- [ ] `Address` (para domicilio del colaborador)
- [ ] `Money` (salario con moneda/frecuencia, integra con ERP)
- [ ] `SkillLevel` (enum: `TRAINEE`, `JUNIOR`, `MID`, `SENIOR`, `EXPERT`)

### Integración con Auth Service

- El `Collaborator` referencia `user_id` del `auth_service` vía FK conceptual (sin acoplamiento de modelo SQLAlchemy).
- La vinculación multitenant se establece mediante `company_id` en ambos servicios.

---

## Fase 2: Motor de Competencias y Validación (Skills Engine)

**Objetivo:** Convertir al HCM en el "Gatekeeper" de la operación industrial.

### Entidades

- [ ] **Skill**: Catálogo de habilidades industriales (Operación Torno CNC, Soldadura MIG, etc.)
- [ ] **CollaboratorSkill**: Asociación Collaborator ↔ Skill con nivel actual y fecha de última evaluación.
- [ ] **Certification**: Certificaciones formales con `issued_at` y `expires_at`.
- [ ] **TrainingRecord**: Kardex de capacitación — cursos, horas acumuladas.

### API Interna (para MES y CMMS)

```
GET  /internal/validate-access/{collaborator_id}/{skill_required}
     → { is_valid: bool, reason: str, expires_at: datetime | null }
     → SLA: < 100ms
```

### Alertas de Vencimiento

- [ ] Lógica cron que detecte certificaciones a vencer en los próximos 30 días.
- [ ] Disparo de evento hacia `notification_service` para alertas proactivas.

---

## Fase 3: Control de Disponibilidad y Tiempo (T&A)

**Objetivo:** Alimentar al ERP y a la planeación de producción con datos de disponibilidad en tiempo real.

### Entidades

- [ ] **Shift**: Definición de turno (matutino, vespertino, nocturno, rotativo).
- [ ] **ShiftAssignment**: Asignación de colaborador a turno por período.
- [ ] **TimeRecord**: Entrada/Salida. Fuente: scanner industrial o WebAuthn biométrico.
- [ ] **WorkCalendar**: Calendario de días hábiles, festivos y paros programados por planta.

### ShiftService — API de Planeación

```
GET /internal/man-hours?line_id={id}&date={date}
    → { available_hours: float, collaborators: int, by_shift: [...] }
```

### Integración con Industrial Scanner

- [ ] Endpoint `POST /clock-in` y `POST /clock-out` para el scanner RFID/biométrico.
- [ ] `TimeRecord` afecta disponibilidad en tiempo real en el dashboard del MES.
- [ ] Vinculación del `CORE_HCM_RFID_SALT` para hashing seguro del ID de tarjeta.

---

## Fase 4: Seguridad, EHS y Domain Events

**Objetivo:** Zero Trust en datos sensibles + arquitectura event-driven para limpieza automática de procesos.

### Seguridad (EHS — Environment, Health & Safety)

- [ ] **MedicalRecord**: Expediente médico. Aislado con cifrado en reposo y permisos de rol granular. Solo accesible por role `MEDICAL_STAFF`.
- [ ] **PPERecord** (Equipo de Protección Personal): Registro de entrega vinculado al puesto. Costo se carga al centro de costos en ERP.

### Domain Events (Event-Driven Architecture)

| Evento | Suscriptores |
|--------|-------------|
| `CollaboratorStatusChanged(INACTIVE/DISABLED)` | MES → desasigna estación de trabajo; CMMS → reasigna OT |
| `CertificationExpired` | Notification Service → alerta a supervisor + colaborador |
| `NewCollaboratorOnboarded` | Auth Service → crea `UserCompanyRole`; MES → habilita accesos |
| `PPEDelivered` | ERP → crea línea de costo en centro de costos del puesto |

---

## Arquitectura del Servicio

```
hcm_service/
├── app/
│   ├── models/
│   │   ├── collaborator.py       # Entidad principal (Fase 1)
│   │   ├── department.py
│   │   ├── position.py
│   │   ├── skill.py              # Fase 2
│   │   ├── collaborator_skill.py
│   │   ├── certification.py
│   │   ├── training_record.py
│   │   ├── shift.py              # Fase 3
│   │   ├── time_record.py
│   │   └── medical_record.py    # Fase 4 (Zero Trust)
│   ├── services/
│   │   ├── competency_manager.py
│   │   ├── shift_service.py
│   │   └── clock_service.py
│   ├── commands/                 # CQRS — Escritura
│   └── queries/                  # CQRS — Lectura optimizada (< 100ms)
└── alembic/
```

---

## Directriz de Implementación para el Agente

```
Refactorizar hr_service → hcm_service.
- Collaborator hereda MultiTenantBase + AuditBase.
- CQRS: Commands → contratación/baja; Queries → validación de Skills (< 100ms SLA).
- company_id obligatorio en todas las transacciones.
- Funcional idéntico en local (Docker) y AWS (ECS/RDS).
- DB: hcm_db (separada de auth DB).
```
