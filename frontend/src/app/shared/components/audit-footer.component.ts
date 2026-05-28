import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { LocalDatePipe } from '../../shared/pipes/local-date.pipe';

@Component({
  selector: 'app-audit-footer',
  standalone: true,
  imports: [CommonModule, MatIconModule, LocalDatePipe],
  template: `
    <div class="flex items-center justify-between mt-6 pt-4 border-t border-surface-border text-[10px] text-surface-text-muted font-mono uppercase tracking-widest relative group">
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-1.5 cursor-help">
          <mat-icon class="text-[14px] w-3.5 h-3.5">history</mat-icon>
          <span>Versión: {{ version() || 1 }}</span>
        </div>
        <div class="flex items-center gap-1.5 cursor-help" title="Creado por: {{ createdBy() || 'System' }}">
          <mat-icon class="text-[14px] w-3.5 h-3.5">person</mat-icon>
          <span>{{ createdBy() || 'System' }}</span>
        </div>
      </div>
      
      <!-- Triple Identity View Structure -->
      @if (folio() && uuid()) {
        <div class="absolute left-1/2 -translate-x-1/2 flex items-center gap-3">
           <span class="text-xs font-black text-surface-text tracking-widest">{{ folio() }}</span>
           <span class="text-[8px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-surface-text-muted select-all cursor-copy hover:border-primary/50 transition-colors" title="Copiar UUID">{{ uuid() }}</span>
        </div>
      }

      <div class="flex items-center gap-1.5 cursor-help" title="Última modificación">
        <mat-icon class="text-[14px] w-3.5 h-3.5">calendar_today</mat-icon>
        <span>{{ createdAt() | localDate:'yyyy-MM-dd HH:mm:ss' }}</span>
      </div>
    </div>

  `
})
export class AuditFooterComponent {
  version = input<number>();
  createdBy = input<string>();
  createdAt = input<string | Date>(new Date());
  folio = input<string>();
  uuid = input<string>();
}
