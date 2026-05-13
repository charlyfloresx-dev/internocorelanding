import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ApiResponse, ValidationStatus } from '../models/domain.types';
import { AuthService } from './auth.service';
import { interval, switchMap, catchError, of, Subscription } from 'rxjs';
import { WebSocketService } from './websocket.service';

export interface AppNotification {
  id: string;
  type: string;
  title: string;
  message: string;
  priority: string;
  channel: string;
  status: string;
  created_at: string;
  payload?: any;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationHubService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private apiUrl = `${environment.notificationUrl}/notifications`;

  private ws = inject(WebSocketService);
  
  notifications = signal<AppNotification[]>([]);
  unreadCount = signal<number>(0);
  
  constructor() {
    // Escuchar mensajes en tiempo real vía WebSocket
    this.ws.messages$.subscribe(msg => {
      if (msg.type === 'NOTIFICATION') {
        console.log('[NotificationHub] 🔔 Real-time notification received:', msg.payload);
        this.notifications.update(prev => [msg.payload, ...prev]);
        this.unreadCount.update(c => c + 1);
      }
    });

    // Carga inicial (una sola vez al iniciar)
    this.fetchNotifications().subscribe(data => {
      this.notifications.set(data);
      this.unreadCount.set(data.length);
    });
  }

  startPolling() {
    // Deprecated: No longer needed with WebSocket active
    console.log('[NotificationHub] 🔌 WebSocket is now the primary data source.');
  }

  stopPolling() {
    // Deprecated: No polling to stop when using WebSockets
  }

  private fetchNotifications() {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) return of([]);

    return this.http.get<ApiResponse<AppNotification[]>>(`${this.apiUrl}`, {
      headers: { 'x-company-id': companyId }
    }).pipe(
      switchMap(res => of(res.data || [])),
      catchError(() => of([]))
    );
  }

  async markAsRead(id: string) {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) return;

    try {
      await this.http.patch(`${this.apiUrl}/${id}/read`, {}, {
        headers: { 'x-company-id': companyId }
      }).toPromise();
      
      this.notifications.update(prev => prev.filter(n => n.id !== id));
      this.unreadCount.update(c => Math.max(0, c - 1));
    } catch (e) {
      console.error('[NotificationHub] Mark as read error:', e);
    }
  }
}
