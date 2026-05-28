// temp_future/src/app/modules/dashboard/components/transaction-timeline/transaction-timeline.component.ts
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService } from '../../../../core/services/dashboard.service';
import { MatIconModule } from '@angular/material/icon';
import { LocalDatePipe } from '../../../../shared/pipes/local-date.pipe';

@Component({
  selector: 'app-transaction-timeline',
  standalone: true,
  imports: [CommonModule, MatIconModule, LocalDatePipe],
  template: `
    <div class="rounded-3xl flex flex-col h-full overflow-hidden transition-all
                bg-white border border-slate-200 dark:bg-slate-900/40 dark:border-white/5">
      <!-- Header -->
      <div class="p-6 border-b flex justify-between items-center border-slate-100 dark:border-white/5">
        <div>
          <h3 class="text-xs font-black uppercase tracking-[0.2em] mb-1 text-slate-900 dark:text-white">Timeline de Auditoría</h3>
          <p class="text-[9px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">Registro de Transacciones en Vivo</p>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full animate-pulse bg-emerald-500 dark:bg-neon-green shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
          <span class="text-[9px] font-black uppercase tracking-tighter text-emerald-600 dark:text-neon-green">Live Feed</span>
        </div>
      </div>

      <!-- Timeline Feed -->
      <div class="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
        @for (doc of dashboard.transactionFeed(); track doc.id) {
          <div class="group relative flex gap-4 p-4 border rounded-2xl transition-all animate-in slide-in-from-right-4 duration-500
                      bg-slate-50 border-slate-100 hover:bg-slate-100
                      dark:bg-white/[0.02] dark:hover:bg-white/[0.05] dark:border-white/5">
            
            <!-- Icon/Type indicator -->
            <div class="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-sm border relative shadow-inner
                        bg-slate-200 border-slate-300 dark:bg-ic-dark dark:border-white/10">
                <mat-icon [ngClass]="{
                   'text-emerald-500 dark:text-neon-green': doc.concept_type === 'ENTRADA',
                   'text-red-500 dark:text-red-400': doc.concept_type === 'SALIDA',
                   'text-primary dark:text-neon-cyan': doc.concept_type === 'TRASPASO'
                }">
                  {{ getIcon(doc.concept_type) }}
                </mat-icon>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <div class="flex justify-between items-start mb-1">
                <p class="text-[10px] font-black uppercase tracking-tighter italic text-slate-900 dark:text-white">
                  {{ doc.folio }} <span class="text-slate-500 dark:text-slate-600 ml-2">[{{ doc.concept_type }}]</span>
                </p>
                <span class="text-[9px] font-bold tabular-nums text-slate-400 dark:text-slate-500">{{ doc.created_at | localDate:'HH:mm:ss' }}</span>
              </div>
              <p class="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                <span class="text-primary dark:text-cyan-400/80 mr-1 font-black">#{{ doc.created_by }}</span>
                procesó documento en Almacén <span class="text-slate-900 dark:text-white">{{ doc.warehouse_id | slice:-6 }}</span>
              </p>
              
              <!-- Integrity Badge -->
              @if (hasDiscrepancy(doc)) {
                <div class="mt-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full border w-fit bg-red-500/10 border-red-500/20">
                  <mat-icon class="!text-[10px] !w-[10px] !h-[10px] text-red-500">warning</mat-icon>
                  <span class="text-[8px] text-red-500 font-black uppercase tracking-widest">Discrepancia Forense</span>
                </div>
              }
            </div>

            <!-- Glow Effect on hover (Dark Only) -->
            <div class="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl pointer-events-none dark:block hidden"></div>
          </div>
        } @empty {
          <div class="h-full flex flex-col items-center justify-center text-center p-12 opacity-30 italic text-slate-400 dark:text-white">
            <mat-icon class="text-4xl mb-4">history</mat-icon>
            <p class="text-xs font-bold uppercase tracking-widest">Esperando Transacciones...</p>
          </div>
        }
      </div>

      <!-- Footer Action -->
      <div class="p-4 border-t text-center bg-slate-50 dark:bg-black/20 border-slate-100 dark:border-white/5">
        <button class="text-[9px] font-black uppercase tracking-[0.3em] transition-all text-primary/70 hover:text-primary dark:text-cyan-400/70 dark:hover:text-cyan-400">
          VER LEDGER COMPLETO
        </button>
      </div>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }
    .dark .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); }
  `]
})
export class TransactionTimelineComponent {
  dashboard = inject(DashboardService);

  getIcon(type: string): string {
    switch(type) {
      case 'ENTRADA': return 'south_west';
      case 'SALIDA': return 'north_east';
      case 'TRASPASO': return 'swap_horiz';
      default: return 'receipt';
    }
  }

  hasDiscrepancy(doc: any): boolean {
    return doc.movements?.some((m: any) => m.is_weight_mismatch);
  }
}
