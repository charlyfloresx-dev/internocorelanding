import { Component, inject, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InventoryService } from '../../core/services/inventory.service';
import { AuthService } from '../../core/services/auth.service';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-general-dashboard',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      <div class="flex flex-col">
        <h1 class="text-2xl font-black text-white tracking-tighter uppercase italic glow-text">Dashboard General</h1>
        <p class="text-surface-text-muted text-[10px] font-bold uppercase tracking-[0.2em] opacity-60">Visión global de la planta</p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Inventory Card -->
        <div class="industrial-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-surface-text-muted text-[10px] font-black uppercase tracking-widest">Inventario Total</h3>
            <mat-icon class="text-primary">inventory_2</mat-icon>
          </div>
          <div class="text-3xl font-black text-white glow-text">{{ totalItems() }}</div>
          <div class="text-[8px] text-surface-text-muted uppercase font-bold tracking-[0.2em] mt-2 italic opacity-60">SKUs registrados en el último turno</div>
        </div>

        <!-- Alerts Card -->
        <div class="industrial-card p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-surface-text-muted text-[10px] font-black uppercase tracking-widest">Alertas de Stock</h3>
            <mat-icon class="text-amber-500">warning</mat-icon>
          </div>
          <div class="text-3xl font-black text-amber-500 drop-shadow-[0_0_8px_rgba(245,158,11,0.3)]">{{ lowStockItems() }}</div>
          <div class="text-[8px] text-surface-text-muted uppercase font-bold tracking-[0.2em] mt-2 italic opacity-60">Productos por debajo del mínimo crítico</div>
        </div>

        <!-- Production Placeholder -->
        <div class="industrial-card p-6 opacity-60">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-surface-text-muted text-[10px] font-black uppercase tracking-widest">Producción Activa</h3>
            <mat-icon class="text-emerald-500">factory</mat-icon>
          </div>
          <div class="text-3xl font-black text-white">--</div>
          <div class="text-[8px] text-surface-text-muted uppercase font-bold tracking-[0.2em] mt-2 italic opacity-60">Módulo en fase de calibración</div>
        </div>
      </div>

      <!-- BANNER DE RESCATE (God Mode active intervention) -->
      @if (isRescueModeActive()) {
        <div class="bg-amber-500/10 border border-amber-500/30 p-4 rounded-xl flex items-center gap-4 animate-pulse">
          <div class="h-10 w-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.2)]">
            <mat-icon>shield_with_heart</mat-icon>
          </div>
          <div>
            <h4 class="text-amber-500 font-black text-[10px] uppercase tracking-widest">Rescate Técnico Activo</h4>
            <p class="text-amber-200/50 text-[9px] font-bold uppercase tracking-tight italic">Acceso extendido por intervención del sistema</p>
          </div>
        </div>
      }
    </div>
  `
})
export class GeneralDashboardComponent implements OnInit {
  private inventoryService = inject(InventoryService);
  private authService = inject(AuthService);

  totalItems = computed(() => this.inventoryService.items().length);
  lowStockItems = computed(() => this.inventoryService.items().filter(i => i.stockQuantity < 10).length);

  isRescueModeActive = computed(() => {
    const permissions = this.authService.currentContext()?.permissions || [];
    return permissions.includes('system.rescue.active');
  });

  ngOnInit() {
    this.inventoryService.loadItems();
  }
}