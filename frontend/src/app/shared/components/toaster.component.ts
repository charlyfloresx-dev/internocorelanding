import {Component, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {NotificationService} from '../../core/services/notification.service';
import {MatIconModule} from '@angular/material/icon';

@Component({
  selector: 'app-toaster',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="fixed top-6 right-6 z-[100] flex flex-col gap-4 pointer-events-none w-full max-w-sm">
      @for (n of notificationService.notifications(); track n.id) {
        <div 
          class="pointer-events-auto industrial-card glass-card p-4 flex items-start gap-4 animate-slide-in-right group relative overflow-hidden"
          [ngClass]="{
            'border-emerald-500/30': n.type === 'success',
            'border-red-500/30': n.type === 'error',
            'border-amber-500/30': n.type === 'warning',
            'border-primary/30': n.type === 'info'
          }"
        >
          <!-- Status Indicator Line -->
          <div 
            class="absolute left-0 top-0 bottom-0 w-1 shadow-[0_0_10px_rgba(0,0,0,0.5)]"
            [ngClass]="{
              'bg-emerald-500 shadow-emerald-500/50': n.type === 'success',
              'bg-red-500 shadow-red-500/50': n.type === 'error',
              'bg-amber-500 shadow-amber-500/50': n.type === 'warning',
              'bg-primary shadow-primary/50': n.type === 'info'
            }"
          ></div>

          <div 
            class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
            [ngClass]="{
              'bg-emerald-500/10 text-emerald-500': n.type === 'success',
              'bg-red-500/10 text-red-500': n.type === 'error',
              'bg-amber-500/10 text-amber-500': n.type === 'warning',
              'bg-primary/10 text-primary': n.type === 'info'
            }"
          >
            <mat-icon>{{ getIcon(n.type) }}</mat-icon>
          </div>

          <div class="flex-1 min-w-0">
            <h4 class="text-[10px] font-black uppercase tracking-widest text-surface-text mb-0.5">{{ n.title }}</h4>
            <p class="text-xs text-surface-text-muted font-medium leading-relaxed">{{ n.message }}</p>
          </div>

          <button 
            (click)="notificationService.remove(n.id)"
            class="text-surface-text-muted hover:text-surface-text transition-colors p-1"
          >
            <mat-icon class="text-lg">close</mat-icon>
          </button>

          <!-- Progress Bar -->
          @if (n.duration && n.duration > 0) {
            <div class="absolute bottom-0 left-0 h-0.5 bg-white/10 w-full">
              <div 
                class="h-full transition-all duration-linear"
                [ngClass]="{
                  'bg-emerald-500': n.type === 'success',
                  'bg-red-500': n.type === 'error',
                  'bg-amber-500': n.type === 'warning',
                  'bg-primary': n.type === 'info'
                }"
                [style.animation]="'toaster-progress ' + n.duration + 'ms linear forwards'"
              ></div>
            </div>
          }
        </div>
      }
    </div>
  `,
  styles: [`
    @keyframes toaster-progress {
      from { width: 100%; }
      to { width: 0%; }
    }
    .duration-linear {
      animation-timing-function: linear;
    }
  `]
})
export class ToasterComponent {
  notificationService = inject(NotificationService);

  getIcon(type: string) {
    switch (type) {
      case 'success': return 'check_circle';
      case 'error': return 'error';
      case 'warning': return 'warning';
      default: return 'info';
    }
  }
}
