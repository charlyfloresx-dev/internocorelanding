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
