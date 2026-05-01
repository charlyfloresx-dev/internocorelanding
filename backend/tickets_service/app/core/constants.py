from enum import Enum

class TicketStatus(str, Enum):
    NEW = "Nuevo"
    IN_REVIEW = "En revisión"
    ASSIGNED = "Asignado"
    IN_PROGRESS = "En progreso"
    ON_HOLD = "En espera"
    RESOLVED = "Resuelto"
    CLOSED = "Cerrado"
    CANCELED = "Cancelado"

class TicketPriority(str, Enum):
    LOW = "Baja"
    MEDIUM = "Media"
    HIGH = "Alta"
    CRITICAL = "Crítica"

class TicketType(str, Enum):
    SUPPORT = "Soporte"
    INCIDENT = "Incidencia"
    IMPROVEMENT = "Mejora"
    COMPLAINT = "Queja"
    TASK = "Tarea"
    # --- Flujos Operacionales Industriales (Fase 5) ---
    MAINTENANCE = "Mantenimiento"           # Flujo 1: Planta / MES
    MATERIAL_RECEIPT = "Recibo Material"     # Flujo 2: Supply Chain / ERP
    DOWNTIME = "Tiempo Muerto"              # Flujo 4: Paros de producción
    ESCALATION = "Escalación"               # Flujo 4: Reasignación jerárquica
