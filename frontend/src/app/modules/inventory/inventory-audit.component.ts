import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

interface AuditLog {
  id: string;
  action: string;
  table_name: string;
  record_id: string;
  user_id: string;
  timestamp: string;
  old_value: any;
  new_value: any;
  trace_id: string;
}

@Component({
  selector: 'app-inventory-audit',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="space-y-8 animate-fade-in pb-24">
      <!-- Header -->
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-center text-amber-500 shadow-sm">
          <mat-icon class="text-2xl">security</mat-icon>
        </div>
        <div>
          <h1 class="text-3xl font-black text-slate-900 dark:text-white tracking-tighter uppercase italic">
            Audit Log Forensic
          </h1>
          <p class="text-slate-500 dark:text-slate-400 font-mono text-[9px] tracking-[0.2em] uppercase">
            Registro inmutable de acciones y cambios en el sistema
          </p>
        </div>
      </div>

      <!-- Filters -->
      <div class="industrial-card p-6 flex flex-wrap gap-4 items-center justify-between">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="flex flex-col gap-1">
            <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Acción</span>
            <select [(ngModel)]="filterAction" (change)="loadLogs()" class="bg-surface-bg border border-surface-border rounded-lg px-3 py-2 text-[10px] font-bold text-surface-text outline-none focus:border-primary">
              <option value="">TODAS</option>
              <option value="INSERT">INSERT</option>
              <option value="UPDATE">UPDATE</option>
              <option value="DELETE">DELETE</option>
              <option value="UNAUTHORIZED_WAREHOUSE_ACCESS">UNAUTHORIZED</option>
            </select>
          </div>
          <div class="flex flex-col gap-1">
            <span class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Tabla</span>
            <select [(ngModel)]="filterTable" (change)="loadLogs()" class="bg-surface-bg border border-surface-border rounded-lg px-3 py-2 text-[10px] font-bold text-surface-text outline-none focus:border-primary">
              <option value="">TODAS</option>
              <option value="inventory_movements">Movements</option>
              <option value="inventory_documents">Documents</option>
              <option value="inventory_warehouses">Warehouses</option>
            </select>
          </div>
        </div>
        <button (click)="loadLogs()" class="p-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all" title="Refrescar">
          <mat-icon>refresh</mat-icon>
        </button>
      </div>

      <!-- Table -->
      <div class="industrial-card overflow-hidden">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50">
                <th class="px-6 py-4 text-[9px] font-black text-slate-500 uppercase tracking-widest">Timestamp</th>
                <th class="px-6 py-4 text-[9px] font-black text-slate-500 uppercase tracking-widest">Acción</th>
                <th class="px-6 py-4 text-[9px] font-black text-slate-500 uppercase tracking-widest">Tabla / ID</th>
                <th class="px-6 py-4 text-[9px] font-black text-slate-500 uppercase tracking-widest">Usuario</th>
                <th class="px-6 py-4 text-[9px] font-black text-slate-500 uppercase tracking-widest text-right">Detalles</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (log of logs(); track log.id) {
                <tr class="hover:bg-white/5 transition-all group">
                  <td class="px-6 py-4">
                    <div class="flex flex-col">
                      <span class="text-xs font-mono font-bold text-surface-text">{{ log.timestamp | date:'dd/MM/yyyy HH:mm:ss' }}</span>
                      <span class="text-[8px] text-slate-500 font-mono">{{ log.trace_id }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span [class]="getActionClass(log.action)" class="px-2 py-1 rounded text-[8px] font-black uppercase tracking-widest border">
                      {{ log.action }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex flex-col">
                      <span class="text-[10px] font-black text-surface-text uppercase tracking-tight">{{ log.table_name }}</span>
                      <span class="text-[8px] font-mono text-slate-500">{{ log.record_id }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-[10px] font-bold text-surface-text-muted uppercase">{{ log.user_id }}</span>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button (click)="selectedLog.set(log)" class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-all">
                      <mat-icon>visibility</mat-icon>
                    </button>
                  </td>
                </tr>
              }
              @if (logs().length === 0) {
                <tr>
                  <td colspan="5" class="px-6 py-12 text-center text-slate-500 uppercase text-[10px] font-black tracking-widest">
                    No se encontraron registros de auditoría
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Detail Modal -->
      @if (selectedLog(); as log) {
        <div class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" (click)="selectedLog.set(null)">
          <div class="industrial-card w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col p-8 space-y-6" (click)="$event.stopPropagation()">
            <div class="flex items-center justify-between border-b border-surface-border pb-4">
              <h3 class="text-xl font-black text-surface-text uppercase tracking-widest italic">Detalle de Auditoría</h3>
              <button (click)="selectedLog.set(null)" class="text-slate-500 hover:text-white">
                <mat-icon>close</mat-icon>
              </button>
            </div>

            <div class="flex-1 overflow-y-auto custom-scrollbar space-y-6 pr-2">
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="p-4 bg-white/5 rounded-xl border border-white/10">
                  <span class="text-[8px] font-black text-slate-500 uppercase block mb-1">Acción</span>
                  <span class="text-xs font-black text-primary">{{ log.action }}</span>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-white/10">
                  <span class="text-[8px] font-black text-slate-500 uppercase block mb-1">Tabla</span>
                  <span class="text-xs font-black text-surface-text">{{ log.table_name }}</span>
                </div>
                <div class="p-4 bg-white/5 rounded-xl border border-white/10 col-span-2">
                  <span class="text-[8px] font-black text-slate-500 uppercase block mb-1">Registro ID</span>
                  <span class="text-[10px] font-mono font-bold text-surface-text">{{ log.record_id }}</span>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 class="text-[9px] font-black text-rose-400 uppercase tracking-widest mb-2 italic">Valor Anterior</h4>
                  <pre class="bg-black/40 p-4 rounded-xl border border-white/5 text-[10px] font-mono text-slate-300 overflow-x-auto">{{ log.old_value | json }}</pre>
                </div>
                <div>
                  <h4 class="text-[9px] font-black text-emerald-400 uppercase tracking-widest mb-2 italic">Valor Nuevo</h4>
                  <pre class="bg-black/40 p-4 rounded-xl border border-white/5 text-[10px] font-mono text-slate-300 overflow-x-auto">{{ log.new_value | json }}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    pre { white-space: pre-wrap; word-break: break-all; }
  `]
})
export class InventoryAuditComponent implements OnInit {
  private http = inject(HttpClient);
  
  logs = signal<AuditLog[]>([]);
  selectedLog = signal<AuditLog | null>(null);
  
  filterAction = '';
  filterTable = '';

  ngOnInit() {
    this.loadLogs();
  }

  loadLogs() {
    let url = `${environment.apiUrl}/api/v1/audit/?limit=100`;
    if (this.filterAction) url += `&action=${this.filterAction}`;
    if (this.filterTable) url += `&table_name=${this.filterTable}`;

    this.http.get<any>(url).subscribe({
      next: (res) => {
        this.logs.set(res.data || []);
      },
      error: (err) => console.error('Error loading audit logs', err)
    });
  }

  getActionClass(action: string) {
    switch (action) {
      case 'INSERT': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'UPDATE': return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'DELETE': return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      case 'UNAUTHORIZED_WAREHOUSE_ACCESS': return 'bg-red-500/20 text-red-500 border-red-500/50';
      default: return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  }
}
