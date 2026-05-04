import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../environments/environment';

interface AuditLog {
  id: string | null;
  action: string;
  table_name: string;
  record_id: string;
  user_id: string;
  timestamp: string;
  old_value: any;
  new_value: any;
  trace_id: string | null;
}

@Component({
  selector: 'app-inventory-audit',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="space-y-8 animate-fade-in pb-24 relative">
      <!-- Forensic Background Pattern -->
      <div class="fixed inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05] overflow-hidden z-0">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" stroke-width="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      <!-- Header Section -->
      <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div class="flex items-center gap-5">
          <div class="w-14 h-14 bg-amber-500/10 border border-amber-500/30 rounded-2xl flex items-center justify-center text-amber-500 shadow-lg">
            <mat-icon class="text-3xl">fingerprint</mat-icon>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-4xl font-black text-slate-900 dark:text-white tracking-tighter uppercase italic leading-none">
                Audit Log <span class="text-amber-500">Forensic</span>
              </h1>
              <div class="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 rounded text-[8px] font-bold text-emerald-500 uppercase tracking-tighter animate-pulse">
                Live Ledger
              </div>
            </div>
            <p class="text-slate-500 dark:text-slate-400 font-mono text-[10px] tracking-[0.3em] uppercase mt-1">
              Registro inmutable de trazabilidad industrial
            </p>
          </div>
        </div>

        <!-- Quick Stats -->
        <div class="flex gap-4">
          <div class="bg-white dark:bg-slate-800 px-6 py-3 rounded-2xl border border-slate-200 dark:border-white/10 flex flex-col items-center min-w-[120px] shadow-sm">
            <span class="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-1">Eventos</span>
            <span class="text-xl font-black text-slate-900 dark:text-white leading-none tabular-nums">{{ logs().length }}</span>
          </div>
          <button (click)="$event.stopPropagation(); loadLogs()" class="w-14 h-14 bg-white dark:bg-slate-800 text-primary rounded-2xl border border-slate-200 dark:border-white/10 hover:border-primary transition-all flex items-center justify-center shadow-lg group">
            <mat-icon class="group-hover:rotate-180 transition-transform duration-700">refresh</mat-icon>
          </button>
        </div>
      </div>

      <!-- Advanced Filters -->
      <div class="bg-white dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-3xl p-2 shadow-2xl relative z-10">
        <div class="flex flex-wrap items-center gap-2 p-4 border border-slate-100 dark:border-white/5 rounded-2xl bg-slate-50 dark:bg-black/20">
          <div class="flex flex-col gap-1.5 flex-1 min-w-[200px]">
            <label class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Filtrar por Acción</label>
            <div class="relative group">
              <select [(ngModel)]="filterAction" (change)="loadLogs()" class="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-[11px] font-black text-slate-900 dark:text-white outline-none focus:border-amber-500/50 appearance-none transition-all cursor-pointer shadow-sm">
                <option value="">TODAS LAS ACCIONES</option>
                <option value="INSERT">INSERT (MANUAL)</option>
                <option value="SEED_CREATE">SEED_CREATE (SISTEMA)</option>
                <option value="UPDATE">UPDATE (MODIFICACIÓN)</option>
                <option value="DELETE">DELETE (ELIMINACIÓN)</option>
                <option value="DENSITY_OVERFLOW">DENSITY_OVERFLOW (ALERTA)</option>
                <option value="CREATE_MOVEMENT">CREATE_MOVEMENT (LOGÍSTICA)</option>
              </select>
              <mat-icon class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">expand_more</mat-icon>
            </div>
          </div>

          <div class="flex flex-col gap-1.5 flex-1 min-w-[200px]">
            <label class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] ml-1">Entidad de Datos</label>
            <div class="relative">
              <select [(ngModel)]="filterTable" (change)="loadLogs()" class="w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 text-[11px] font-black text-slate-900 dark:text-white outline-none focus:border-amber-500/50 appearance-none transition-all cursor-pointer shadow-sm">
                <option value="">TODAS LAS ENTIDADES</option>
                <option value="inventory_movements">Movimientos de Inventario</option>
                <option value="inventory_locations">Ubicaciones (WMS)</option>
                <option value="products">Maestro de Productos</option>
                <option value="users">Control de Usuarios</option>
                <option value="audit_logs">Sistema de Auditoría</option>
              </select>
              <mat-icon class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">expand_more</mat-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- Ledger Table -->
      <div class="bg-white dark:bg-slate-900/50 backdrop-blur-md border border-slate-200 dark:border-white/10 rounded-3xl overflow-hidden shadow-2xl relative z-10">
        <div class="overflow-x-auto custom-scrollbar">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-50 dark:bg-black/40 border-b border-slate-100 dark:border-white/5">
                <th class="px-8 py-5 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em]">Estampa de Tiempo</th>
                <th class="px-8 py-5 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em]">Acción / Protocolo</th>
                <th class="px-8 py-5 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em]">Entidad / Referencia</th>
                <th class="px-8 py-5 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em]">Operador</th>
                <th class="px-8 py-5 text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.25em] text-right">Análisis</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-white/5">
              @for (log of logs(); track log.id) {
                <tr class="hover:bg-slate-50 dark:hover:bg-white/[0.03] transition-all group cursor-pointer" (click)="selectedLog.set(log)">
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-4">
                      <div class="w-1 bg-slate-200 dark:bg-white/10 group-hover:bg-primary h-10 rounded-full transition-all"></div>
                      <div class="flex flex-col">
                        <span class="text-xs font-mono font-black text-slate-400 dark:text-slate-500 tabular-nums italic">
                          {{ log.timestamp | date:'dd/MM/yyyy' }}
                        </span>
                        <span class="text-[14px] font-mono font-bold text-slate-900 dark:text-primary tracking-tight tabular-nums">
                          {{ log.timestamp | date:'HH:mm:ss' }}
                        </span>
                      </div>
                    </div>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-3">
                      <div [class]="getActionClass(log.action)" class="w-8 h-8 rounded-lg border flex items-center justify-center shadow-sm">
                        <mat-icon class="text-[16px]">{{ getActionIcon(log.action) }}</mat-icon>
                      </div>
                      <div class="flex flex-col">
                        <span [class]="getActionTextClass(log.action)" class="text-[10px] font-black uppercase tracking-widest leading-none">
                          {{ log.action }}
                        </span>
                        <span class="text-[8px] text-slate-400 dark:text-slate-500 font-mono mt-1 tracking-tighter">TRX-{{ log.trace_id?.split('-')?.[0] || 'UNSET' }}</span>
                      </div>
                    </div>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex flex-col">
                      <div class="flex items-center gap-2">
                        <span class="text-[11px] font-black text-slate-900 dark:text-white uppercase tracking-tight italic">{{ log.table_name }}</span>
                        @if (log.action === 'DENSITY_OVERFLOW') {
                          <span class="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
                        }
                      </div>
                      <span class="text-[9px] font-mono text-slate-400 dark:text-slate-500 mt-0.5">{{ getReadableReference(log) }}</span>
                    </div>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-2">
                      <div class="w-6 h-6 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-white/10 flex items-center justify-center">
                        <mat-icon class="text-[12px] text-slate-400">person</mat-icon>
                      </div>
                      <span class="text-[11px] font-black text-slate-600 dark:text-slate-400 uppercase tracking-tighter">{{ log.user_id }}</span>
                    </div>
                  </td>
                  <td class="px-8 py-6 text-right">
                    <button class="w-10 h-10 flex items-center justify-center text-primary bg-primary/5 hover:bg-primary/20 border border-primary/20 rounded-xl transition-all shadow-sm ml-auto group-hover:scale-110">
                      <mat-icon>analytics</mat-icon>
                    </button>
                  </td>
                </tr>
              }
              @if (logs().length === 0) {
                <tr>
                  <td colspan="5" class="px-8 py-24 text-center">
                    <div class="flex flex-col items-center gap-4 opacity-20">
                      <mat-icon class="text-6xl text-slate-400">search_off</mat-icon>
                      <span class="uppercase text-[12px] font-black tracking-[0.5em] text-slate-400">No se encontraron registros forenses</span>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Premium Detail Drawer-Modal -->
      @if (selectedLog(); as log) {
        <div class="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center p-4 md:p-12 animate-fade-in" (click)="selectedLog.set(null)">
          <div class="bg-white dark:bg-slate-900 w-full max-w-6xl h-full max-h-[85vh] overflow-hidden flex flex-col p-0 border border-slate-200 dark:border-white/10 rounded-[32px] shadow-[0_0_100px_rgba(0,0,0,0.3)] relative" (click)="$event.stopPropagation()">
            
            <!-- Scanline Effect -->
            <div class="absolute inset-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%] z-20"></div>

            <!-- Modal Header -->
            <div class="flex items-center justify-between p-8 border-b border-slate-100 dark:border-white/10 bg-slate-50 dark:bg-black/20 relative z-30">
              <div class="flex items-center gap-6">
                <div [class]="getActionClass(log.action)" class="w-16 h-16 rounded-2xl border flex items-center justify-center shadow-xl">
                  <mat-icon class="text-3xl">{{ getActionIcon(log.action) }}</mat-icon>
                </div>
                <div>
                  <h3 class="text-3xl font-black text-slate-900 dark:text-white uppercase tracking-tighter italic leading-none">Expediente de Auditoría</h3>
                  <div class="flex items-center gap-3 mt-3">
                    <span class="text-[10px] font-mono text-primary font-bold px-2 py-0.5 bg-primary/10 rounded">ID-AUDIT: {{ log.id?.split('-')?.[0] || 'N/A' }}</span>
                    <span class="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-700"></span>
                    <span class="text-[10px] font-mono text-slate-400 dark:text-slate-500 tracking-tighter">TRACE: {{ log.trace_id }}</span>
                  </div>
                </div>
              </div>
              <button (click)="selectedLog.set(null)" class="w-12 h-12 flex items-center justify-center bg-white dark:bg-white/5 hover:bg-rose-50 dark:hover:bg-rose-500/20 text-slate-400 hover:text-rose-500 rounded-full transition-all border border-slate-200 dark:border-white/10 group">
                <mat-icon class="group-hover:rotate-90 transition-transform">close</mat-icon>
              </button>
            </div>

            <!-- Modal Body -->
            <div class="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8 relative z-30 bg-white dark:bg-transparent">
              <!-- Identity Grid -->
              <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="p-6 bg-slate-50 dark:bg-black/30 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-primary/30 transition-colors">
                  <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-2">Protocolo Operativo</span>
                  <span [class]="getActionTextClass(log.action)" class="text-sm font-black italic uppercase leading-none">{{ log.action }}</span>
                </div>
                <div class="p-6 bg-slate-50 dark:bg-black/30 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-primary/30 transition-colors">
                  <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-2">Entidad Afectada</span>
                  <span class="text-sm font-black text-slate-900 dark:text-white uppercase italic leading-none">{{ log.table_name }}</span>
                </div>
                <div class="p-6 bg-slate-50 dark:bg-black/30 rounded-2xl border border-slate-100 dark:border-white/5 hover:border-primary/30 transition-colors col-span-2">
                  <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest block mb-2">Referencia Única (Record ID)</span>
                  <span class="text-xs font-mono font-bold text-primary truncate block leading-none tabular-nums">{{ log.record_id }}</span>
                </div>
              </div>

              <!-- Value Comparison -->
              <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-4">
                <div class="space-y-3">
                  <div class="flex items-center justify-between px-2">
                    <h4 class="text-[10px] font-black text-rose-500 uppercase tracking-[0.3em] italic">Estado Anterior (Snapshot)</h4>
                    <mat-icon class="text-rose-500/30 text-sm">history</mat-icon>
                  </div>
                  <div class="group relative">
                    <div class="absolute -inset-0.5 bg-rose-500/10 rounded-2xl blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                    <pre class="relative bg-slate-50 dark:bg-black/60 p-6 rounded-2xl border border-slate-200 dark:border-white/10 text-[11px] font-mono text-slate-600 dark:text-slate-400 overflow-x-auto min-h-[250px] shadow-sm custom-scrollbar leading-relaxed">
                      @if (log.old_value && (log.old_value | json) !== '{}') {
                        {{ log.old_value | json }}
                      } @else {
                        <div class="flex flex-col items-center justify-center h-48 opacity-20">
                          <mat-icon class="text-6xl mb-4 text-slate-400">block</mat-icon>
                          <span class="uppercase font-black text-[12px] tracking-widest text-slate-400">Inexistente / NULL</span>
                        </div>
                      }
                    </pre>
                  </div>
                </div>

                <div class="space-y-3">
                  <div class="flex items-center justify-between px-2">
                    <h4 class="text-[10px] font-black text-emerald-500 uppercase tracking-[0.3em] italic">Estado Final (Comprometido)</h4>
                    <mat-icon class="text-emerald-500/30 text-sm">verified</mat-icon>
                  </div>
                  <div class="group relative">
                    <div class="absolute -inset-0.5 bg-emerald-500/10 rounded-2xl blur opacity-0 group-hover:opacity-100 transition duration-500"></div>
                    <pre class="relative bg-slate-50 dark:bg-black/60 p-6 rounded-2xl border border-slate-200 dark:border-white/10 text-[11px] font-mono text-slate-900 dark:text-emerald-50/70 overflow-x-auto min-h-[250px] shadow-sm custom-scrollbar leading-relaxed">
                      @if (log.new_value && (log.new_value | json) !== '{}') {
                        {{ log.new_value | json }}
                      } @else {
                        <div class="flex flex-col items-center justify-center h-48 opacity-20">
                          <mat-icon class="text-6xl mb-4 text-slate-400">delete_sweep</mat-icon>
                          <span class="uppercase font-black text-[12px] tracking-widest text-slate-400">Registro Eliminado</span>
                        </div>
                      }
                    </pre>
                  </div>
                </div>
              </div>

              <!-- Footer Metadata -->
              <div class="pt-8 border-t border-slate-100 dark:border-white/5 flex flex-wrap justify-between items-center gap-4">
                <div class="flex items-center gap-2 text-slate-400 dark:text-slate-500">
                  <mat-icon class="text-sm">schedule</mat-icon>
                  <span class="text-[10px] font-mono uppercase tracking-widest italic font-bold">Ejecución: {{ log.timestamp | date:'full' }}</span>
                </div>
                <div class="flex items-center gap-4">
                  <div class="flex items-center gap-2 text-slate-400 dark:text-slate-500">
                    <mat-icon class="text-sm">fingerprint</mat-icon>
                    <span class="text-[10px] font-mono uppercase tracking-widest font-bold">Sello Digital: {{ log.id }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; position: relative; }
    .custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    pre { white-space: pre-wrap; word-break: break-all; }
    .animate-fade-in { animation: fadeIn 0.4s ease-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
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

  getReadableReference(log: AuditLog): string {
    const val = log.new_value || log.old_value;
    if (!val) return log.record_id || 'N/A';
    
    // Si es un objeto vacío (ocurre a veces en el API)
    if (typeof val === 'object' && Object.keys(val).length === 0) return log.record_id || 'N/A';

    // Priorizar identificadores industriales legibles
    if (log.table_name?.includes('product')) {
       return val.sku || val.code || log.record_id;
    }
    
    if (log.table_name?.includes('location')) {
       return val.path || val.code || log.record_id;
    }

    if (log.table_name?.includes('warehouse')) {
       return val.code || val.name || log.record_id;
    }

    return log.record_id || 'N/A';
  }

  getActionClass(action: string) {
    switch (action) {
      case 'INSERT': 
      case 'SEED_CREATE': 
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.1)]';
      case 'UPDATE': 
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30 shadow-[0_0_15px_rgba(245,158,11,0.1)]';
      case 'DELETE': 
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.1)]';
      case 'DENSITY_OVERFLOW': 
        return 'bg-red-600/20 text-red-500 border-red-600/50 shadow-[0_0_20px_rgba(220,38,38,0.2)] animate-pulse';
      case 'CREATE_MOVEMENT':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.1)]';
      case 'UNAUTHORIZED_WAREHOUSE_ACCESS': 
        return 'bg-black text-rose-600 border-rose-900 shadow-[0_0_30px_rgba(225,29,72,0.3)]';
      default: 
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  }

  getActionTextClass(action: string) {
    switch (action) {
      case 'INSERT': 
      case 'SEED_CREATE': return 'text-emerald-500';
      case 'UPDATE': return 'text-amber-500';
      case 'DELETE': return 'text-rose-500';
      case 'DENSITY_OVERFLOW': return 'text-red-500 font-black underline decoration-double';
      case 'CREATE_MOVEMENT': return 'text-indigo-400';
      case 'UNAUTHORIZED_WAREHOUSE_ACCESS': return 'text-rose-700';
      default: return 'text-slate-500';
    }
  }

  getActionIcon(action: string) {
    switch (action) {
      case 'INSERT': return 'add_circle';
      case 'SEED_CREATE': return 'auto_awesome';
      case 'UPDATE': return 'edit_note';
      case 'DELETE': return 'delete_forever';
      case 'DENSITY_OVERFLOW': return 'report_problem';
      case 'CREATE_MOVEMENT': return 'swap_horiz';
      case 'UNAUTHORIZED_WAREHOUSE_ACCESS': return 'gpp_bad';
      default: return 'event_note';
    }
  }
}
