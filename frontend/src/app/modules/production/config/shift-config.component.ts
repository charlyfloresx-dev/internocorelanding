import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { ShiftService } from '../../../core/services/shift.service';
import { SideDrawerService } from '../../../core/services/side-drawer.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ShiftFormComponent } from '../../../shared/components/shift-form.component';
import { ShiftRead, BreakSlot } from '../../../core/models/mes.types';

const BREAK_ICON: Record<string, string> = {
  BREAK: 'coffee',
  MEAL:  'restaurant',
  MAINTENANCE: 'build',
};

@Component({
  selector: 'app-shift-config',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            Turnos de Producción
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            Matutino · Vespertino · Nocturno — Horarios y grupos de descanso
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

          <!-- Scope filter -->
          <select [(ngModel)]="scopeFilter"
            class="px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest focus:border-primary outline-none cursor-pointer">
            <option value="">Todos</option>
            <option value="company">Empresa</option>
            <option value="resource">Por Recurso</option>
          </select>

          <button (click)="loadShifts()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all">
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <button (click)="openCreate()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20">
            <mat-icon class="text-sm">add</mat-icon>
            Nuevo Turno
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="industrial-card overflow-hidden">
        @if (svc.loading()) {
          <div class="p-12 flex items-center justify-center">
            <div class="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
          </div>
        } @else {
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="bg-surface-bg/50 border-b border-surface-border">
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] w-8"></th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Código</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Nombre</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Horario</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Breaks</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Alcance</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Estado</th>
                  <th class="px-6 py-5 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-border">
                @for (shift of filtered(); track shift.id) {
                  <tr class="group hover:bg-primary/5 transition-all duration-200"
                      [class.bg-amber-500/5]="expandedId() === shift.id">
                    <!-- Expand toggle -->
                    <td class="px-6 py-4">
                      <button (click)="toggleExpand(shift.id)"
                        class="p-1 hover:bg-surface-border rounded-lg transition-all"
                        [class.text-primary]="expandedId() === shift.id"
                        [class.text-surface-text-muted]="expandedId() !== shift.id">
                        <mat-icon class="text-sm transition-transform"
                          [class.rotate-90]="expandedId() === shift.id">
                          chevron_right
                        </mat-icon>
                      </button>
                    </td>

                    <td class="px-6 py-4">
                      <span class="text-xs font-black text-primary tracking-widest font-mono">{{ shift.code }}</span>
                    </td>

                    <td class="px-6 py-4">
                      <span class="text-sm font-bold text-surface-text">{{ shift.name }}</span>
                    </td>

                    <td class="px-6 py-4">
                      <div class="inline-flex items-center gap-2 px-3 py-1.5 bg-surface-bg border border-surface-border rounded-xl font-mono text-xs">
                        <span class="text-surface-text">{{ shift.start_time }}</span>
                        <mat-icon class="text-xs text-surface-text-muted">arrow_forward</mat-icon>
                        <span class="text-surface-text">{{ shift.end_time }}</span>
                        @if (shift.is_overnight) {
                          <mat-icon class="text-[11px] text-amber-400" title="Cruza medianoche">bedtime</mat-icon>
                        }
                      </div>
                    </td>

                    <td class="px-6 py-4">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-surface-text">{{ shift.breaks.length }}</span>
                        <div class="flex gap-1">
                          @for (brk of shift.breaks; track brk.code) {
                            <span class="p-1 rounded bg-surface-bg border border-surface-border"
                              [title]="brk.label + ' (' + brk.duration_minutes + 'min)'">
                              <mat-icon class="text-[10px] text-surface-text-muted">{{ breakIcon(brk.break_type) }}</mat-icon>
                            </span>
                          }
                        </div>
                        <span class="text-[9px] text-surface-text-muted">{{ shift.break_minutes }}min total</span>
                      </div>
                    </td>

                    <td class="px-6 py-4">
                      @if (shift.resource_id) {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px] font-black uppercase">
                          <mat-icon class="text-[9px]">grid_view</mat-icon>
                          Recurso
                        </span>
                      } @else {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-[9px] font-black uppercase">
                          <mat-icon class="text-[9px]">business</mat-icon>
                          Empresa
                        </span>
                      }
                    </td>

                    <td class="px-6 py-4">
                      @if (shift.is_active) {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] font-black uppercase">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>Activo
                        </span>
                      } @else {
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-bg text-surface-text-muted border border-surface-border text-[9px] font-black uppercase">
                          Inactivo
                        </span>
                      }
                    </td>

                    <td class="px-6 py-4 text-right">
                      <div class="flex justify-end items-center gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-4 group-hover:translate-x-0">
                        <button (click)="openEdit(shift)"
                          class="p-2 hover:bg-primary/10 text-primary rounded-lg transition-all" title="Editar turno">
                          <mat-icon class="text-sm">edit</mat-icon>
                        </button>
                        @if (shift.is_active) {
                          <button (click)="deleteShift(shift)"
                            class="p-2 hover:bg-rose-500/10 text-rose-400 rounded-lg transition-all" title="Desactivar">
                            <mat-icon class="text-sm">remove_circle</mat-icon>
                          </button>
                        }
                      </div>
                    </td>
                  </tr>

                  <!-- Expandable breaks panel -->
                  @if (expandedId() === shift.id) {
                    <tr class="bg-amber-500/5 border-b border-surface-border">
                      <td colspan="8" class="px-8 py-4">
                        <div class="space-y-3">
                          <h4 class="text-[10px] font-black text-amber-400 uppercase tracking-widest flex items-center gap-2">
                            <mat-icon class="text-xs">coffee</mat-icon>
                            Breaks de {{ shift.name }}
                          </h4>

                          @if (shift.breaks.length === 0) {
                            <p class="text-[10px] text-surface-text-muted italic">
                              Sin breaks configurados. Abre "Editar" para agregar breaks.
                            </p>
                          } @else {
                            <div class="flex flex-wrap gap-3">
                              @for (brk of shift.breaks; track brk.code) {
                                <div class="flex items-center gap-2 px-4 py-3 bg-surface-card border border-surface-border rounded-xl">
                                  <mat-icon class="text-sm text-amber-400">{{ breakIcon(brk.break_type) }}</mat-icon>
                                  <div>
                                    <div class="text-xs font-bold text-surface-text">{{ brk.label }}</div>
                                    <div class="text-[9px] text-surface-text-muted font-mono">
                                      {{ brk.start_time }} – {{ brk.end_time }} · {{ brk.duration_minutes }} min
                                    </div>
                                  </div>
                                  <span class="ml-2 px-2 py-0.5 rounded-full bg-surface-bg text-[8px] font-black uppercase {{ breakTypeColor(brk.break_type) }}">
                                    {{ brk.break_type }}
                                  </span>
                                </div>
                              }
                            </div>
                          }

                          <p class="text-[9px] text-surface-text-muted italic flex items-center gap-1">
                            <mat-icon class="text-[9px]">info</mat-icon>
                            Agrega o elimina breaks desde el formulario de edición. Los grupos de descanso para stagger de áreas comunes se configuran en el módulo RH.
                          </p>
                        </div>
                      </td>
                    </tr>
                  }
                } @empty {
                  <tr>
                    <td colspan="8" class="px-8 py-32 text-center">
                      <div class="flex flex-col items-center gap-4">
                        <div class="w-20 h-20 bg-surface-bg border border-surface-border rounded-full flex items-center justify-center">
                          <mat-icon class="text-4xl text-surface-text-muted/20">schedule</mat-icon>
                        </div>
                        <p class="text-surface-text-muted text-sm italic">No hay turnos configurados.</p>
                        <button (click)="openCreate()"
                          class="px-6 py-3 bg-primary/10 text-primary rounded-xl text-xs font-bold hover:bg-primary/20 transition-all">
                          Crear primer turno
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
      @if (!svc.loading() && svc.shifts().length > 0) {
        <div class="flex items-center gap-6 text-[10px] text-surface-text-muted font-mono">
          <span>{{ svc.shifts().length }} turnos</span>
          <span>·</span>
          <span>{{ svc.shifts().filter(s => s.is_active).length }} activos</span>
          <span>·</span>
          <span>{{ svc.shifts().filter(s => !s.resource_id).length }} de empresa</span>
          <span>·</span>
          <span>{{ svc.shifts().filter(s => !!s.resource_id).length }} por recurso</span>
        </div>
      }

    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in { animation: fadeIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    .rotate-90 { transform: rotate(90deg); }
  `]
})
export class ShiftConfigComponent implements OnInit {
  svc    = inject(ShiftService);
  drawer = inject(SideDrawerService);
  notif  = inject(NotificationService);

  searchQuery = '';
  scopeFilter = '';
  expandedId  = signal<string | null>(null);

  filtered = computed(() => {
    let list = this.svc.shifts();
    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(s =>
        s.code.toLowerCase().includes(q) || s.name.toLowerCase().includes(q)
      );
    }
    if (this.scopeFilter === 'company') list = list.filter(s => !s.resource_id);
    if (this.scopeFilter === 'resource') list = list.filter(s => !!s.resource_id);
    return list;
  });

  ngOnInit() {
    this.loadShifts();
    this.drawer.refresh$.subscribe(() => this.loadShifts());
  }

  async loadShifts() {
    await this.svc.loadShifts();
  }

  toggleExpand(id: string) {
    this.expandedId.set(this.expandedId() === id ? null : id);
  }

  breakIcon(type?: string): string {
    return BREAK_ICON[type ?? 'BREAK'] ?? 'coffee';
  }

  breakTypeColor(type?: string): string {
    if (type === 'MEAL') return 'text-emerald-400';
    if (type === 'MAINTENANCE') return 'text-violet-400';
    return 'text-amber-400';
  }

  openCreate() {
    this.drawer.open(ShiftFormComponent, {
      title: 'Nuevo Turno',
      subtitle: 'Configurar horario de producción',
      icon: 'add_circle',
      width: 'w-[520px]',
    });
  }

  openEdit(shift: ShiftRead) {
    this.drawer.open(ShiftFormComponent, {
      title: 'Editar Turno',
      subtitle: shift.name,
      icon: 'edit_square',
      width: 'w-[520px]',
    }, { item: shift });
  }

  async deleteShift(shift: ShiftRead) {
    if (!confirm(`¿Desactivar el turno "${shift.name}"?`)) return;
    try {
      await this.svc.deleteShift(shift.id);
      this.notif.success('Turno desactivado', shift.name);
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo desactivar');
    }
  }
}
