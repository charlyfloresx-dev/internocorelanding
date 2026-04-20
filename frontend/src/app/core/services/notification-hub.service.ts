import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ApiResponse, ValidationStatus } from '../models/domain.types';
import { AuthService } from './auth.service';
import { interval, switchMap, catchError, of, Subscription } from 'rxjs';

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
  private apiUrl = `${environment.apiUrl}/notifications`;

  notifications = signal<AppNotification[]>([]);
  unreadCount = signal<number>(0);
  
  private pollingSub?: Subscription;

  constructor() {
    // Start polling when authenticated and company is selected
    // Note: In a real app, this would be managed by a more central orchestrator
  }

  startPolling() {
    if (this.pollingSub) return;

    this.pollingSub = interval(30000) // Poll every 30 seconds
      .pipe(
        switchMap(() => this.fetchNotifications()),
        catchError(err => {
          console.error('[NotificationHub] Polling error:', err);
          return of([]);
        })
      )
      .subscribe(data => {
        this.notifications.set(data);
        this.unreadCount.set(data.length); // Simplified
      });
      
    // Initial fetch
    this.fetchNotifications().subscribe(data => {
      this.notifications.set(data);
      this.unreadCount.set(data.length);
    });
  }

  stopPolling() {
    this.pollingSub?.unsubscribe();
    this.pollingSub = undefined;
  }

  private fetchNotifications() {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) return of([]);

    return this.http.get<ApiResponse<AppNotification[]>>(`${this.apiUrl}/`, {
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
