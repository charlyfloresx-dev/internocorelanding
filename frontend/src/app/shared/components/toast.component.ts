
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ToastService } from '@services/toast.service';

@Component({
  selector: 'app-toast-container',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-4 pointer-events-none perspective-1000">
      @for (toast of toastService.toasts(); track toast.id) {
        <div class="pointer-events-auto min-w-[340px] max-w-md bg-slate-900 border-l-4 rounded shadow-2xl overflow-hidden animate-slide-in-right backdrop-blur-md"
             [ngClass]="getClasses(toast.type)">
          
          <!-- Glass Reflection Effect -->
          <div class="absolute top-0 left-0 w-full h-full bg-gradient-to-br from-white/5 to-transparent pointer-events-none"></div>

          <div class="p-4 flex items-start gap-4 relative z-10">
            <!-- Icon Box -->
            <div class="flex-shrink-0 w-10 h-10 rounded flex items-center justify-center bg-slate-800 border border-slate-700 shadow-inner">
              @if (toast.type === 'success') { <i class="fa-solid fa-check text-green-500 text-xl animate-pulse-once"></i> }
              @if (toast.type === 'error') { <i class="fa-solid fa-triangle-exclamation text-red-500 text-xl animate-shake"></i> }
              @if (toast.type === 'info') { <i class="fa-solid fa-info text-sky-500 text-xl"></i> }
              @if (toast.type === 'warning') { <i class="fa-solid fa-bolt text-yellow-500 text-xl"></i> }
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              @if (toast.title) {
                <h4 class="text-xs font-bold uppercase tracking-widest mb-1"
                    [ngClass]="{
                      'text-green-500': toast.type === 'success',
                      'text-red-500': toast.type === 'error',
                      'text-sky-500': toast.type === 'info',
                      'text-yellow-500': toast.type === 'warning'
                    }">
                  {{ toast.title }}
                </h4>
              }
              <p class="text-sm text-slate-200 leading-snug font-medium shadow-black drop-shadow-md">{{ toast.message }}</p>
            </div>

            <!-- Close -->
            <button (click)="toastService.remove(toast.id)" class="text-slate-600 hover:text-white transition-colors self-start -mt-1 -mr-1">
              <i class="fa-solid fa-times"></i>
            </button>
          </div>

          <!-- Progress Bar Animation -->
          <div class="h-0.5 bg-slate-800 w-full mt-1">
            <div class="h-full animate-shrink-width" 
                 [ngClass]="{
                   'bg-green-500': toast.type === 'success',
                   'bg-red-500': toast.type === 'error',
                   'bg-sky-500': toast.type === 'info',
                   'bg-yellow-500': toast.type === 'warning'
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
export class ToastComponent {
  toastService = inject(ToastService);

  getClasses(type: string): string {
    const base = 'border-l-4 transition-all duration-300 ';
    switch(type) {
      case 'success': return base + 'border-green-500 shadow-[0_5px_15px_rgba(34,197,94,0.2)]';
      case 'error':   return base + 'border-red-500 shadow-[0_5px_15px_rgba(239,68,68,0.25)]';
      case 'info':    return base + 'border-sky-500 shadow-[0_5px_15px_rgba(14,165,233,0.2)]';
      case 'warning': return base + 'border-yellow-500 shadow-[0_5px_15px_rgba(234,179,8,0.2)]';
      default: return base + 'border-slate-500';
    }
  }
}
