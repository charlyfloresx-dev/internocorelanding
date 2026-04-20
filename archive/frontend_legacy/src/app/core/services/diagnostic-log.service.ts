
import { Injectable, signal } from '@angular/core';

export interface LogEntry {
  timestamp: string;
  action: string;
  target: string;
  status: 'pending' | 'success' | 'failed';
  details?: string;
}

@Injectable({
  providedIn: 'root'
})
export class DiagnosticLogService {
  private history: LogEntry[] = [];
  logs = signal<LogEntry[]>([]);

  constructor() {
    this.loadHistory();
  }

  private loadHistory() {
    const saved = localStorage.getItem('interno_diag_log');
    if (saved) {
      try {
        this.history = JSON.parse(saved);
        this.logs.set(this.history);
      } catch (e) {
        this.history = [];
      }
    }
  }

  private saveHistory() {
    localStorage.setItem('interno_diag_log', JSON.stringify(this.history));
    this.logs.set([...this.history]);
  }

  // Comprueba si una acción específica ya se intentó y falló
  wasAttempted(action: string, target: string): boolean {
    return this.history.some(h => h.action === action && h.target === target && h.status === 'failed');
  }

  record(action: string, target: string, status: 'pending' | 'success' | 'failed', details?: string) {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      action,
      target,
      status,
      details
    };
    this.history.push(entry);
    this.saveHistory();
  }

  clear() {
    this.history = [];
    localStorage.removeItem('interno_diag_log');
    this.logs.set([]);
  }
}
