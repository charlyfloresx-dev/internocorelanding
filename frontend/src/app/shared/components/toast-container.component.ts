import {Component, inject, ChangeDetectionStrategy} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ToastService} from '../../core/services/toast.service';
import {MatIconModule} from '@angular/material/icon';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-4 pointer-events-none perspective-1000 dark">
      @for (toast of toastService.activeToasts(); track toast.id) {
        <div class="pointer-events-auto min-w-[340px] max-w-md bg-ic-slate/95 border-l-4 rounded-lg shadow-2xl overflow-hidden animate-slide-in-right backdrop-blur-md relative"
             [ngClass]="getClasses(toast.type)">
          
          <!-- Glass Reflection Effect -->
          <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/10 to-transparent pointer-events-none"></div>

          <div class="p-4 flex items-start gap-4 relative z-10">
            <!-- Icon Box -->
            <div class="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center bg-ic-dark/80 border border-white/10 shadow-inner">
              @if (toast.type === 'success') { <mat-icon class="!text-neon-green text-2xl animate-pulse-once">check_circle</mat-icon> }
              @if (toast.type === 'error') { <mat-icon class="!text-red-500 text-2xl animate-shake">error</mat-icon> }
              @if (toast.type === 'info') { <mat-icon class="!text-neon-cyan text-2xl">info</mat-icon> }
              @if (toast.type === 'warning') { <mat-icon class="!text-amber-500 text-2xl animate-shake">warning</mat-icon> }
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              @if (toast.title) {
                <h4 class="text-[10px] font-black uppercase tracking-[0.2em] mb-1"
                    [ngClass]="{
                      'text-neon-green': toast.type === 'success',
                      'text-red-500': toast.type === 'error',
                      'text-neon-cyan': toast.type === 'info',
                      'text-amber-500': toast.type === 'warning'
                    }">
                  {{ toast.title }}
                </h4>
              }
              <p class="text-xs text-white leading-snug font-bold drop-shadow-md">{{ toast.message }}</p>
            </div>

            <!-- Close -->
            <button (click)="toastService.remove(toast.id)" class="text-white/40 hover:text-white transition-colors self-start -mt-1 -mr-1">
              <mat-icon class="text-lg">close</mat-icon>
            </button>
          </div>

          <!-- Progress Bar Animation -->
          <div class="h-0.5 bg-white/10 w-full mt-auto">
            <div class="h-full animate-shrink-width" 
                 [ngClass]="{
                   'bg-neon-green': toast.type === 'success',
                   'bg-red-500': toast.type === 'error',
                   'bg-neon-cyan': toast.type === 'info',
                   'bg-amber-500': toast.type === 'warning'
                 }"
                 [style.animation-duration.ms]="toast.duration"></div>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    @keyframes slide-in-right {
      0% { transform: translateX(100%) scale(0.9); opacity: 0; }
      80% { transform: translateX(-5%) scale(1.02); opacity: 1; }
      100% { transform: translateX(0) scale(1); opacity: 1; }
    }
    .animate-slide-in-right {
      animation: slide-in-right 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    
    @keyframes shrink-width {
      from { width: 100%; }
      to { width: 0%; }
    }
    .animate-shrink-width {
      animation: shrink-width linear forwards;
    }

    @keyframes pulse-once {
      0% { transform: scale(0.8); }
      50% { transform: scale(1.2); }
      100% { transform: scale(1); }
    }
    .animate-pulse-once { animation: pulse-once 0.4s ease-out; }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-2px); }
      75% { transform: translateX(2px); }
    }
    .animate-shake { animation: shake 0.3s ease-in-out; }

    /* Perspective for 3D feel */
    .perspective-1000 { perspective: 1000px; }
  `]
})
export class ToastContainerComponent {
  toastService = inject(ToastService);

  getClasses(type: string): string {
    const base = 'border-l-4 transition-all duration-300 ';
    switch(type) {
      case 'success': return base + 'border-neon-green shadow-[0_5px_15px_rgba(0,255,157,0.2)]';
      case 'error':   return base + 'border-red-500 shadow-[0_5px_15px_rgba(239,68,68,0.25)]';
      case 'info':    return base + 'border-neon-cyan shadow-[0_5px_15px_rgba(0,229,255,0.2)]';
      case 'warning': return base + 'border-amber-500 shadow-[0_5px_15px_rgba(245,158,11,0.2)]';
      default: return base + 'border-ic-muted';
    }
  }
}
