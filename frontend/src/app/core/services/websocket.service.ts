import { Injectable, inject, signal, OnDestroy } from '@angular/core';
import { toObservable } from '@angular/core/rxjs-interop';
import { AuthService } from './auth.service';
import { Subject, Subscription, timer } from 'rxjs';
import { retryWhen, delayWhen, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

export interface WsMessage {
  type: 'NOTIFICATION' | 'INVENTORY_UPDATE' | 'TICKET_ESCALATION' | 'SYSTEM_ALERT';
  company_id: string;
  payload: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService implements OnDestroy {
  private auth = inject(AuthService);
  private socket?: WebSocket;
  private reconnectSub?: Subscription;
  private activeCompanyId: string | null = null;

  // Global event stream for other services to subscribe to
  private _messageSource = new Subject<WsMessage>();
  public messages$ = this._messageSource.asObservable();

  public connected = signal<boolean>(false);

  constructor() {
    // Auto-connect/disconnect based on company selection
    toObservable(this.auth.activeCompanyId).subscribe((companyId: string | null) => {
      if (companyId) {
        if (this.activeCompanyId !== companyId) {
          this.activeCompanyId = companyId;
          this.connect(companyId);
        }
      } else {
        this.activeCompanyId = null;
        this.disconnect();
      }
    });
  }

  private connect(companyId: string) {
    this.disconnect();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use the base host but with the WS port/path
    const wsUrl = `${protocol}//localhost:8000/ws/${companyId}`;
    
    console.log(`[WebSocket] 🔌 Connecting to ${wsUrl}...`);
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('[WebSocket] ✅ Connected.');
      this.connected.set(true);
      this.reconnectSub?.unsubscribe();
    };

    this.socket.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        this._messageSource.next(msg);
      } catch (e) {
        console.error('[WebSocket] ❌ Error parsing message:', e);
      }
    };

    this.socket.onclose = () => {
      console.warn('[WebSocket] 🔌 Disconnected.');
      this.connected.set(false);
      this.scheduleReconnect(companyId);
    };

    this.socket.onerror = (err) => {
      console.error('[WebSocket] ❌ Error:', err);
    };
  }

  private disconnect() {
    if (this.socket) {
      this.socket.onclose = null; // Prevent reconnect loop
      this.socket.close();
      this.socket = undefined;
    }
    this.connected.set(false);
  }

  private scheduleReconnect(companyId: string) {
    if (this.reconnectSub) return;
    
    console.log('[WebSocket] ⏳ Scheduling reconnect in 5s...');
    this.reconnectSub = timer(5000).subscribe(() => {
      this.reconnectSub = undefined;
      this.connect(companyId);
    });
  }

  ngOnDestroy() {
    this.disconnect();
    this.reconnectSub?.unsubscribe();
  }
}
