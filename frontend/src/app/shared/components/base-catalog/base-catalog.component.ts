// temp_future/src/app/shared/components/base-catalog/base-catalog.component.ts
import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-base-catalog',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="glass-panel p-6 rounded-xl border border-white/10 shadow-2xl futuristic-bg">
      <div class="flex justify-between items-center mb-6">
        <div>
          <h2 class="text-2xl font-bold text-white tracking-wider uppercase">{{ title }}</h2>
          <p class="text-xs text-cyan-400 font-mono italic">{{ subtitle }}</p>
        </div>
        <button (click)="onCreate.emit()" 
                class="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg transition-all border border-cyan-400/50 shadow-[0_0_15px_rgba(6,182,212,0.4)]">
          + NUEVO REGISTRO
        </button>
      </div>

      <!-- Loading State -->
      @if (isLoading()) {
        <div class="flex flex-col items-center justify-center py-12 space-y-4">
          <div class="w-12 h-12 border-4 border-cyan-500/20 border-t-cyan-500 rounded-full animate-spin"></div>
          <span class="text-xs text-cyan-400 font-mono animate-pulse">SINCRONIZANDO CON EL NÚCLEO...</span>
        </div>
      } @else {
        <div class="overflow-x-auto">
          <ng-content select="[table]"></ng-content>
        </div>
      }
    </div>
  `,
  styles: [`
    .glass-panel {
      background: rgba(15, 23, 42, 0.8);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }
    .futuristic-bg {
      background-image: 
        radial-gradient(circle at 2px 2px, rgba(6, 182, 212, 0.05) 1px, transparent 0);
      background-size: 24px 24px;
    }
  `]
})
export class BaseCatalogComponent {
  @Input() title: string = 'Catálogo';
  @Input() subtitle: string = 'SISTEMA DE GESTIÓN INDUSTRIAL';
  @Output() onCreate = new EventEmitter<void>();

  isLoading = signal<boolean>(false);
}
