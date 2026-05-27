// temp_future/src/app/core/services/support.service.ts
import { inject, Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';
import { WebSocketService } from './websocket.service';
import { environment } from '../../../environments/environment';
import { Ticket, TicketAction, TicketComment, TicketPriority, TicketStatus, ApiResponse } from '../models/support.types';
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

  async getTicket(ticketId: string): Promise<Ticket | null> {
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<Ticket>>(`${this.baseUrl}/${ticketId}`)
      );
      return response.data || null;
    } catch (err) {
      console.error('Error loading ticket:', err);
      return null;
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

  async triageTicket(ticketId: string, action: 'APPROVE' | 'REASSIGN', assignees: import('../models/support.types').AssigneeInput[], comment?: string) {
    try {
      const payload: any = { action, assignees };
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
    const [usersRes, collaboratorsRes, contactsRes] = await Promise.allSettled([
      firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/users/?q=${q}`)),
      firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/staff/search?q=${q}`)),
      firstValueFrom(this.http.get<ApiResponse<any[]>>(`${environment.apiUrl}/api/v1/partners/contacts/search?q=${q}`))
    ]);

    const results: any[] = [];
    if (usersRes.status === 'fulfilled' && usersRes.value.data)
      results.push(...usersRes.value.data.map(u => ({ ...u, type: 'INTERNAL', label: u.full_name, sub: u.email })));
    if (collaboratorsRes.status === 'fulfilled' && collaboratorsRes.value.data)
      results.push(...collaboratorsRes.value.data.map(c => ({ ...c, type: 'PLANTA', label: c.full_name, sub: c.internal_id })));
    if (contactsRes.status === 'fulfilled' && contactsRes.value.data)
      results.push(...contactsRes.value.data.map(e => ({ ...e, type: 'EXTERNO', label: e.full_name, sub: e.email })));

    return results;
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

  async getActions(ticketId: string): Promise<TicketAction[]> {
    try {
      const response = await firstValueFrom(
        this.http.get<ApiResponse<TicketAction[]>>(`${this.baseUrl}/${ticketId}/actions`)
      );
      return response.data || [];
    } catch (err) {
      console.error('Error loading actions:', err);
      return [];
    }
  }

  async createAction(ticketId: string, payload: {
    description: string;
    assigned_to_id?: string;
    collaborator_id?: string;
    external_contact_id?: string;
    commit_date?: string;
  }): Promise<TicketAction> {
    const response = await firstValueFrom(
      this.http.post<ApiResponse<TicketAction>>(`${this.baseUrl}/${ticketId}/actions`, payload)
    );
    return response.data;
  }

  async closeAction(ticketId: string, actionId: string): Promise<TicketAction> {
    const response = await firstValueFrom(
      this.http.patch<ApiResponse<TicketAction>>(
        `${this.baseUrl}/${ticketId}/actions/${actionId}/close`,
        {}
      )
    );
    return response.data;
  }
}
