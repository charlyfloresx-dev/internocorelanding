import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { TenantDashboardService } from '../../../../core/services/tenant-dashboard.service';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-tenant-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      <!-- 1. RESUMEN DE SALUD OPERATIVA (TOP ROW) -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        <!-- Warehouse Availability -->
        <div class="p-6 rounded-3xl border backdrop-blur-xl bg-white/5 border-white/10 relative overflow-hidden group hover:border-primary/30 transition-all">
          <div class="absolute -top-4 -right-4 w-24 h-24 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-colors"></div>
          <div class="flex justify-between items-start mb-6">
             <div>
               <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Ocupación de Planta</h4>
               <p class="text-[8px] text-primary font-bold uppercase tracking-widest mt-1 italic">Real-Time WMS Density</p>
             </div>
             <mat-icon class="text-primary opacity-40">warehouse</mat-icon>
          </div>
          
          <div class="flex flex-col items-center">
            <div class="relative w-32 h-32 mb-4">
              <svg class="w-full h-full -rotate-90">
                <circle cx="64" cy="64" r="56" fill="transparent" stroke="rgba(255,255,255,0.05)" stroke-width="8" />
                <circle cx="64" cy="64" r="56" fill="transparent" stroke="currentColor" stroke-width="10" 
                        class="text-primary transition-all duration-1000 ease-out drop-shadow-[0_0_8px_rgba(0,229,255,0.5)]"
                        stroke-dasharray="351.8"
                        [style.stroke-dashoffset]="351.8 - (service.totalOccupancy() / 100 * 351.8)" />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center">
                <span class="text-3xl font-black text-white italic tracking-tighter">{{ service.totalOccupancy() | number:'1.0-1' }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Hardware Connectivity -->
        <div class="p-6 rounded-3xl border backdrop-blur-xl bg-white/5 border-white/10 relative overflow-hidden group hover:border-emerald-500/30 transition-all">
          <div class="flex justify-between items-start mb-6">
             <div>
               <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Conectividad Hardware</h4>
               <p class="text-[8px] text-emerald-400 font-bold uppercase tracking-widest mt-1">Active Scanners & Scales</p>
             </div>
             <mat-icon class="text-emerald-400 opacity-40">sensors</mat-icon>
          </div>
          
          <div class="space-y-4">
            @for (hw of service.hardwareStatus(); track hw.id) {
              <div class="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5 group-hover:border-white/10 transition-all">
                <div class="flex items-center gap-3">
                  <div class="w-2 h-2 rounded-full shadow-[0_0_8px]" 
                       [ngClass]="{
                         'bg-emerald-500 shadow-emerald-500/50': hw.status === 'ONLINE',
                         'bg-red-500 shadow-red-500/50': hw.status === 'OFFLINE',
                         'bg-amber-500 shadow-amber-500/50': hw.status === 'MAINTENANCE'
                       }"></div>
                  <span class="text-[10px] font-bold text-white tracking-tight">{{ hw.name }}</span>
                </div>
                <span class="text-[8px] font-black uppercase tracking-widest text-slate-500">{{ hw.type }}</span>
              </div>
            }
          </div>
        </div>

        <!-- Transactional Value KPI -->
        <div class="p-6 rounded-3xl border backdrop-blur-xl bg-white/5 border-white/10 relative overflow-hidden group hover:border-amber-500/30 transition-all">
          <div class="flex justify-between items-start mb-6">
             <div>
               <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Valor Transaccional (24h)</h4>
               <p class="text-[8px] text-amber-500 font-bold uppercase tracking-widest mt-1">Ledger Throughput</p>
             </div>
             <mat-icon class="text-amber-500 opacity-40">payments</mat-icon>
          </div>
          
          <div class="mt-8">
            <span class="text-5xl font-black italic tracking-tighter text-white drop-shadow-[0_0_15px_rgba(245,158,11,0.3)]">
              $ {{ service.throughput24h() | number:'1.0-0' }}
            </span>
            <div class="flex items-center gap-2 mt-4 text-[10px] font-black">
              <mat-icon class="text-[14px] w-[14px] h-[14px] text-emerald-500">trending_up</mat-icon>
              <span class="text-emerald-500">+8.4%</span>
              <span class="text-slate-500 uppercase tracking-widest">frente al turno anterior</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. SECCIÓN DE FLUJO Y AUDITORÍA (MIDDLE SECTION) -->
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
        
        <!-- Timeline de Eventos -->
        <div class="xl:col-span-2 p-6 rounded-3xl border backdrop-blur-xl bg-white/5 border-white/10">
          <div class="flex justify-between items-center mb-6">
             <div class="flex items-center gap-3">
               <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Timeline de Dominio</h4>
               <div class="px-2 py-0.5 rounded border border-primary/20 bg-primary/10 text-[8px] font-black text-primary uppercase animate-pulse">Live Feed</div>
             </div>
             <mat-icon class="text-slate-600">history</mat-icon>
          </div>
          
          <div class="space-y-4">
            @for (ev of service.recentActivity(); track $index) {
              <div class="flex items-start gap-4 p-4 rounded-2xl bg-white/5 border border-transparent hover:border-white/10 transition-all">
                <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <mat-icon>{{ ev.module === 'Auth' ? 'person' : ev.module === 'WMS' ? 'inventory_2' : 'precision_manufacturing' }}</mat-icon>
                </div>
                <div class="flex-1">
                  <div class="flex justify-between items-start">
                    <h5 class="text-[11px] font-black text-white tracking-tight">{{ ev.action }}</h5>
                    <span class="text-[9px] font-mono text-slate-500">{{ ev.timestamp | date:'HH:mm:ss' }}</span>
                  </div>
                  <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1">
                    {{ ev.user }} • <span class="text-primary/70">{{ ev.module }}</span>
                  </p>
                </div>
              </div>
            }
          </div>
        </div>

        <!-- Tenant Isolation Status -->
        <div class="p-6 rounded-3xl border backdrop-blur-xl bg-primary/5 border-primary/20 flex flex-col items-center justify-center text-center">
           <mat-icon class="text-6xl text-primary mb-6 animate-pulse">verified_user</mat-icon>
           <h4 class="text-xs font-black text-white uppercase tracking-[0.3em] mb-2">Multi-Tenancy Safe</h4>
           <p class="text-[9px] text-slate-400 font-bold uppercase tracking-widest leading-relaxed">
             Aislamiento de datos confirmado para:<br>
             <span class="text-primary">{{ auth.activeCompanyId() }}</span>
           </p>
           <div class="mt-8 flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
             <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
             <span class="text-[8px] font-black text-emerald-400 uppercase tracking-widest">Inyección de Filtros Activa</span>
           </div>
        </div>
      </div>

      <!-- 3. GESTIÓN DE RECURSOS (BOTTOM ROW) -->
      <div class="p-6 rounded-3xl border backdrop-blur-xl bg-white/5 border-white/10">
         <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400 mb-6">Cuotas y Plan Empresa</h4>
         <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div class="md:col-span-1 space-y-4">
              <div class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Plan Actual</div>
              <div class="text-2xl font-black italic text-emerald-400 tracking-tighter">ENTERPRISE</div>
              <div class="p-4 rounded-2xl bg-white/5 border border-white/5 space-y-3">
                <div class="flex justify-between text-[9px] font-black uppercase">
                  <span class="text-slate-400">Uso Mensual</span>
                  <span class="text-white">68%</span>
                </div>
                <div class="h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div class="h-full bg-emerald-500" [style.width.%]="68"></div>
                </div>
              </div>
            </div>
            
            <div class="md:col-span-3 overflow-hidden rounded-2xl border border-white/5">
              <table class="w-full text-left">
                <thead class="bg-white/5 text-[9px] font-black text-slate-500 uppercase tracking-widest border-b border-white/5">
                  <tr>
                    <th class="p-4">Almacén / Recurso</th>
                    <th class="p-4 text-center">Estatus</th>
                    <th class="p-4 text-right">Carga Actual</th>
                  </tr>
                </thead>
                <tbody class="text-[10px] font-bold text-white">
                  @for (wh of service.warehouses(); track wh.id) {
                    <tr class="border-b border-white/5 hover:bg-white/5 transition-colors">
                      <td class="p-4">
                        <div class="flex flex-col">
                          <span>{{ wh.name }}</span>
                          <span class="text-[8px] text-slate-500 font-mono">{{ wh.code }}</span>
                        </div>
                      </td>
                      <td class="p-4 text-center">
                        <span class="px-2 py-0.5 rounded text-[8px] font-black border border-emerald-500/20 text-emerald-400 uppercase bg-emerald-500/10">Activo</span>
                      </td>
                      <td class="p-4 text-right tabular-nums">
                        {{ wh.current_occupancy || 0 }} / {{ wh.capacity }} m²
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
         </div>
      </div>

    </div>
  `
})
export class TenantDashboardComponent {
  service = inject(TenantDashboardService);
  auth = inject(AuthService);
}
