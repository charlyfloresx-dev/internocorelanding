import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InventoryService } from '@services/inventory.service';
import { Warehouse } from '../../core/models/api.types';

@Component({
  selector: 'app-warehouse-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-white tracking-tight">Almacenes</h1>
          <p class="text-slate-400 text-sm">Gestión de ubicaciones físicas y lógicas</p>
        </div>
        <button class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-lg shadow-lg shadow-sky-900/20 transition-all flex items-center gap-2">
          <i class="fa-solid fa-plus"></i> Nuevo Almacén
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        @for (wh of service.warehouses(); track wh.id) {
          <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all group relative overflow-hidden">
            <div class="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <i class="fa-solid fa-warehouse text-6xl"></i>
            </div>
            
            <div class="flex items-start justify-between mb-4 relative z-10">
              <div class="w-12 h-12 rounded-lg bg-slate-800 flex items-center justify-center text-sky-500 border border-slate-700">
                <i class="fa-solid fa-box-open text-xl"></i>
              </div>
              <span class="px-2 py-1 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-400 border border-slate-700">
                {{ wh.typeName }}
              </span>
            </div>

            <h3 class="text-lg font-bold text-white mb-1 relative z-10">{{ wh.name }}</h3>
            <p class="text-sm text-slate-400 mb-4 relative z-10">{{ wh.location }}</p>

            <div class="grid grid-cols-2 gap-4 border-t border-slate-800 pt-4 relative z-10">
              <div>
                <div class="text-[10px] uppercase font-bold text-slate-500">Capacidad</div>
                <div class="text-white font-mono">{{ wh.capacity | number }} <span class="text-xs text-slate-600">{{ wh.unitCode }}</span></div>
              </div>
              <div>
                <div class="text-[10px] uppercase font-bold text-slate-500">Grupo</div>
                <div class="text-white">{{ wh.groupName }}</div>
              </div>
            </div>

            <div class="mt-4 flex gap-2 relative z-10">
              <button class="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded transition-colors">
                <i class="fa-solid fa-pen-to-square mr-1"></i> Editar
              </button>
              <button class="flex-1 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold rounded transition-colors">
                <i class="fa-solid fa-list-check mr-1"></i> Inventario
              </button>
            </div>
          </div>
        }
        
        @if (service.warehouses().length === 0) {
          <div class="col-span-full py-12 text-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800 border-dashed">
            <i class="fa-solid fa-warehouse text-4xl mb-3 opacity-50"></i>
            <p>No hay almacenes registrados.</p>
          </div>
        }
      </div>
    </div>
  `
})
export class WarehouseListComponent implements OnInit {
  public service = inject(InventoryService);

  ngOnInit() {
    // Cargar catálogos necesarios
    this.service.loadCatalogs();
    this.service.loadWarehouseCatalogs();
  }
}