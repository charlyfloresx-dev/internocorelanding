class Department {
  final String id;
  final String name;
  final String code;

  const Department({required this.id, required this.name, required this.code});

  factory Department.fromJson(Map<String, dynamic> json) => Department(
        id: json['id'],
        name: json['name'],
        code: json['code'],
      );
}

enum TicketPriority { low, medium, high, critical }
enum TicketStatus { newTicket, pending, reviewing, assigned, inProgress, waiting, resolved, closed, canceled }

class Ticket {
  final String id;
  final String referenceCode;
  final String title;
  final String description;
  final TicketPriority priority;
  final TicketStatus status;
  final DateTime createdAt;
  final String? assignedToId;
  final String? area;
  final String? ticketType;

  Ticket({
    required this.id,
    required this.referenceCode,
    required this.title,
    required this.description,
    required this.priority,
    required this.status,
    required this.createdAt,
    this.assignedToId,
    this.area,
    this.ticketType,
  });

  factory Ticket.fromJson(Map<String, dynamic> json) {
    return Ticket(
      id: json['id'],
      referenceCode: json['reference_code'],
      title: json['title'],
      description: json['description'],
      priority: _parsePriority(json['priority']),
      status: _parseStatus(json['status']),
      createdAt: DateTime.parse(json['created_at']),
      assignedToId: json['assigned_to_id'],
      area: json['area'],
      ticketType: json['ticket_type'],
    );
  }

  static TicketPriority _parsePriority(String? p) {
    switch (p) {
      case 'Baja':
        return TicketPriority.low;
      case 'Alta':
        return TicketPriority.high;
      case 'Crítica':
        return TicketPriority.critical;
      case 'Media':
      default:
        return TicketPriority.medium;
    }
  }

  static TicketStatus _parseStatus(String? s) {
    switch (s) {
      case 'Pendiente de Aprobación':
        return TicketStatus.pending;
      case 'En revisión':
        return TicketStatus.reviewing;
      case 'Asignado':
        return TicketStatus.assigned;
      case 'En progreso':
        return TicketStatus.inProgress;
      case 'En espera':
        return TicketStatus.waiting;
      case 'Resuelto':
        return TicketStatus.resolved;
      case 'Cerrado':
        return TicketStatus.closed;
      case 'Cancelado':
        return TicketStatus.canceled;
      case 'Nuevo':
      default:
        return TicketStatus.newTicket;
    }
  }
}

class TicketCreateRequest {
  final String title;
  final String description;
  final TicketPriority priority;
  final String? area;

  TicketCreateRequest({
    required this.title,
    required this.description,
    required this.priority,
    this.area,
  });

  Map<String, dynamic> toJson(String companyId) {
    String priorityStr = 'Media';
    switch (priority) {
      case TicketPriority.low: priorityStr = 'Baja'; break;
      case TicketPriority.medium: priorityStr = 'Media'; break;
      case TicketPriority.high: priorityStr = 'Alta'; break;
      case TicketPriority.critical: priorityStr = 'Crítica'; break;
    }

    return {
      'title': title,
      'description': description,
      'priority': priorityStr,
      'company_id': companyId,
      if (area != null && area!.isNotEmpty) 'area': area,
    };
  }
}

class TicketComment {
  final String id;
  final String content;
  final String authorId;
  final DateTime createdAt;

  TicketComment({
    required this.id,
    required this.content,
    required this.authorId,
    required this.createdAt,
  });

  factory TicketComment.fromJson(Map<String, dynamic> json) {
    return TicketComment(
      id: json['id'],
      content: json['content'],
      authorId: json['author_id'],
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}

class TicketAction {
  final String id;
  final String description;
  final String? assignedToId;
  final String? assigneeName;
  final String? assigneeType;
  final DateTime? commitDate;
  final bool isClosed;
  final DateTime? closedAt;
  final DateTime createdAt;

  TicketAction({
    required this.id,
    required this.description,
    this.assignedToId,
    this.assigneeName,
    this.assigneeType,
    this.commitDate,
    required this.isClosed,
    this.closedAt,
    required this.createdAt,
  });

  factory TicketAction.fromJson(Map<String, dynamic> json) {
    return TicketAction(
      id: json['id'],
      description: json['description'],
      assignedToId: json['assigned_to_id'],
      assigneeName: json['assignee_name'],
      assigneeType: json['assignee_type'],
      commitDate: json['commit_date'] != null ? DateTime.tryParse(json['commit_date']) : null,
      isClosed: json['is_closed'] ?? false,
      closedAt: json['closed_at'] != null ? DateTime.tryParse(json['closed_at']) : null,
      createdAt: DateTime.parse(json['created_at']),
    );
  }
}
