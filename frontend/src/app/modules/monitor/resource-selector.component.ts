import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { ResourceService } from '../../core/services/resource.service';
import { ResourceRead } from '../../core/models/mes.types';

const TYPE_ICON: Record<string, string> = {
  CELL: 'grid_view',
  MACHINE: 'precision_manufacturing',
  AREA: 'warehouse',
  LINE: 'linear_scale',
};

const TYPE_LABEL: Record<string, string> = {
  CELL: 'Celda',
  MACHINE: 'Máquina',
  AREA: 'Área',
  LINE: 'Línea',
};

@Component({
  selector: 'app-resource-selector',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="space-y-6 animate-fade-in-up">

      <!-- Header -->
      <div>
        <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">
          <span class="text-primary glow-text">Monitor de Producción</span>
        </h2>
        <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest mt-1">
          Selecciona un recurso para monitorear en tiempo real
        </p>
      </div>

      <!-- Loading skeleton -->
      @if (loading()) {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          @for (_ of [1,2,3,4]; track _) {
            <div class="industrial-card p-5 h-28 animate-pulse bg-surface-text/5"></div>
          }
        </div>
      }

      <!-- Empty state -->
      @else if (resources().length === 0) {
        <div class="industrial-card p-12 text-center">
          <mat-icon class="text-surface-text-muted text-5xl mb-4">precision_manufacturing</mat-icon>
          <p class="text-surface-text-muted text-sm font-bold uppercase tracking-widest">
            No hay recursos configurados
          </p>
          <p class="text-surface-text-muted text-xs mt-2">
            Configura celdas, máquinas y líneas en la sección de administración MES.
          </p>
        </div>
      }

      <!-- Resource grid -->
      @else {
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          @for (res of resources(); track res.id) {
            <button
              (click)="navigate(res.code)"
              class="industrial-card p-5 text-left hover:border-primary/40 hover:bg-primary/5
                     transition-all duration-200 group focus:outline-none focus:ring-2
                     focus:ring-primary/30 rounded-xl"
            >
              <div class="flex items-start justify-between mb-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center
                            group-hover:bg-primary/20 transition-colors">
                  <mat-icon class="text-primary text-lg">{{ typeIcon(res.resource_type) }}</mat-icon>
                </div>
                <span class="text-[8px] px-2 py-0.5 rounded-full border border-surface-border
                             text-surface-text-muted font-bold uppercase tracking-widest">
                  {{ typeLabel(res.resource_type) }}
                </span>
              </div>
              <div class="font-black text-surface-text text-sm uppercase tracking-wide
                          group-hover:text-primary transition-colors">
                {{ res.code }}
              </div>
              <div class="text-[10px] text-surface-text-muted mt-0.5 truncate">
                {{ res.name }}
              </div>
              @if (res.capacity) {
                <div class="text-[8px] text-surface-text-muted mt-2 font-mono">
                  Cap. {{ res.capacity }} pzas/h
                </div>
              }
            </button>
          }
        </div>
      }

    </div>
  `,
  styles: [':host { display: block; }']
})
export class ResourceSelectorComponent implements OnInit {
  private svc    = inject(ResourceService);
  private router = inject(Router);

  readonly resources = this.svc.resourceList;
  readonly loading   = this.svc.isLoading;

  ngOnInit(): void {
    this.svc.listResources();
  }

  navigate(code: string): void {
    this.router.navigate(['/monitor/resources', code]);
  }

  typeIcon(type: string | null): string {
    return TYPE_ICON[type ?? ''] ?? 'device_hub';
  }

  typeLabel(type: string | null): string {
    return TYPE_LABEL[type ?? ''] ?? 'Recurso';
  }
}
