import { inject, Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ApiResponse, Ticket, TicketStatus, TicketPriority, TicketType, CreateTicketCommand, UpdateTicketCommand, TicketComment } from '@models/api.types';
import { firstValueFrom } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class TicketService {
    private http = inject(HttpClient);
    private apiUrl = environment.ticketsUrl;

    tickets = signal<Ticket[]>([]);
    currentTicket = signal<Ticket | null>(null);
    loading = signal<boolean>(false);

    async loadTickets() {
        this.loading.set(true);
        try {
            const res = await firstValueFrom(this.http.get<ApiResponse<Ticket[]>>(this.apiUrl));
            this.tickets.set(res.data);
        } catch (error) {
            console.error('Error loading tickets', error);
        } finally {
            this.loading.set(false);
        }
    }

    async loadTicket(id: string) {
        this.loading.set(true);
        try {
            const res = await firstValueFrom(this.http.get<ApiResponse<Ticket>>(`${this.apiUrl}/${id}`));
            this.currentTicket.set(res.data);
        } catch (error) {
            console.error('Error loading ticket', error);
            this.currentTicket.set(null);
        } finally {
            this.loading.set(false);
        }
    }

    async createTicket(cmd: CreateTicketCommand): Promise<boolean> {
        try {
            await firstValueFrom(this.http.post<ApiResponse<Ticket>>(this.apiUrl, cmd));
            await this.loadTickets();
            return true;
        } catch (error) {
            console.error('Error creating ticket', error);
            return false;
        }
    }

    async updateTicket(id: string, cmd: UpdateTicketCommand): Promise<boolean> {
        try {
            await firstValueFrom(this.http.patch<ApiResponse<Ticket>>(`${this.apiUrl}/${id}`, cmd));
            await this.loadTicket(id);
            return true;
        } catch (error) {
            console.error('Error updating ticket', error);
            return false;
        }
    }

    async addComment(ticketId: string, content: string): Promise<boolean> {
        try {
            await firstValueFrom(this.http.post<ApiResponse<TicketComment>>(`${this.apiUrl}/${ticketId}/comments`, { content }));
            await this.loadTicket(ticketId); // Refresh history/comments
            return true;
        } catch (error) {
            console.error('Error adding comment', error);
            return false;
        }
    }
}
