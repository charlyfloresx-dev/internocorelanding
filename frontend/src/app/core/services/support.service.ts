// temp_future/src/app/core/services/support.service.ts
import { inject, Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';
import { WebSocketService } from './websocket.service';
import { environment } from '../../../environments/environment';
import { Ticket, TicketComment, TicketPriority, TicketStatus, ApiResponse } from '../models/support.types';
import { firstValueFrom, filter } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SupportService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
  private ws = inject(WebSocketService);
  private baseUrl = `${environment.ticketsUrl}/tickets`;

  private _tickets = signal<Ticket[]>([]);
  private _loading = signal<boolean>(false);
  private _error = signal<string | null>(null);
  private _constants = signal<{statuses: string[], priorities: string[], types: string[]} | null>(null);

  readonly tickets = computed(() => this._tickets());
  readonly loading = computed(() => this._loading());
  readonly error = computed(() => this._error());
  readonly constants = computed(() => this._constants());

  constructor() {
    this.loadConstants();
    
    // Escuchar actualizaciones de tickets en tiempo real
    this.ws.messages$.pipe(
      filter((msg: any) => msg.type === 'TICKET_UPDATE' || msg.type === 'TICKET_CREATED')
    ).subscribe((msg: any) => {
       console.log(`[SupportService] 🎫 Real-time ticket update (${msg.type}):`, msg.payload);
       this.handleRealtimeTicketUpdate(msg.type, msg.payload);
    });
  }

  private handleRealtimeTicketUpdate(type: string, payload: any) {
    if (type === 'TICKET_CREATED') {
      this._tickets.update(ts => [payload, ...ts]);
    } else {
      this._tickets.update(ts => ts.map(t => t.id === payload.id ? { ...t, ...payload } : t));
    }
  }

  async loadConstants() {
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<any>>(`${this.baseUrl}/config/constants`)
      );
      if (response.data) {
        this._constants.set(response.data);
      }
    } catch (err) {
      console.error('Error loading ticket constants:', err);
    }
  }

  async loadTickets() {
    this._loading.set(true);
    this._error.set(null);
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<Ticket[]>>(this.baseUrl)
      );
      if (response.data) {
        this._tickets.set(response.data);
      }
    } catch (err: any) {
      this._error.set(err.message || 'Error al cargar tickets');
      console.error('Error loading tickets:', err);
    } finally {
      this._loading.set(false);
    }
  }

  async createTicket(title: string, description: string, priority: TicketPriority = TicketPriority.MEDIUM, area?: string) {
    const companyId = this.authService.activeCompanyId();
    if (!companyId) return;

    this._loading.set(true);
    try {
      const payload: any = {
        title,
        description,
        priority,
        company_id: companyId,
        ticket_type: 'Soporte',
        source_service: 'MANUAL'
      };

      if (area) {
        payload.area = area;
      }

      const response = await firstValueFrom(
        this.http.post<ApiResponse<Ticket>>(this.baseUrl, payload)
      );

      return response.data;
    } catch (err: any) {
      this._error.set(err.message || 'Error al crear ticket');
      throw err;
    } finally {
      this._loading.set(false);
    }
  }

  async getMessages(ticketId: string): Promise<TicketComment[]> {
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<TicketComment[]>>(`${this.baseUrl}/${ticketId}/comments`)
      );
      return response.data || [];
    } catch (err) {
      console.error('Error loading comments:', err);
      return [];
    }
  }

  async addMessage(ticketId: string, content: string) {
    try {
      const response = await firstValueFrom(
        this.http.post<ApiResponse<TicketComment>>(`${this.baseUrl}/${ticketId}/comments`, { content })
      );
      return response.data;
    } catch (err) {
      console.error('Error adding comment:', err);
      throw err;
    }
  }

  async updateTicketStatus(ticketId: string, newStatus: string) {
    try {
      const response = await firstValueFrom(
        this.http.patch<ApiResponse<Ticket>>(`${this.baseUrl}/${ticketId}`, { status: newStatus })
      );
      return response.data;
    } catch (err) {
      console.error('Error updating ticket status:', err);
      this.loadTickets();
      throw err;
    }
  }

  async triageTicket(ticketId: string, action: 'APPROVE' | 'REASSIGN', newAssignedToId?: string, comment?: string, collaboratorId?: string, externalContactId?: string) {
    try {
      const payload: any = { action };
      if (newAssignedToId) payload.new_assigned_to_id = newAssignedToId;
      if (collaboratorId) payload.collaborator_id = collaboratorId;
      if (externalContactId) payload.external_contact_id = externalContactId;
      if (comment) payload.comment = comment;

      const response = await firstValueFrom(
        this.http.post<ApiResponse<Ticket>>(`${this.baseUrl}/${ticketId}/triage`, payload)
      );
      return response.data;
    } catch (err) {
      console.error('Error in triage action:', err);
      throw err;
    }
  }

  async searchIdentities(q: string): Promise<any[]> {
    try {
      const [users, collaborators, contacts] = await Promise.all([
        firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/users/?q=${q}`)),
        firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/hcm/collaborators/search?q=${q}`)),
        firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/partners/contacts/search?q=${q}`))
      ]);

      const results = [];
      if (users.data) results.push(...users.data.map(u => ({ ...u, type: 'INTERNAL', label: u.full_name, sub: u.email })));
      if (collaborators.data) results.push(...collaborators.data.map(c => ({ ...c, type: 'PLANTA', label: c.full_name, sub: c.internal_id })));
      if (contacts.data) results.push(...contacts.data.map(e => ({ ...e, type: 'EXTERNO', label: e.full_name, sub: e.email })));

      return results;
    } catch (err) {
      console.error('Error searching identities:', err);
      return [];
    }
  }

  async getTechniciansWorkload(): Promise<Record<string, number>> {
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<Record<string, number>>>(`${this.baseUrl}/technicians/workload`)
      );
      return response.data || {};
    } catch (err) {
      console.error('Error loading technician workload:', err);
      return {};
    }
  }
}
