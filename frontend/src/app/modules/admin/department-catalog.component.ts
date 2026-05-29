import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { DepartmentService, Department } from '../../core/services/department.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { NotificationService } from '../../core/services/notification.service';
import { DepartmentFormComponent } from '../../shared/components/department-form.component';

@Component({
  selector: 'app-department-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">

      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            Áreas y Departamentos
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            Configuración organizacional · HCM
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <!-- Search -->
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input
              type="text"
              [(ngModel)]="searchQuery"
              placeholder="Buscar código o nombre..."
              class="pl-12 pr-6 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64 outline-none"
            >
          </div>

          <!-- Filter toggle -->
          <button
            (click)="showInactive.set(!showInactive())"
            class="px-5 py-3 border rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all"
            [class.bg-surface-bg]="!showInactive()"
            [class.border-surface-border]="!showInactive()"
            [class.bg-amber-50]="showInactive()"
            [class.border-amber-300]="showInactive()"
            [class.text-amber-700]="showInactive()"
          >
            {{ showInactive() ? 'Mostrando inactivos' : 'Solo activos' }}
          </button>

          <!-- Refresh -->
          <button
            (click)="reload()"
            [disabled]="svc.loading()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all disabled:opacity-50"
          >
            <mat-icon class="text-sm" [class.animate-spin]="svc.loading()">refresh</mat-icon>
          </button>

          <!-- New -->
          <button
            (click)="openCreate()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-sm">add</mat-icon>
            Nuevo Departamento
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="industrial-card overflow-hidden">
        @if (svc.loading()) {
          <div class="p-16 text-center">
            <mat-icon class="text-4xl text-primary animate-spin mb-3">sync</mat-icon>
            <p class="text-surface-text-muted text-xs font-mono uppercase tracking-widest">Cargando departamentos...</p>
          </div>
        } @else if (filtered().length === 0) {
          <div class="p-16 text-center">
            <mat-icon class="text-6xl text-surface-text-muted/20 mb-4">corporate_fare</mat-icon>
            <p class="text-surface-text-muted font-mono italic text-sm">
              {{ searchQuery ? 'Sin resultados para "' + searchQuery + '"' : 'No hay departamentos registrados.' }}
            </p>
            @if (!searchQuery) {
              <button (click)="openCreate()" class="mt-6 px-6 py-3 bg-primary/10 text-primary rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-primary/20 transition-all">
                Crear el primero
              </button>
            }
          </div>
        } @else {
          <table class="w-full">
            <thead>
              <tr class="border-b border-surface-border">
                <th class="px-6 py-4 text-left text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Código</th>
                <th class="px-6 py-4 text-left text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Nombre</th>
                <th class="px-6 py-4 text-left text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] hidden md:table-cell">Descripción</th>
                <th class="px-6 py-4 text-center text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Estado</th>
                <th class="px-6 py-4 text-right text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (dept of filtered(); track dept.id) {
                <tr class="border-b border-surface-border/50 hover:bg-primary/[0.02] transition-colors group">
                  <td class="px-6 py-4">
                    <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono font-bold text-primary">
                      {{ dept.code }}
                    </span>
                  </td>
                  <td class="px-6 py-4">
                    <span class="text-[11px] font-bold text-surface-text">{{ dept.name }}</span>
                  </td>
                  <td class="px-6 py-4 hidden md:table-cell">
                    <span class="text-[10px] text-surface-text-muted line-clamp-1">
                      {{ dept.description || '—' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-center">
                    <button
                      (click)="toggleActive(dept)"
                      [disabled]="togglingId() === dept.id"
                      class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-[9px] font-black uppercase tracking-wider transition-all"
                      [class.bg-emerald-100]="dept.is_active"
                      [class.text-emerald-700]="dept.is_active"
                      [class.hover:bg-emerald-200]="dept.is_active"
                      [class.bg-slate-100]="!dept.is_active"
                      [class.text-slate-500]="!dept.is_active"
                      [class.hover:bg-slate-200]="!dept.is_active"
                      [title]="dept.is_active ? 'Clic para desactivar' : 'Clic para activar'"
                    >
                      <span class="w-1.5 h-1.5 rounded-full"
                        [class.bg-emerald-500]="dept.is_active"
                        [class.bg-slate-400]="!dept.is_active"
                      ></span>
                      {{ dept.is_active ? 'Activo' : 'Inactivo' }}
                    </button>
                  </td>
                  <td class="px-6 py-4 text-right">
                    <button
                      (click)="openEdit(dept)"
                      class="p-2 hover:bg-primary/10 text-surface-text-muted hover:text-primary rounded-xl transition-all opacity-0 group-hover:opacity-100"
                      title="Editar"
                    >
                      <mat-icon class="text-sm">edit</mat-icon>
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>

          <!-- Row count -->
          <div class="px-6 py-3 border-t border-surface-border/50 flex justify-between items-center">
            <span class="text-[9px] font-mono text-surface-text-muted uppercase tracking-widest">
              {{ filtered().length }} departamento{{ filtered().length !== 1 ? 's' : '' }}
            </span>
            @if (showInactive() && inactiveCount() > 0) {
              <span class="text-[9px] text-amber-600 font-bold uppercase tracking-widest">
                {{ inactiveCount() }} inactivo{{ inactiveCount() !== 1 ? 's' : '' }}
              </span>
            }
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in { animation: fadeIn 0.4s cubic-bezier(0.22,1,0.36,1) forwards; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    .line-clamp-1 { overflow:hidden; display:-webkit-box; -webkit-line-clamp:1; -webkit-box-orient:vertical; }
  `]
})
export class DepartmentCatalogComponent implements OnInit {
  svc = inject(DepartmentService);
  private drawer = inject(SideDrawerService);
  private notify = inject(NotificationService);

  searchQuery = '';
  showInactive = signal(false);
  togglingId = signal<string | null>(null);

  filtered = computed(() => {
    let list = this.svc.departments();
    if (!this.showInactive()) list = list.filter(d => d.is_active);
    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(d => d.code.toLowerCase().includes(q) || d.name.toLowerCase().includes(q));
    }
    return list;
  });

  inactiveCount = computed(() => this.svc.departments().filter(d => !d.is_active).length);

  ngOnInit() {
    this.reload();
    this.drawer.refresh$.subscribe(() => this.reload());
  }

  reload() {
    this.svc.load();
  }

  openCreate() {
    this.drawer.open(DepartmentFormComponent, {
      title: 'Nuevo Departamento',
      subtitle: 'Área organizacional HCM',
      icon: 'add_circle'
    });
  }

  openEdit(dept: Department) {
    this.drawer.open(DepartmentFormComponent, {
      title: 'Editar Departamento',
      subtitle: dept.code,
      icon: 'edit_square'
    }, { item: dept });
  }

  toggleActive(dept: Department) {
    this.togglingId.set(dept.id);
    const req = dept.is_active
      ? this.svc.deactivate(dept.id)
      : this.svc.update(dept.id, { is_active: true });

    req.subscribe({
      next: () => {
        dept.is_active = !dept.is_active;
        this.togglingId.set(null);
        const msg = dept.is_active ? 'Departamento activado' : 'Departamento desactivado';
        this.notify.success('Éxito', msg);
      },
      error: () => {
        this.togglingId.set(null);
        this.notify.error('Error', 'No se pudo cambiar el estado');
      }
    });
  }
}
