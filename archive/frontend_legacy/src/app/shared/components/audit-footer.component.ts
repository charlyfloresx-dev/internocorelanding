import { Component, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
    selector: 'app-audit-footer',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    template: `
    <div class="flex items-center justify-between mt-6 pt-4 border-t border-white/10 text-[10px] text-surface-text-muted font-mono uppercase tracking-widest italic opacity-60">
      <div class="flex items-center gap-6">
        <div class="flex items-center gap-1.5">
          <mat-icon class="text-[14px] w-3.5 h-3.5 text-primary">history</mat-icon>
          <span>Versión: {{ version() || 1 }}.0</span>
        </div>
        <div class="flex items-center gap-1.5 border-l border-white/10 pl-6">
          <mat-icon class="text-[14px] w-3.5 h-3.5 text-primary">person</mat-icon>
          <span>Audit: {{ createdBy() || 'SYSTEM_DAEMON' }}</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse shadow-[0_0_5px_rgba(0,229,255,0.8)]"></span>
        <span>{{ createdAt() | date:'yyyy-MM-dd HH:mm:ss' }}</span>
      </div>
    </div>
  `
})
export class AuditFooterComponent {
    version = input<number>();
    createdBy = input<string>();
    createdAt = input<string | Date>(new Date());
}
