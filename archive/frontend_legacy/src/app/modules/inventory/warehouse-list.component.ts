import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { heroPlus, heroMapPin, heroCubeTransparent, heroPencilSquare, heroRectangleStack, heroHome } from '@ng-icons/heroicons/outline';
import { InventoryService } from '@services/inventory.service';
import { Warehouse } from '../../core/models/api.types';

@Component({
  selector: 'app-warehouse-list',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-surface-text tracking-tight">Almacenes</h1>
          <p class="text-surface-text-muted text-sm">Gestión de ubicaciones físicas y lógicas</p>
        </div>
        <button class="px-4 py-2 bg-primary hover:bg-primary-dark text-surface-bg font-bold rounded-lg shadow-lg shadow-primary/20 transition-all flex items-center gap-2">
          <ng-icon name="heroPlus"></ng-icon> Nuevo Almacén
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        @for (wh of service.warehouses(); track wh.id) {
          <div class="industrial-card p-6">
            <div class="absolute top-0 right-0 p-4 opacity-[0.05] group-hover:opacity-[0.15] transition-opacity">
              <ng-icon name="heroHome" class="text-6xl text-primary"></ng-icon>
            </div>
            
            <div class="flex items-start justify-between mb-4 relative z-10">
              <div class="w-12 h-12 rounded-lg bg-surface-bg flex items-center justify-center text-primary border border-surface-border">
                <ng-icon name="heroCubeTransparent" class="text-xl"></ng-icon>
              </div>
              <span class="px-2 py-1 rounded text-[10px] font-bold uppercase bg-surface-bg text-surface-text-muted border border-surface-border">
                {{ wh.typeName }}
              </span>
            </div>

            <h3 class="text-lg font-bold text-surface-text mb-1 relative z-10">{{ wh.name }}</h3>
            <p class="text-sm text-surface-text-muted mb-4 relative z-10 flex items-center gap-1"><ng-icon name="heroMapPin"></ng-icon> {{ wh.location }}</p>

            <div class="grid grid-cols-2 gap-4 border-t border-surface-border pt-4 relative z-10">
              <div>
                <div class="text-[10px] uppercase font-bold text-surface-text-muted">Capacidad</div>
                <div class="text-surface-text font-mono">{{ wh.capacity | number }} <span class="text-xs text-surface-text-muted">{{ wh.unitCode }}</span></div>
              </div>
              <div>
                <div class="text-[10px] uppercase font-bold text-surface-text-muted">Grupo</div>
                <div class="text-surface-text">{{ wh.groupName }}</div>
              </div>
            </div>

            <div class="mt-4 flex gap-2 relative z-10">
              <button class="flex-1 py-2 bg-surface-bg hover:bg-surface-border text-surface-text-muted text-xs font-bold rounded transition-colors flex items-center justify-center gap-1">
                <ng-icon name="heroPencilSquare"></ng-icon> Editar
              </button>
              <button class="flex-1 py-2 bg-surface-bg hover:bg-surface-border text-surface-text-muted text-xs font-bold rounded transition-colors flex items-center justify-center gap-1">
                <ng-icon name="heroRectangleStack"></ng-icon> Inventario
              </button>
            </div>
          </div>
        }
        
        @if (service.warehouses().length === 0) {
          <div class="col-span-full py-12 text-center text-surface-text-muted bg-surface-bg/50 rounded-xl border border-surface-border border-dashed">
            <ng-icon name="heroHome" class="text-4xl mb-3 opacity-50"></ng-icon>
            <p>No hay almacenes registrados.</p>
          </div>
        }
      </div>
    </div>
  `,
  providers: [provideIcons({ heroPlus, heroMapPin, heroCubeTransparent, heroPencilSquare, heroRectangleStack, heroHome })]
})
export class WarehouseListComponent implements OnInit {
  public service = inject(InventoryService);

  ngOnInit() {
    // Cargar catálogos necesarios
    this.service.loadCatalogs();
    this.service.loadWarehouseCatalogs();
  }
}