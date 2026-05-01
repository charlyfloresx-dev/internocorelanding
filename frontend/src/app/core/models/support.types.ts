export enum TicketStatus {
  NEW = "Nuevo",
  IN_REVIEW = "En revisión",
  ASSIGNED = "Asignado",
  IN_PROGRESS = "En progreso",
  ON_HOLD = "En espera",
  RESOLVED = "Resuelto",
  CLOSED = "Cerrado",
  CANCELED = "Cancelado"
}

export enum TicketPriority {
  LOW = "Baja",
  MEDIUM = "Media",
  HIGH = "Alta",
  CRITICAL = "Crítica"
}

export enum TicketType {
  SUPPORT = "Soporte",
  INCIDENT = "Incidencia",
  IMPROVEMENT = "Mejora",
  COMPLAINT = "Queja",
  TASK = "Tarea",
  MAINTENANCE = "Mantenimiento",
  MATERIAL_RECEIPT = "Recibo Material",
  DOWNTIME = "Tiempo Muerto",
  ESCALATION = "Escalación"
}

export interface TicketComment {
  id: string;
  author_id: string;
  content: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  reference_code: string;
  title: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  ticket_type: TicketType;
  created_at: string;
  updated_at?: string;
  assigned_to_id?: string;
  comments?: TicketComment[];
}

export interface ApiResponse<T> {
  status: string;
  data: T;
  message: string;
  meta: any;
}
