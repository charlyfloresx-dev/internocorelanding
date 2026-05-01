import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MasterDataService, Category, Brand } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { TranslationService } from '../../core/services/translation.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { CategoryBrandFormComponent } from '../../shared/components/category-brand-form.component';

@Component({
  selector: 'app-category-brand-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">
      <!-- Header: Control Grid Style -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            {{ t('catalog.categories.title', 'Taxonomía Maestra') }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            {{ t('catalog.categories.subtitle', 'Organización jerárquica por categorías y marcas') }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <!-- Integrated Search -->
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              [placeholder]="activeTab() === 'categories' ? 'Buscar categoría...' : 'Buscar marca...'"
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
            (click)="loadData()"
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
            {{ activeTab() === 'categories' ? 'Nueva Categoría' : 'Nueva Marca' }}
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex items-center gap-2 p-1 bg-surface-bg border border-surface-border rounded-2xl w-fit">
        <button 
          (click)="activeTab.set('categories')"
          [class.bg-primary]="activeTab() === 'categories'"
          [class.text-white]="activeTab() === 'categories'"
          [class.dark:text-slate-950]="activeTab() === 'categories'"
          [class.text-surface-text-muted]="activeTab() !== 'categories'"
          class="px-8 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all"
        >
          Categorías
        </button>
        <button 
          (click)="activeTab.set('brands')"
          [class.bg-primary]="activeTab() === 'brands'"
          [class.text-white]="activeTab() === 'brands'"
          [class.dark:text-slate-950]="activeTab() === 'brands'"
          [class.text-surface-text-muted]="activeTab() !== 'brands'"
          class="px-8 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all"
        >
          Marcas
        </button>
      </div>

      <!-- Control Grid Table -->
      <div class="industrial-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50 border-b border-surface-border">
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">ID / Badge</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Código</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Nombre</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">Tipo</th>
                <th class="px-8 py-6 text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (item of filteredItems(); track item.id) {
                <tr class="group hover:bg-primary/5 transition-all duration-300">
                  <td class="px-8 py-5">
                    <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono text-surface-text-muted">
                      {{ item.id.substring(0, 8) }}
                    </span>
                  </td>
                  <td class="px-8 py-5">
                    <span class="text-xs font-black text-primary tracking-widest uppercase">{{ item.code }}</span>
                  </td>
                  <td class="px-8 py-5">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-surface-bg border border-surface-border flex items-center justify-center">
                        <mat-icon class="text-sm text-surface-text-muted">
                          {{ activeTab() === 'categories' ? 'folder' : 'diamond' }}
                        </mat-icon>
                      </div>
                      <span class="text-sm font-bold text-surface-text">{{ item.name }}</span>
                    </div>
                  </td>
                  <td class="px-8 py-5">
                    @if (masterData.isGlobal(item)) {
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
                      
                      @if (masterData.isGlobal(item)) {
                        <button (click)="onViewDetails(item)" class="p-2 hover:bg-surface-text-muted/10 text-surface-text-muted rounded-lg transition-all" title="Ver Detalles (Solo Lectura)">
                          <mat-icon class="text-sm">lock</mat-icon>
                        </button>
                      } @else {
                        <button (click)="onEditItem(item)" class="p-2 hover:bg-amber-500/10 text-amber-500 rounded-lg transition-all" title="Editar">
                          <mat-icon class="text-sm">edit</mat-icon>
                        </button>
                      }
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="5" class="px-8 py-32 text-center">
                    <div class="flex flex-col items-center justify-center space-y-4">
                      <div class="w-20 h-20 bg-surface-bg border border-surface-border rounded-full flex items-center justify-center">
                        <mat-icon class="text-4xl text-surface-text-muted/20">
                          {{ activeTab() === 'categories' ? 'folder' : 'diamond' }}
                        </mat-icon>
                      </div>
                      <p class="text-surface-text-muted font-mono text-sm italic">No se encontraron registros con los filtros actuales.</p>
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
export class CategoryBrandCatalogComponent implements OnInit {
  masterData = inject(MasterDataService);
  notifications = inject(NotificationService);
  translation = inject(TranslationService);

  activeTab = signal<'categories' | 'brands'>('categories');
  categories = signal<Category[]>([]);
  brands = signal<Brand[]>([]);
  searchQuery = '';
  statusFilter = 'ALL';
  drawerService = inject(SideDrawerService);

  filteredItems = computed(() => {
    const list = this.activeTab() === 'categories' ? this.categories() : this.brands();
    let filtered = list;

    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      filtered = filtered.filter(i => 
        i.code.toLowerCase().includes(q) || 
        i.name.toLowerCase().includes(q)
      );
    }

    if (this.statusFilter !== 'ALL') {
      filtered = filtered.filter(i => 
        this.statusFilter === 'GLOBAL' ? this.masterData.isGlobal(i) : !this.masterData.isGlobal(i)
      );
    }

    return filtered;
  });

  ngOnInit() {
    this.loadData();
    // Listen for refreshes from the drawer
    this.drawerService.refresh$.subscribe(() => {
      this.loadData();
    });
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  loadData() {
    this.masterData.getCategories().subscribe({
      next: (res) => this.categories.set(res.data),
      error: () => {
        this.categories.set([
          { id: 'cat-1', name: 'Materia Prima', code: 'RAW', company_id: null },
          { id: 'cat-2', name: 'Producto Terminado', code: 'FIN', company_id: null },
          { id: 'cat-3', name: 'Empaque', code: 'PKG', company_id: 'tenant-1' }
        ] as Category[]);
      }
    });

    this.masterData.getBrands().subscribe({
      next: (res) => this.brands.set(res.data),
      error: () => {
        this.brands.set([
          { id: 'br-1', name: 'Generico', code: 'GEN', company_id: null },
          { id: 'br-2', name: 'Interno Premium', code: 'PREM', company_id: 'tenant-1' }
        ] as Brand[]);
      }
    });
  }

  onViewDetails(item: Category | Brand) {
    this.drawerService.open(CategoryBrandFormComponent, {
      title: this.activeTab() === 'categories' ? 'Detalles de Categoría' : 'Detalles de Marca',
      subtitle: 'Vista de Solo Lectura',
      icon: this.activeTab() === 'categories' ? 'folder' : 'diamond'
    }, { context: this.activeTab(), item });
  }

  openAddModal() {
    this.drawerService.open(CategoryBrandFormComponent, {
      title: this.activeTab() === 'categories' ? 'Nueva Categoría' : 'Nueva Marca',
      subtitle: 'Administración de Taxonomía',
      icon: 'add_circle'
    }, { context: this.activeTab() });
  }

  onEditItem(item: Category | Brand) {
    this.drawerService.open(CategoryBrandFormComponent, {
      title: this.activeTab() === 'categories' ? 'Editar Categoría' : 'Editar Marca',
      subtitle: 'Modificación de Atributos',
      icon: 'edit_square'
    }, { context: this.activeTab(), item });
  }
}
