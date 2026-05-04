export enum TicketStatus {
  NEW = "Nuevo",
  PENDING_APPROVAL = "Pendiente de Aprobación",
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
  created_by: string;
  assigned_to_id?: string;
  area?: string;
  department_id?: string;
  comments?: TicketComment[];
}

export interface TicketTriage {
  action: 'APPROVE' | 'REASSIGN';
  new_assigned_to_id?: string;
  comment?: string;
}

export interface ApiResponse<T> {
  status: string;
  data: T;
  message: string;
  meta: any;
}
