import { Component, inject, signal, ViewChild, ViewContainerRef, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-side-drawer',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe],
  template: `
    <!-- Main Drawer Container -->
    <div 
      class="fixed inset-y-0 right-0 z-[100] bg-surface-card border-l border-surface-border shadow-2xl transform transition-transform duration-500 ease-out flex flex-col"
      [class]="drawerService.options().width || 'w-96'"
      [class.translate-x-0]="drawerService.isOpen()"
      [class.translate-x-full]="!drawerService.isOpen()"
    >
      <!-- Header -->
      <div class="h-20 px-6 border-b border-surface-border flex items-center justify-between bg-nav-bar/50 backdrop-blur-xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
            <mat-icon>{{ drawerService.options().icon || 'edit_note' }}</mat-icon>
          </div>
          <div>
            <h2 class="text-sm font-black text-surface-text uppercase tracking-widest">
              {{ drawerService.options().title | translate }}
            </h2>
            <span class="text-[10px] text-surface-text-muted font-bold uppercase tracking-tighter">
              {{ (drawerService.options().subtitle || 'master.drawer_subtitle') | translate }}
            </span>
          </div>
        </div>
        <button (click)="drawerService.close()" class="text-surface-text-muted hover:text-primary transition-colors">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <!-- Dynamic Content Area -->
      <div class="flex-1 overflow-y-auto custom-scrollbar p-6">
        <ng-container #contentContainer></ng-container>
      </div>

      <!-- Footer Info (Industrial Branding) -->
      <div class="p-4 bg-nav-bar/20 border-t border-surface-border flex items-center justify-center gap-4">
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(0,229,255,0.5)]"></div>
          <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">
            InternoCore {{ 'common.data_engine' | translate:'Data Engine' }}
          </span>
        </div>
      </div>
    </div>

    <!-- Backdrop -->
    @if (drawerService.isOpen()) {
      <button 
        (click)="drawerService.close()"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] animate-in fade-in duration-500 w-full h-full text-transparent"
        aria-label="Close Drawer"
      >
        Close
      </button>
    }
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar {
      width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(0, 229, 255, 0.1);
      border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: rgba(0, 229, 255, 0.3);
    }
  `]
})
export class SideDrawerComponent {
  drawerService = inject(SideDrawerService);
  
  @ViewChild('contentContainer', { read: ViewContainerRef }) contentContainer!: ViewContainerRef;

  constructor() {
    // Escuchar cambios en el componente para renderizar dinámicamente
    effect(() => {
      const componentType = this.drawerService.component();
      if (this.contentContainer) {
        this.contentContainer.clear();
        if (componentType) {
          const componentRef = this.contentContainer.createComponent(componentType);
          // Inyectar datos si el componente tiene una propiedad 'data'
          if (componentRef.instance && 'data' in componentRef.instance) {
            (componentRef.instance as any).data = this.drawerService.data();
          }
        }
      }
    });
  }
}
