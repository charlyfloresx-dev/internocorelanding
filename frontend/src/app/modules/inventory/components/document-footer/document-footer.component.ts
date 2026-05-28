// temp_future/src/app/modules/inventory/components/document-footer/document-footer.component.ts
import { Component, Input, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LocalDatePipe } from '../../../../shared/pipes/local-date.pipe';

@Component({
  selector: 'app-document-footer',
  standalone: true,
  imports: [CommonModule, LocalDatePipe],
  template: `
    <div class="glass-effect rounded-2xl p-6 border border-white/5 mt-6">
      <div class="flex flex-col md:flex-row justify-between items-center gap-6">
        
        <!-- Discrepancy Alert -->
        <div class="flex items-center gap-4 transition-all duration-500" 
             [class.opacity-0]="!hasDiscrepancy()"
             [class.animate-pulse]="hasDiscrepancy()">
           <div class="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center text-amber-500 border border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
             <span class="material-icons">warning</span>
           </div>
           <div>
             <p class="text-[10px] font-black text-amber-500 uppercase tracking-widest">Alerta de Integridad</p>
             <p class="text-[9px] text-slate-500 uppercase">Se detectaron discrepancias en la masa de las partidas.</p>
           </div>
        </div>

        <!-- Totals -->
        <div class="flex items-center gap-12">
          <div class="text-right">
            <p class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">Masa Total Calculada</p>
            <p class="text-3xl font-black text-white tracking-tighter">
              {{ totalWeight | number:'1.2-2' }} 
              <span class="text-xs text-cyan-500 uppercase ml-2 tracking-widest">Kg</span>
            </p>
          </div>
          
          <div class="text-right border-l border-white/10 pl-12">
            <p class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">Unidades Totales</p>
            <p class="text-3xl font-black text-white tracking-tighter">
              {{ totalQuantity | number }} 
              <span class="text-xs text-slate-500 uppercase ml-2 tracking-widest">Items</span>
            </p>
          </div>
        </div>
      </div>

      <!-- Audit Tracking Shadow -->
      <div class="mt-8 pt-6 border-t border-white/5 flex justify-between items-center text-[8px] font-bold text-slate-600 uppercase tracking-[0.3em]">
        <span>REGISTRO GENERADO POR: CHARLY FLORES</span>
        <span class="text-cyan-900/50">INTERNO CORE v2.1.0 // {{ today | localDate:'medium' }}</span>
      </div>
    </div>
  `,
  styles: [`
    .glass-effect {
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(8px);
    }
  `]
})
export class DocumentFooterComponent {
  @Input() totalWeight: number = 0;
  @Input() totalQuantity: number = 0;
  @Input() movements: any[] = [];

  today = new Date();

  hasDiscrepancy = computed(() => {
    return this.movements.some(m => m.is_weight_mismatch);
  });
}
