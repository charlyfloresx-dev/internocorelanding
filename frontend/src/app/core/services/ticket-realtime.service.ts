import { Injectable, inject, signal, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { TicketService } from './ticket.service';
import { ToastService } from './toast.service';

interface TicketEvent {
  event_type: 'ticket.created' | 'ticket.updated' | 'ticket.assigned' | 'ticket.status_changed';
  ticket_id: string;
  station_id: string;
  priority?: string;
  status?: string;
  timestamp: string;
}

@Injectable({ providedIn: 'root' })
export class TicketRealtimeService {
  private http = inject(HttpClient);
  private ticketSvc = inject(TicketService);
  private toastSvc = inject(ToastService);

  private ws: WebSocket | null = null;
  isConnected = signal(false);
  connectionAttempts = signal(0);

  private currentResourceId: string | null = null;
  private maxRetries = 5;
  private retryDelay = 1000;

  constructor() {
    // Auto-reconnect when connection is lost
    effect(() => {
      if (!this.isConnected() && this.connectionAttempts() < this.maxRetries) {
        this.scheduleReconnect();
      }
    });
  }

  /** Initialize WebSocket connection for a specific resource */
  connect(resourceId: string): void {
    if (this.currentResourceId === resourceId && this.isConnected()) {
      return; // Already connected to this resource
    }

    this.currentResourceId = resourceId;
    this.disconnect(); // Clean up previous connection

    const wsUrl = this.getWebSocketUrl(resourceId);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${resourceId}`);
        this.isConnected.set(true);
        this.connectionAttempts.set(0);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as TicketEvent;
          this.handleTicketEvent(data);
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      this.ws.onerror = (err) => {
        console.error('[WebSocket] Error:', err);
        this.isConnected.set(false);
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] Connection closed');
        this.isConnected.set(false);
        // Auto-reconnect
        this.connectionAttempts.update(c => c + 1);
      };
    } catch (err) {
      console.error('[WebSocket] Failed to create connection:', err);
      this.isConnected.set(false);
      this.connectionAttempts.update(c => c + 1);
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected.set(false);
    this.currentResourceId = null;
  }

  private handleTicketEvent(event: TicketEvent): void {
    // Only process events for the current station
    if (event.station_id !== this.currentResourceId) {
      return;
    }

    console.log(`[Realtime] Ticket event received:`, event.event_type);

    // Reload tickets from server to get fresh data
    if (this.currentResourceId) {
      this.ticketSvc.loadByStation(this.currentResourceId).catch(err => {
        console.error('[Realtime] Failed to reload tickets:', err);
      });
    }

    // Show toast for critical tickets
    if (event.event_type === 'ticket.created' && event.priority === 'CRÍTICA') {
      this.toastSvc.warning('⚠️ Ticket Crítico', 'Se ha creado un ticket crítico en tu estación', 5000);
      this.playAlertSound();
    }

    // Show toast for status changes
    if (event.event_type === 'ticket.status_changed' && event.status === 'En progreso') {
      this.toastSvc.info('ℹ️ Ticket Asignado', 'Se te ha asignado un nuevo ticket', 3000);
    }
  }

  private scheduleReconnect(): void {
    const delay = this.retryDelay * Math.pow(2, this.connectionAttempts());
    setTimeout(() => {
      if (this.currentResourceId && !this.isConnected()) {
        this.connect(this.currentResourceId);
      }
    }, delay);
  }

  private playAlertSound(): void {
    // Use Web Audio API for alert sound (simple beep)
    try {
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioCtx.createOscillator();
      const gainNode = audioCtx.createGain();

      oscillator.connect(gainNode);
      gainNode.connect(audioCtx.destination);

      oscillator.frequency.value = 800;
      oscillator.type = 'sine';

      gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);

      oscillator.start(audioCtx.currentTime);
      oscillator.stop(audioCtx.currentTime + 0.5);
    } catch (err) {
      console.warn('[Realtime] Could not play alert sound:', err);
    }
  }

  private getWebSocketUrl(resourceId: string): string {
    // Replace http/https with ws/wss
    const baseUrl = environment.ticketsUrl.replace(/^https:/, 'wss:').replace(/^http:/, 'ws:');
    return `${baseUrl}/tickets/realtime/${resourceId}`;
  }
}
