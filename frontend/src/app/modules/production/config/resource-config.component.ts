import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { ResourceService } from '../../../core/services/resource.service';
import { SideDrawerService } from '../../../core/services/side-drawer.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ResourceFormComponent } from '../../../shared/components/resource-form.component';
import { ResourceBulkFormComponent } from '../../../shared/components/resource-bulk-form.component';
import { ShiftFormComponent } from '../../../shared/components/shift-form.component';
import { ResourceRead } from '../../../core/models/mes.types';

const TYPE_ICON: Record<string, string> = {
  CELL:    'grid_view',
  MACHINE: 'precision_manufacturing',
  LINE:    'linear_scale',
  AREA:    'warehouse',
};
const TYPE_COLOR: Record<string, string> = {
  CELL:    'text-sky-400',
  MACHINE: 'text-violet-400',
  LINE:    'text-emerald-400',
  AREA:    'text-amber-400',
};

@Component({
  selector: 'app-resource-config',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            Recursos de Producción
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            Celdas · Máquinas · Líneas · Áreas — Configuración de planta
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <!-- Search -->
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm group-focus-within:text-primary transition-colors">search</mat-icon>
            <input type="text" [(ngModel)]="searchQuery"
              placeholder="Código o nombre..."
              class="pl-11 pr-5 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-52 outline-none" />
          </div>

          <!-- Type filter -->
          <select [(ngModel)]="typeFilter"
            class="px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest focus:border-primary outline-none cursor-pointer">
            <option value="">Todos los tipos</option>
            <option value="CELL">CELL</option>
            <option value="MACHINE">MACHINE</option>
            <option value="LINE">LINE</option>
            <option value="AREA">AREA</option>
          </select>

          <button (click)="loadResources()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all"
            title="Actualizar">
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <!-- Bulk upload -->
          <button (click)="openBulk()"
            class="flex items-center gap-2 px-5 py-3 bg-surface-bg border border-surface-border hover:bg-emerald-500/10 hover:border-emerald-500/30 text-emerald-400 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all">
            <mat-icon class="text-sm">upload_file</mat-icon>
            Carga CSV
          </button>

          <!-- New resource -->
          <button (click)="openCreate()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20">
            <mat-icon class="text-sm">add</mat-icon>
            Nuevo Recurso
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="industrial-card overflow-hidden">
        @if (svc.isLoading()) {
          <div class="p-12 flex items-center justify-center">
            <div class="flex flex-col items-center gap-4">
              <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
              <p class="text-surface-text-muted text-xs font-mono">Cargando recursos...</p>
            </div>
          </div>
        } @else {
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-bg/50 border-b border-surface-border">
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Tipo</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Código</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Nombre</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Capacidad</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Estado</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-border">
                @for (r of filtered(); track r.id) {
                  <tr class="group hover:bg-primary/5 transition-all duration-200">
                    <td class="px-6 py-4">
                      <div class="flex items-center gap-2">
                        <mat-icon class="text-lg {{ typeColor(r.resource_type) }}">{{ typeIcon(r.resource_type) }}</mat-icon>
                        <span class="text-[9px] font-black uppercase tracking-widest {{ typeColor(r.resource_type) }}">
                          {{ r.resource_type ?? '—' }}
                        </span>
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      <span class="text-xs font-black text-primary tracking-widest font-mono">{{ r.code }}</span>
                    </td>
                    <td class="px-6 py-4">
                      <div>
                        <div class="text-sm font-bold text-surface-text">{{ r.name }}</div>
                        @if (r.description) {
                          <div class="text-[10px] text-surface-text-muted truncate max-w-xs">{{ r.description }}</div>
                        }
                      </div>
                    </td>
                    <td class="px-6 py-4">
                      @if (r.capacity) {
                        <div class="inline-flex items-center gap-1 px-3 py-1.5 bg-surface-bg border border-surface-border rounded-xl">
                          <span class="text-xs font-mono font-bold text-emerald-400">{{ r.capacity }}</span>
                          <span class="text-[9px] text-surface-text-muted">pzas/hr</span>
                        </div>
                      } @else {
                        <span class="text-surface-text-muted text-xs">—</span>
                      }
                    </td>
                    <td class="px-6 py-4">
                      @if (r.active) {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-black uppercase">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                          Activo
                        </span>
                      } @else {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-bg text-surface-text-muted border border-surface-border text-[9px] font-black uppercase">
                          Inactivo
                        </span>
                      }
                    </td>
                    <td class="px-6 py-4 text-right">
                      <div class="flex justify-end items-center gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-4 group-hover:translate-x-0">
                        <button (click)="openShifts(r)"
                          class="p-2 hover:bg-amber-500/10 text-amber-400 rounded-lg transition-all"
                          title="Gestionar turnos del recurso">
                          <mat-icon class="text-sm">schedule</mat-icon>
                        </button>
                        <button (click)="openEdit(r)"
                          class="p-2 hover:bg-primary/10 text-primary rounded-lg transition-all"
                          title="Editar recurso">
                          <mat-icon class="text-sm">edit</mat-icon>
                        </button>
                      </div>
                    </td>
                  </tr>
                } @empty {
                  <tr>
                    <td colspan="6" class="px-8 py-32 text-center">
                      <div class="flex flex-col items-center gap-4">
                        <div class="w-20 h-20 bg-surface-bg border border-surface-border rounded-full flex items-center justify-center">
                          <mat-icon class="text-4xl text-surface-text-muted/20">precision_manufacturing</mat-icon>
                        </div>
                        <p class="text-surface-text-muted text-sm italic">No hay recursos configurados.</p>
                        <button (click)="openCreate()"
                          class="px-6 py-3 bg-primary/10 text-primary rounded-xl text-xs font-bold transition-all hover:bg-primary/20">
                          Crear primer recurso
                        </button>
                      </div>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </div>

      <!-- Stats bar -->
      @if (!svc.isLoading() && svc.resourceList().length > 0) {
        <div class="flex items-center gap-6 text-[10px] text-surface-text-muted font-mono">
          <span>{{ svc.resourceList().length }} recursos totales</span>
          <span>·</span>
          <span>{{ svc.resourceList().filter(r => r.active).length }} activos</span>
          <span>·</span>
          <span>{{ svc.resourceList().filter(r => r.resource_type === 'CELL').length }} celdas</span>
          <span>·</span>
          <span>{{ svc.resourceList().filter(r => r.resource_type === 'MACHINE').length }} máquinas</span>
        </div>
      }

    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in { animation: fadeIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
  `]
})
export class ResourceConfigComponent implements OnInit {
  svc    = inject(ResourceService);
  drawer = inject(SideDrawerService);
  notif  = inject(NotificationService);

  searchQuery = '';
  typeFilter  = '';

  filtered = computed(() => {
    let list = this.svc.resourceList();
    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(r =>
        r.code.toLowerCase().includes(q) || r.name.toLowerCase().includes(q)
      );
    }
    if (this.typeFilter) list = list.filter(r => r.resource_type === this.typeFilter);
    return list;
  });

  ngOnInit() {
    this.loadResources();
    this.drawer.refresh$.subscribe(() => this.loadResources());
  }

  async loadResources() {
    await this.svc.listResources();
  }

  typeIcon(type?: string | null): string {
    return TYPE_ICON[type ?? ''] ?? 'settings';
  }

  typeColor(type?: string | null): string {
    return TYPE_COLOR[type ?? ''] ?? 'text-surface-text-muted';
  }

  openCreate() {
    this.drawer.open(ResourceFormComponent, {
      title: 'Nuevo Recurso',
      subtitle: 'Celda · Máquina · Área · Línea',
      icon: 'add_circle',
      width: 'w-[480px]',
    });
  }

  openEdit(r: ResourceRead) {
    this.drawer.open(ResourceFormComponent, {
      title: 'Editar Recurso',
      subtitle: r.code,
      icon: 'edit_square',
      width: 'w-[480px]',
    }, { item: r });
  }

  openBulk() {
    this.drawer.open(ResourceBulkFormComponent, {
      title: 'Carga Masiva',
      subtitle: 'Importar desde CSV',
      icon: 'upload_file',
      width: 'w-[520px]',
    });
  }

  openShifts(r: ResourceRead) {
    this.drawer.open(ShiftFormComponent, {
      title: `Turno — ${r.code}`,
      subtitle: 'Nuevo turno específico de este recurso',
      icon: 'schedule',
      width: 'w-[520px]',
    }, { resourceId: r.id });
  }
}
