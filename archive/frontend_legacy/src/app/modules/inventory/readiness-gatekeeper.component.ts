import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-inventory-readiness-gatekeeper',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="fixed inset-0 z-[100] bg-slate-950/90 backdrop-blur-md flex items-center justify-center p-4">
      <div class="w-full max-w-2xl bg-ic-slate border border-white/10 rounded-xl shadow-2xl overflow-hidden animate-fade-in-up">
        <!-- Header -->
        <div class="p-8 border-b border-white/5 bg-gradient-to-r from-primary/10 to-transparent">
          <div class="flex items-center gap-4 mb-4">
            <div class="w-12 h-12 rounded-lg bg-primary/20 flex items-center justify-center text-primary border border-primary/30">
              <mat-icon class="text-2xl">security</mat-icon>
            </div>
            <div>
              <h2 class="text-2xl font-black text-white uppercase tracking-tighter italic">Configuración Pendiente</h2>
              <p class="text-surface-text-muted text-xs font-mono uppercase tracking-widest mt-1">Verificación de Requisitos Operativos</p>
            </div>
          </div>
          <p class="text-sm text-slate-400">
            Para garantizar la integridad del Kardex y los reportes financieros, su empresa debe completar la configuración mínima antes de habilitar el Control de Misión.
          </p>
        </div>

        <!-- Steps -->
        <div class="p-8 space-y-4">
          @for (step of readiness?.steps; track step.task || step.name) {
            <div class="flex items-center justify-between p-4 rounded bg-white/5 border border-white/5 group hover:border-primary/30 transition-all">
              <div class="flex items-center gap-4">
                <div [class]="(step.is_completed !== undefined ? step.is_completed : step.completed) ? 'text-emerald-500' : 'text-slate-600'" class="transition-colors">
                  <mat-icon>{{ (step.is_completed !== undefined ? step.is_completed : step.completed) ? 'check_circle' : 'radio_button_unchecked' }}</mat-icon>
                </div>
                <div>
                  <div class="text-[11px] font-black uppercase tracking-widest" [class.text-white]="!(step.is_completed !== undefined ? step.is_completed : step.completed)" [class.text-emerald-400]="(step.is_completed !== undefined ? step.is_completed : step.completed)">
                    {{ step.task || step.name }}
                  </div>
                  <div class="text-[9px] font-bold uppercase tracking-tighter" [class]="step.importance === 'Critical' ? 'text-red-500' : 'text-amber-500'">
                    Prioridad: {{ step.importance || 'Alta' }}
                  </div>
                </div>
              </div>
              
              @if (!(step.is_completed !== undefined ? step.is_completed : step.completed)) {
                <a [href]="step.action_link" class="px-4 py-1.5 bg-white/5 hover:bg-primary hover:text-white rounded text-[10px] font-black uppercase tracking-widest transition-all">
                  Configurar
                </a>
              } @else {
                <div class="text-[9px] font-black text-emerald-500 uppercase tracking-widest italic opacity-60">
                  Completado
                </div>
              }
            </div>
          }
        </div>

        <!-- Footer -->
        <div class="p-6 bg-black/40 border-t border-white/5 flex justify-between items-center">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></div>
            <span class="text-[10px] font-bold text-amber-500 uppercase tracking-widest">Esperando Requisitos Críticos</span>
          </div>
          <button (click)="onRefresh.emit()" class="btn-primary py-2 px-6 text-[10px] uppercase h-10">
            <mat-icon class="text-sm">refresh</mat-icon>
            Re-verificar
          </button>
        </div>
      </div>
    </div>
  `
})
export class InventoryReadinessGatekeeperComponent {
  @Input() readiness: any;
  @Output() onRefresh = new EventEmitter<void>();
}
