import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { NotificationHubService } from '../../../core/services/notification-hub.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-density-alert-panel',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe],
  template: `
    @if (overflowAlerts().length > 0) {
      <div class="industrial-card p-6 border-amber-500/30 bg-amber-500/5 overflow-hidden relative">
        <!-- Background Glow -->
        <div class="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/10 blur-[80px] rounded-full"></div>
        
        <div class="flex items-center justify-between mb-6 relative">
          <h2 class="text-xs font-black text-amber-500 uppercase tracking-[0.2em] flex items-center gap-2">
            <mat-icon class="text-sm animate-bounce">warning</mat-icon>
            {{ 'inventory.alerts.density_title' | translate:'Violaciones de Densidad (God Mode)' }}
          </h2>
          <span class="text-[10px] bg-amber-500 text-black px-2 py-0.5 rounded font-black">
            {{ overflowAlerts().length }} ACTIVAS
          </span>
        </div>

        <div class="space-y-4 relative">
          @for (alert of overflowAlerts(); track alert.id) {
            <div class="p-4 bg-surface-bg/80 border border-amber-500/20 rounded-xl hover:border-amber-500/40 transition-all group overflow-hidden">
              <div class="flex items-start justify-between">
                <div class="flex flex-col">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-[10px] font-black text-amber-500 font-mono tracking-tighter uppercase">
                      {{ alert.title }}
                    </span>
                    @if (alert.priority === 'HIGH') {
                      <span class="text-[8px] bg-red-500 text-white px-1 rounded font-bold">CRÍTICO</span>
                    }
                  </div>
                  <p class="text-xs text-surface-text-muted font-medium mb-3">
                    {{ alert.message }}
                  </p>
                </div>
                
                <button 
                  (click)="hub.markAsRead(alert.id)"
                  class="p-2 hover:bg-amber-500/10 rounded-lg text-surface-text-muted hover:text-amber-500 transition-colors"
                >
                  <mat-icon class="text-sm">check_circle</mat-icon>
                </button>
              </div>

              <div class="flex items-center gap-4 mt-2">
                 <div class="flex flex-col">
                    <span class="text-[8px] text-surface-text-muted uppercase font-bold">RECURSO</span>
                    <span class="text-[10px] font-mono text-surface-text font-black">{{ 'LOG-DOCK-SEC-01' }}</span>
                 </div>
                 <div class="flex flex-col">
                    <span class="text-[8px] text-surface-text-muted uppercase font-bold">ACCIÓN RECOMENDADA</span>
                    <span class="text-[10px] text-amber-400 font-bold">RELOCATE TO ZONE B</span>
                 </div>
              </div>
            </div>
          }
        </div>
      </div>
    }
  `,
  styles: [`
    .industrial-card {
      background: linear-gradient(135deg, rgba(245, 158, 11, 0.05) 0%, rgba(0,0,0,0.2) 100%);
      border: 1px solid rgba(245, 158, 11, 0.1);
      border-radius: 20px;
    }
  `]
})
export class DensityAlertPanelComponent {
  public hub = inject(NotificationHubService);
  
  overflowAlerts = () => this.hub.notifications().filter(n => n.type === 'CapacityViolation');

  constructor() {
    this.hub.startPolling();
  }
}
