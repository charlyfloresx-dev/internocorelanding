// temp_future/src/app/modules/dashboard/dashboard.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TransactionTimelineComponent } from './components/transaction-timeline/transaction-timeline.component';
import { IntegrityMonitorComponent } from './components/integrity-monitor/integrity-monitor.component';
import { LatencyMonitorComponent } from './components/latency-monitor/latency-monitor.component';
import { UsageMonitorComponent } from './components/usage-monitor/usage-monitor.component';
import { TenantDashboardComponent } from './components/tenant-view/tenant-dashboard.component';
import { MatIconModule } from '@angular/material/icon';
import { signal } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule, 
    TransactionTimelineComponent, 
    IntegrityMonitorComponent, 

    LatencyMonitorComponent,
    UsageMonitorComponent,
    TenantDashboardComponent,
    MatIconModule
  ],
  template: `
    <div class="min-h-screen p-6 md:p-12 space-y-10 animate-in fade-in duration-1000 relative overflow-hidden transition-colors
                bg-white dark:bg-ic-dark">
      
      <!-- HUD Elements (Only for Dark Mode) -->
      <div class="fixed inset-0 pointer-events-none opacity-20 dark:block hidden">
        <div class="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,229,255,0.05),transparent_70%)]"></div>
        <div class="scanline absolute top-0 left-0 w-full h-1 bg-primary/20 animate-scan-line"></div>
      </div>
 
      <!-- Top Header Area -->
      <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-20 border-b border-slate-100 dark:border-white/5 pb-8">
        <div class="group">
          <h1 class="text-3xl md:text-5xl font-black italic tracking-tighter uppercase mb-2 
                     text-slate-900 dark:text-white dark:drop-shadow-[0_0_15px_rgba(0,229,255,0.5)]">
            Mission <span class="text-primary group-hover:text-amber-500 transition-colors">Control</span>
          </h1>
          <div class="flex items-center gap-3">
             <div class="px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-[8px] text-primary font-black uppercase tracking-widest">
               V.4.2.0-Alpha — Forensic Node
             </div>
             <p class="text-[10px] text-slate-500 dark:text-slate-400 font-bold uppercase tracking-[0.4em] hidden md:block">Real-Time Observability Engine</p>
          </div>
        </div>

        <!-- View Switcher -->
        <div class="flex p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-slate-200 dark:border-white/10 relative z-30">
          <button (click)="activeView.set('FORENSIC')" 
                  [class.bg-white]="activeView() === 'FORENSIC'"
                  [class.dark:bg-white/10]="activeView() === 'FORENSIC'"
                  [class.shadow-sm]="activeView() === 'FORENSIC'"
                  class="px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all
                         text-slate-500 dark:text-slate-400"
                  [class.text-primary]="activeView() === 'FORENSIC'">
            Protocolo Forense
          </button>
          <button (click)="activeView.set('TENANT')" 
                  [class.bg-white]="activeView() === 'TENANT'"
                  [class.dark:bg-white/10]="activeView() === 'TENANT'"
                  [class.shadow-sm]="activeView() === 'TENANT'"
                  class="px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all
                         text-slate-500 dark:text-slate-400"
                  [class.text-primary]="activeView() === 'TENANT'">
            Operación Empresa
          </button>
        </div>
      </div>

      <!-- TENANT VIEW -->
      <ng-container *ngIf="activeView() === 'TENANT'">
        <app-tenant-dashboard></app-tenant-dashboard>
      </ng-container>

      <!-- FORENSIC GRID (Original) -->
      <div *ngIf="activeView() === 'FORENSIC'" class="grid grid-cols-1 xl:grid-cols-3 gap-8 relative z-10 animate-in fade-in zoom-in-95 duration-500">
        
        <!-- Main Stats & Charts (2/3 width) -->
        <div class="xl:col-span-2 space-y-8">
           <div class="bg-white dark:bg-transparent border border-slate-200 dark:border-white/10 rounded-2xl p-1 shadow-sm">
             <app-integrity-monitor></app-integrity-monitor>
           </div>
           
           <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
             <div class="bg-white dark:bg-transparent border border-slate-200 dark:border-white/10 rounded-2xl p-1 shadow-sm">
                <app-usage-monitor></app-usage-monitor>
             </div>
             <div class="bg-slate-50 dark:bg-white/5 rounded-2xl p-8 flex items-center justify-center border border-dashed border-slate-200 dark:border-white/10">
                <span class="text-slate-400 dark:text-white/20 font-black uppercase text-[10px] tracking-[0.3em]">Reserved for Network Ops</span>
             </div>
           </div>

           <!-- Latency Oscilloscope Area -->
           <div class="h-[400px] bg-white dark:bg-transparent border border-slate-200 dark:border-white/10 rounded-2xl overflow-hidden relative shadow-sm">
              <div class="absolute top-4 left-4 z-20 px-3 py-1 bg-slate-900 dark:bg-black/60 rounded text-[9px] font-mono text-white dark:text-primary border border-white/10">
                DATA_STREAM: [LATENCY_OSCILLOSCOPE]
              </div>
              <app-latency-monitor></app-latency-monitor>
           </div>
        </div>

        <!-- Real-time Timeline (1/3 width) -->
        <div class="xl:col-span-1 h-[820px] bg-white dark:bg-transparent border border-slate-200 dark:border-white/10 rounded-2xl p-1 shadow-sm">
           <app-transaction-timeline></app-transaction-timeline>
        </div>

      </div>

    </div>
  `
})
export class DashboardComponent {
  activeView = signal<'FORENSIC' | 'TENANT'>('TENANT');
}
