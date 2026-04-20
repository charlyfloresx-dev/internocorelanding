import { Component, OnInit, inject, signal, computed, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MasterDataService, Warehouse } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { TranslationService } from '../../core/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import { WarehouseModalComponent } from '../../shared/components/warehouse-modal.component';

@Component({
  selector: 'app-warehouse-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule, WarehouseModalComponent],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            {{ t('catalog.warehouses.title', 'Red de Almacenes') }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            {{ t('catalog.warehouses.subtitle', 'Gestión de centros de distribución y capacidad') }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              placeholder="Buscar almacén..."
              class="pl-12 pr-6 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64 outline-none"
            >
          </div>

          <button 
            (click)="loadWarehouses()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all"
          >
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <button 
            (click)="openAddModal()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-sm">add</mat-icon>
            {{ t('catalog.warehouses.new', 'Nuevo Almacén') }}
          </button>
        </div>
      </div>

      <!-- Modal Wrapper -->
      @if (isModalVisible()) {
        <app-warehouse-modal #whModal (saved)="onWhSaved($event)"></app-warehouse-modal>
      }

      <!-- Warehouses Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        @for (wh of filteredWarehouses(); track wh.id) {
          <div class="group industrial-card p-8 space-y-6 relative overflow-hidden">
            <!-- Background Accent -->
            <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-bl-[5rem] -mr-10 -mt-10 group-hover:scale-110 transition-transform duration-700"></div>

            <div class="flex justify-between items-start relative">
              <div class="space-y-2">
                <div class="flex items-center gap-3">
                  <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono text-surface-text-muted">
                    {{ wh.code }}
                  </span>
                  @if (masterData.isGlobal(wh)) {
                    <mat-icon class="text-primary text-sm" title="Global">public</mat-icon>
                  }
                </div>
                <h3 class="text-2xl font-black text-surface-text uppercase tracking-tight">{{ wh.name }}</h3>
              </div>
              <div class="p-4 bg-surface-bg border border-surface-border rounded-3xl">
                <mat-icon class="text-primary">warehouse</mat-icon>
              </div>
            </div>

            <!-- Occupancy KPI -->
            <div class="space-y-3">
              <div class="flex justify-between items-end">
                <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Ocupación Actual</span>
                <span class="text-sm font-mono font-bold" [ngClass]="getOccupancyColor(wh)">
                  {{ getOccupancyPercent(wh) }}%
                </span>
              </div>
              <div class="h-3 bg-surface-bg border border-surface-border rounded-full overflow-hidden p-0.5">
                <div 
                  class="h-full rounded-full transition-all duration-1000 ease-out shadow-sm"
                  [style.width.%]="getOccupancyPercent(wh)"
                  [ngClass]="getOccupancyBg(wh)"
                ></div>
              </div>
              <div class="flex justify-between text-[9px] font-mono text-surface-text-muted uppercase">
                <span>0 m³</span>
                <span>Capacidad: {{ wh.capacity | number }} m³</span>
              </div>
            </div>

            <div class="pt-6 border-t border-surface-border flex justify-between items-center">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" [class.bg-emerald-500]="wh.status === 'ACTIVE'" [class.bg-rose-500]="wh.status === 'INACTIVE'"></div>
                <span class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted">{{ wh.status }}</span>
              </div>
              
              <div class="flex items-center gap-2">
                <button class="p-2 hover:bg-surface-bg border border-transparent hover:border-surface-border text-surface-text-muted rounded-xl transition-all">
                  <mat-icon class="text-sm">history</mat-icon>
                </button>
                @if (masterData.isGlobal(wh) && !isAdmin()) {
                  <button class="p-2 text-surface-text-muted/30 cursor-not-allowed">
                    <mat-icon class="text-sm">lock</mat-icon>
                  </button>
                } @else {
                  <button (click)="onEditWh(wh)" class="p-2 hover:bg-primary/10 text-primary rounded-xl transition-all">
                    <mat-icon class="text-sm">edit</mat-icon>
                  </button>
                }
              </div>
            </div>
          </div>
        } @empty {
          <div class="col-span-full py-32 text-center industrial-card border-dashed">
            <mat-icon class="text-6xl text-surface-text-muted/20 mb-4">warehouse</mat-icon>
            <p class="text-surface-text-muted font-mono italic">No se encontraron almacenes disponibles.</p>
          </div>
        }
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
export class WarehouseCatalogComponent implements OnInit {
  masterData = inject(MasterDataService);
  notifications = inject(NotificationService);
  translation = inject(TranslationService);
  auth = inject(AuthService);

  warehouses = signal<Warehouse[]>([]);
  loading = signal(false);
  searchQuery = '';
  isModalVisible = signal(false);

  @ViewChild('whModal') whModal!: WarehouseModalComponent;

  isAdmin = computed(() => this.auth.roles().includes('admin'));

  filteredWarehouses = computed(() => {
    let list = this.warehouses();
    
    // Tenancy Rule: If not global admin, only show current tenant's warehouses
    if (!this.auth.roles().includes('admin')) {
      const companyId = this.auth.activeCompanyId();
      list = list.filter(w => w.company_id === companyId || w.company_id === null);
    }

    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(w => 
        w.name.toLowerCase().includes(q) || 
        w.code.toLowerCase().includes(q)
      );
    }

    return list;
  });

  ngOnInit() {
    this.loadWarehouses();
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  loadWarehouses() {
    this.loading.set(true);
    this.masterData.getWarehouses().subscribe({
      next: (res) => {
        this.warehouses.set(res.data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading warehouses:', err);
        // Mock data
        this.warehouses.set([
          { id: 'wh-1', name: 'Planta Norte - Automotriz', code: 'WH-NRT', capacity: 50000, current_occupancy: 32000, status: 'ACTIVE', company_id: null },
          { id: 'wh-2', name: 'Centro Logístico Bajío', code: 'WH-BAJ', capacity: 120000, current_occupancy: 115000, status: 'ACTIVE', company_id: null },
          { id: 'wh-3', name: 'Almacén de Refacciones CDMX', code: 'WH-CDMX', capacity: 15000, current_occupancy: 12000, status: 'ACTIVE', company_id: 'tenant-1' },
          { id: 'wh-4', name: 'Depósito Temporal Toluca', code: 'WH-TOL', capacity: 8000, current_occupancy: 2000, status: 'INACTIVE', company_id: 'tenant-1' }
        ] as Warehouse[]);
        this.loading.set(false);
      }
    });
  }

  getOccupancyPercent(wh: Warehouse): number {
    if (!wh.capacity) return 0;
    return Math.round(((wh.current_occupancy || 0) / wh.capacity) * 100);
  }

  getOccupancyColor(wh: Warehouse): string {
    const p = this.getOccupancyPercent(wh);
    if (p < 70) return 'text-emerald-500';
    if (p < 90) return 'text-amber-500';
    return 'text-rose-500';
  }

  getOccupancyBg(wh: Warehouse): string {
    const p = this.getOccupancyPercent(wh);
    if (p < 70) return 'bg-emerald-500';
    if (p < 90) return 'bg-amber-500';
    return 'bg-rose-500';
  }

  openAddModal() {
    this.isModalVisible.set(true);
    setTimeout(() => this.whModal.open());
  }

  onEditWh(wh: Warehouse) {
    this.isModalVisible.set(true);
    setTimeout(() => this.whModal.open(wh));
  }

  onWhSaved(wh: Warehouse) {
    this.loadWarehouses();
    this.isModalVisible.set(false);
  }
}
