import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse, Ticket, TicketStatus, TicketPriority, TicketType } from '../models/domain.types';

const OPEN_STATUSES = 'Nuevo,Pendiente de Aprobación,Asignado,En progreso';

@Injectable({ providedIn: 'root' })
export class TicketService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.ticketsUrl}/tickets`;

  // Signals for the resource Soporte tab
  stationTickets   = signal<Ticket[]>([]);
  loadingStation   = signal(false);

  getTickets(): Observable<ApiResponse<Ticket[]>> {
    return this.http.get<ApiResponse<Ticket[]>>(this.apiUrl);
  }

  /** Load open tickets for a specific MES resource (station_id = resource.id) */
  async loadByStation(resourceId: string): Promise<void> {
    this.loadingStation.set(true);
    try {
      const res = await firstValueFrom(
        this.http.get<ApiResponse<Ticket[]>>(
          `${this.apiUrl}?station_id=${resourceId}`
        )
      );
      const all: Ticket[] = (res as any).data ?? [];
      // Keep only open tickets (not RESOLVED/CLOSED/CANCELLED)
      this.stationTickets.set(
        all.filter(t => !['Resuelto', 'Cerrado', 'Cancelado'].includes(t.status))
      );
    } catch {
      this.stationTickets.set([]);
    } finally {
      this.loadingStation.set(false);
    }
  }

  getConfigConstants(): Observable<ApiResponse<any>> {
    return this.http.get<ApiResponse<any>>(`${this.apiUrl}/config/constants`);
  }

  getTicket(id: string): Observable<ApiResponse<Ticket>> {
    return this.http.get<ApiResponse<Ticket>>(`${this.apiUrl}/${id}`);
  }

  createTicket(ticket: Partial<Ticket>): Observable<ApiResponse<Ticket>> {
    return this.http.post<ApiResponse<Ticket>>(this.apiUrl, ticket);
  }

  updateTicket(id: string, updates: Partial<Ticket>): Observable<ApiResponse<Ticket>> {
    return this.http.patch<ApiResponse<Ticket>>(`${this.apiUrl}/${id}`, updates);
  }

  addComment(ticketId: string, content: string): Observable<ApiResponse<any>> {
    return this.http.post<ApiResponse<any>>(`${this.apiUrl}/${ticketId}/comments`, { content });
  }

  updateStatus(ticketId: string, status: string): Observable<ApiResponse<Ticket>> {
    return this.http.patch<ApiResponse<Ticket>>(`${this.apiUrl}/${ticketId}`, { status });
  }

  deleteTicket(id: string): Observable<ApiResponse<Ticket>> {
    return this.http.delete<ApiResponse<Ticket>>(`${this.apiUrl}/${id}`);
  }
}
