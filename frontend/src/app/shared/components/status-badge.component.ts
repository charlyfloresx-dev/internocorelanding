import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [CommonModule],
  template: `
    <span 
      class="status-badge"
      [ngClass]="{
        'bg-emerald-500/10 text-emerald-500 border-emerald-500/20': status() === 'CONFIRMED' || status() === 'SUCCESS' || status() === 'GREEN',
        'bg-amber-500/10 text-amber-500 border-amber-500/20': status() === 'PENDING' || status() === 'TRANSIT' || status() === 'ORANGE',
        'bg-red-500/10 text-red-500 border-red-500/20': status() === 'CANCELLED' || status() === 'ERROR' || status() === 'RED' || status() === 'CRITICAL',
        'bg-surface-text/10 text-surface-text-muted border-surface-border': status() === 'DRAFT'
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
