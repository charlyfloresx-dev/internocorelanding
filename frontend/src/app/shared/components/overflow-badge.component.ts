import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ValidationStatus } from '../../core/models/domain.types';

@Component({
  selector: 'app-overflow-badge',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    @if (status === 'OVERFLOW_CONFIRMED') {
      <div 
        class="flex items-center gap-1 bg-amber-500/10 border border-amber-500/50 text-amber-500 px-2 py-0.5 rounded text-[9px] font-black uppercase shadow-[0_0_10px_rgba(245,158,11,0.2)] animate-pulse"
        title="Physical Overcapacity Detected"
      >
        <mat-icon class="text-[10px] w-3 h-3">warning</mat-icon>
        OVERFLOW
      </div>
    } @else if (status === 'UNDER_REVIEW') {
      <div class="flex items-center gap-1 bg-cyan-500/10 border border-cyan-500/50 text-cyan-500 px-2 py-0.5 rounded text-[9px] font-black uppercase">
        <mat-icon class="text-[10px] w-3 h-3">hourglass_empty</mat-icon>
        PENDING
      </div>
    }
  `
})
export class OverflowBadgeComponent {
  @Input() status?: ValidationStatus | string;
}
