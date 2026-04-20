import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-status-badge',
    standalone: true,
    imports: [CommonModule],
    template: `
    <span 
      class="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest border shadow-lg transition-all"
      [ngClass]="{
        'bg-emerald-500/10 text-emerald-500 border-emerald-500/20': status() === 'CONFIRMED' || status() === 'SUCCESS' || status() === 'GREEN' || status() === 'ACTIVE' || status() === 'PROCESSED',
        'bg-amber-500/10 text-amber-500 border-amber-500/20': status() === 'PENDING' || status() === 'TRANSIT' || status() === 'ORANGE' || status() === 'DRAFT',
        'bg-red-500/10 text-red-500 border-red-500/20': status() === 'CANCELLED' || status() === 'ERROR' || status() === 'RED' || status() === 'CRITICAL' || status() === 'FAILED',
        'bg-surface-text/10 text-surface-text-muted border-surface-border': status() === 'INACTIVE' || status() === 'ARCHIVED'
      }"
    >
      {{ label() || status() }}
    </span>
  `
})
export class StatusBadgeComponent {
    status = input.required<string>();
    label = input<string>();
}
