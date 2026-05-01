import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MasterDataService, UOM, ApiResponse } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { TranslationService } from '../../core/services/translation.service';
import { HttpErrorResponse } from '@angular/common/http';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { UomFormComponent } from '../../shared/components/uom-form.component';

@Component({
  selector: 'app-uom-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">
      <!-- Header: Control Grid Style -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            {{ t('catalog.uom.title', 'Gestión de Unidades') }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            {{ t('catalog.uom.subtitle', 'Configuración de magnitudes y factores de conversión') }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <!-- Integrated Search -->
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              placeholder="Buscar por código o nombre..."
              class="pl-12 pr-6 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64 outline-none"
            >
          </div>

          <!-- Status Filter -->
          <select 
            [(ngModel)]="statusFilter"
            class="px-4 py-3 bg-surface-bg border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none cursor-pointer"
          >
            <option value="ALL">TODOS LOS ESTADOS</option>
            <option value="GLOBAL">GLOBAL (SISTEMA)</option>
            <option value="TENANT">PRIVADO (TENANT)</option>
          </select>

          <button 
            (click)="loadUoms()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all"
            title="Refrescar Datos"
          >
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <button 
            (click)="openAddModal()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-sm">add</mat-icon>
            {{ t('catalog.uom.new', 'Nueva UOM') }}
          </button>
        </div>
      </div>

      <!-- Control Grid Table -->
      <div class="industrial-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50 border-b border-surface-border">
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">ID / Badge</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Código</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Abreviación</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Nombre</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Factor Conversión</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Tipo</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (uom of filteredUoms(); track uom.id) {
                <tr class="group hover:bg-primary/5 transition-all duration-300">
                  <td class="px-8 py-5">
                    <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono text-surface-text-muted">
                      {{ uom.id.substring(0, 8) }}
                    </span>
                  </td>
                  <td class="px-8 py-5">
                    <span class="text-xs font-black text-primary tracking-widest">{{ uom.code }}</span>
                  </td>
                  <td class="px-8 py-5">
                    <span class="text-xs font-mono text-surface-text">{{ uom.abbreviation }}</span>
                  </td>
                  <td class="px-8 py-5">
                    <span class="text-sm font-bold text-surface-text">{{ uom.name }}</span>
                  </td>
                  <td class="px-8 py-5">
                    <div class="inline-block px-4 py-2 bg-surface-bg border border-surface-border rounded-xl">
                      <span class="text-xs font-mono text-emerald-600 dark:text-emerald-400 font-bold">
                        {{ uom.conversion_factor | number:'1.8-8' }}
                      </span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    @if (masterData.isGlobal(uom)) {
                      <div class="flex items-center gap-2 text-primary">
                        <mat-icon class="text-sm">public</mat-icon>
                        <span class="text-[9px] font-black uppercase tracking-widest">Global</span>
                      </div>
                    } @else {
                      <div class="flex items-center gap-2 text-surface-text-muted">
                        <mat-icon class="text-sm">business</mat-icon>
                        <span class="text-[9px] font-black uppercase tracking-widest">Tenant</span>
                      </div>
                    }
                  </td>
                  <td class="px-8 py-5 text-right">
                    <div class="flex justify-end items-center gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-x-4 group-hover:translate-x-0">
                      <button class="p-2 hover:bg-primary/10 text-primary rounded-lg transition-all" title="Auditoría">
                        <mat-icon class="text-sm">history</mat-icon>
                      </button>
                      <button class="p-2 hover:bg-emerald-500/10 text-emerald-500 rounded-lg transition-all" title="Clonar">
                        <mat-icon class="text-sm">content_copy</mat-icon>
                      </button>
                      
                      @if (masterData.isGlobal(uom)) {
                        <button (click)="onViewDetails(uom)" class="p-2 hover:bg-surface-text-muted/10 text-surface-text-muted rounded-lg transition-all" title="Ver Detalles (Solo Lectura)">
                          <mat-icon class="text-sm">lock</mat-icon>
                        </button>
                      } @else {
                        <button (click)="onEditUom(uom)" class="p-2 hover:bg-amber-500/10 text-amber-500 rounded-lg transition-all" title="Editar">
                          <mat-icon class="text-sm">edit</mat-icon>
                        </button>
                      }
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="7" class="px-8 py-32 text-center">
                    <div class="flex flex-col items-center justify-center space-y-4">
                      <div class="w-20 h-20 bg-surface-bg border border-surface-border rounded-full flex items-center justify-center">
                        <mat-icon class="text-4xl text-surface-text-muted/20">straighten</mat-icon>
                      </div>
                      <p class="text-surface-text-muted font-mono text-sm italic">No se encontraron unidades de medida con los filtros actuales.</p>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in {
      animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class UomCatalogComponent implements OnInit {
  masterData = inject(MasterDataService);
  notifications = inject(NotificationService);
  translation = inject(TranslationService);

  uoms = signal<UOM[]>([]);
  loading = signal(false);
  searchQuery = '';
  statusFilter = 'ALL';
  drawerService = inject(SideDrawerService);

  filteredUoms = computed(() => {
    let list = this.uoms();
    
    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(u => 
        u.code.toLowerCase().includes(q) || 
        u.name.toLowerCase().includes(q) ||
        u.abbreviation.toLowerCase().includes(q)
      );
    }

    if (this.statusFilter !== 'ALL') {
      list = list.filter(u => 
        this.statusFilter === 'GLOBAL' ? this.masterData.isGlobal(u) : !this.masterData.isGlobal(u)
      );
    }

    return list;
  });

  ngOnInit() {
    this.loadUoms();
    this.drawerService.refresh$.subscribe(() => this.loadUoms());
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  loadUoms() {
    this.loading.set(true);
    this.masterData.getUoms().subscribe({
      next: (response: ApiResponse<UOM[]>) => {
        this.uoms.set(response.data);
        this.loading.set(false);
      },
      error: (err: HttpErrorResponse) => {
        console.error('Error loading UOMs:', err);
        // Mock data fallback with new fields
        this.uoms.set([
          { id: 'uom-1', name: 'Kilogramo', code: 'KG', abbreviation: 'kg', conversion_factor: 1.00000000, company_id: null },
          { id: 'uom-2', name: 'Gramo', code: 'G', abbreviation: 'g', conversion_factor: 0.00100000, company_id: null },
          { id: 'uom-3', name: 'Libra', code: 'LB', abbreviation: 'lb', conversion_factor: 0.45359237, company_id: null },
          { id: 'uom-4', name: 'Litro', code: 'L', abbreviation: 'l', conversion_factor: 1.00000000, company_id: null },
          { id: 'uom-5', name: 'Mililitro', code: 'ML', abbreviation: 'ml', conversion_factor: 0.00100000, company_id: null },
          { id: 'uom-6', name: 'Unidad', code: 'UN', abbreviation: 'un', conversion_factor: 1.00000000, company_id: null },
          { id: 'uom-7', name: 'Caja 12 Unidades', code: 'CJ-12', abbreviation: 'cj12', conversion_factor: 12.00000000, company_id: 'tenant-1' }
        ] as UOM[]);
        this.loading.set(false);
      }
    });
  }

  onViewDetails(uom: UOM) {
    this.drawerService.open(UomFormComponent, {
      title: 'Detalles de Unidad',
      subtitle: 'Vista de Solo Lectura',
      icon: 'straighten'
    }, { item: uom });
  }

  openAddModal() {
    this.drawerService.open(UomFormComponent, {
      title: 'Nueva Unidad',
      subtitle: 'Configuración de Magnitud',
      icon: 'add_circle'
    });
  }

  onEditUom(uom: UOM) {
    this.drawerService.open(UomFormComponent, {
      title: 'Editar Unidad',
      subtitle: 'Modificación de Magnitud',
      icon: 'edit_square'
    }, { item: uom });
  }
}
