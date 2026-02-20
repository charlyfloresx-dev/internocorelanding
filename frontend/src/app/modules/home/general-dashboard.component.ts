import { Component, inject, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InventoryService } from '../../core/services/inventory.service';

@Component({
  selector: 'app-general-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      <h1 class="text-2xl font-bold text-white tracking-tight">Dashboard General</h1>
      <p class="text-slate-400 text-sm">Visión global de la planta</p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Inventory Card -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-slate-400 text-xs font-bold uppercase">Inventario Total</h3>
            <i class="fa-solid fa-boxes-stacked text-sky-500"></i>
          </div>
          <div class="text-3xl font-bold text-white">{{ totalItems() }}</div>
          <div class="text-xs text-slate-500 mt-2">SKUs registrados</div>
        </div>

        <!-- Alerts Card -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-slate-400 text-xs font-bold uppercase">Alertas de Stock</h3>
            <i class="fa-solid fa-triangle-exclamation text-yellow-500"></i>
          </div>
          <div class="text-3xl font-bold text-yellow-500">{{ lowStockItems() }}</div>
          <div class="text-xs text-slate-500 mt-2">Productos por debajo del mínimo</div>
        </div>

        <!-- Production Placeholder -->
        <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg opacity-50">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-slate-400 text-xs font-bold uppercase">Producción Activa</h3>
            <i class="fa-solid fa-industry text-emerald-500"></i>
          </div>
          <div class="text-3xl font-bold text-white">--</div>
          <div class="text-xs text-slate-500 mt-2">Módulo en construcción</div>
        </div>
      </div>
    </div>
  `
})
export class GeneralDashboardComponent implements OnInit {
  private inventoryService = inject(InventoryService);

  totalItems = computed(() => this.inventoryService.items().length);
  lowStockItems = computed(() => this.inventoryService.items().filter(i => i.stockQuantity < 10).length);

  ngOnInit() {
    this.inventoryService.loadItems();
  }
}