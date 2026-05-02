import { inject, Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';
import { Ticket, TicketComment, TicketPriority, TicketStatus, ApiResponse } from '../models/support.types';
import { firstValueFrom } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class SupportService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);
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

      if (response.data) {
        this._tickets.update(ts => [response.data, ...ts]);
        return response.data;
      }
      return null;
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
      
      // Update the local ticket updatedAt if needed
      this._tickets.update(ts => ts.map(t => {
        if (t.id === ticketId) {
          return { ...t, updated_at: new Date().toISOString() };
        }
        return t;
      }));

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
      
      if (response.data) {
        // Actualizamos localmente
        this._tickets.update(ts => ts.map(t => t.id === ticketId ? { ...t, status: response.data.status } : t));
      }
      return response.data;
    } catch (err) {
      console.error('Error updating ticket status:', err);
      // Reload tickets to restore correct state on error
      this.loadTickets();
      throw err;
    }
  }

  /**
   * Phase 10: Triage logic for supervisors
   */
  async triageTicket(ticketId: string, action: 'APPROVE' | 'REASSIGN', newAssignedToId?: string, comment?: string) {
    try {
      const payload: any = { action };
      if (newAssignedToId) payload.new_assigned_to_id = newAssignedToId;
      if (comment) payload.comment = comment;

      const response = await firstValueFrom(
        this.http.post<ApiResponse<Ticket>>(`${this.baseUrl}/${ticketId}/triage`, payload)
      );

      if (response.data) {
        // Actualizamos localmente la señal
        this._tickets.update(ts => ts.map(t => t.id === ticketId ? response.data : t));
      }
      return response.data;
    } catch (err) {
      console.error('Error in triage action:', err);
      throw err;
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
