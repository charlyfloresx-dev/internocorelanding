import { Component, signal, inject, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { InventoryService } from '../../core/services/inventory.service';
import { PendingPutawayItem } from '../../core/models/domain.types';

@Component({
  selector: 'app-pending-putaway',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="min-h-screen bg-surface-bg text-surface-text font-mono p-6">
      <div class="max-w-6xl mx-auto space-y-6">
        
        <!-- HEADER -->
        <div class="flex items-center justify-between mb-8">
          <div>
            <h1 class="text-2xl font-black text-emerald-400 uppercase tracking-widest flex items-center gap-3">
              <mat-icon>inbox</mat-icon>
              Cola de Put-Away Pendientes
            </h1>
            <p class="text-sm text-surface-text-muted mt-1">
              Material en DOCK esperando asignación a ubicación final.
            </p>
          </div>
          <div class="flex items-center gap-4">
            <button (click)="loadPending()" class="w-10 h-10 rounded-xl bg-surface-card border border-surface-border flex items-center justify-center hover:bg-surface-border/50 transition-colors">
              <mat-icon [class.animate-spin]="isLoading()" class="text-emerald-400">sync</mat-icon>
            </button>
          </div>
        </div>

        <!-- LIST -->
        <div *ngIf="isLoading() && !pendingItems().length" class="text-center py-12">
          <mat-icon class="animate-spin text-emerald-500 text-4xl">sync</mat-icon>
          <p class="text-surface-text-muted font-bold mt-4">Cargando cola DOCK...</p>
        </div>

        <div *ngIf="!isLoading() && pendingItems().length === 0" class="bg-surface-card border border-surface-border rounded-2xl p-12 text-center shadow-xl">
          <mat-icon class="text-6xl text-emerald-500/20 mb-4">check_circle</mat-icon>
          <h2 class="text-xl font-black text-emerald-400">DOCK LIMPIO</h2>
          <p class="text-surface-text-muted mt-2">No hay movimientos pendientes de ubicación.</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div *ngFor="let item of pendingItems()" 
               class="bg-surface-card border border-surface-border rounded-2xl p-6 shadow-xl hover:border-emerald-500/50 transition-colors relative overflow-hidden group">
            
            <!-- Urgent indicator -->
            <div *ngIf="item.days_in_dock > 2" class="absolute top-0 left-0 w-full h-1 bg-red-500"></div>
            
            <div class="flex justify-between items-start mb-4">
              <div>
                <span class="text-[10px] font-black uppercase text-surface-text-muted block">Movement ID</span>
                <span class="text-xs font-mono text-emerald-400">{{ item.movement_id | slice:0:8 }}...</span>
              </div>
              <div class="text-right">
                <span class="text-[10px] font-black uppercase" 
                      [class.text-red-400]="item.days_in_dock > 2"
                      [class.text-amber-400]="item.days_in_dock === 2"
                      [class.text-emerald-400]="item.days_in_dock < 2">
                  {{ item.days_in_dock }} Días en Dock
                </span>
              </div>
            </div>

            <div class="space-y-4">
              <div>
                <span class="text-[10px] font-black uppercase text-surface-text-muted block">Producto SKU</span>
                <span class="text-lg font-black text-surface-text">{{ item.product_id }}</span> <!-- Ideally resolve to SKU, but product_id provided by backend -->
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <span class="text-[10px] font-black uppercase text-surface-text-muted block">Cantidad Pendiente</span>
                  <span class="text-base font-black text-amber-400">{{ item.available_quantity }} / {{ item.quantity }}</span>
                </div>
                <div>
                  <span class="text-[10px] font-black uppercase text-surface-text-muted block">Pedimento</span>
                  <span class="text-xs font-black px-2 py-1 bg-indigo-500/20 text-indigo-400 rounded border border-indigo-500/30 inline-block mt-1">
                    {{ item.pedimento_number || 'N/A' }}
                  </span>
                </div>
              </div>
            </div>

            <button (click)="routeToPutAway(item)" 
                    class="w-full mt-6 py-3 rounded-xl bg-surface-bg border border-emerald-500/30 text-emerald-400 font-black uppercase hover:bg-emerald-500 hover:text-surface-bg transition-colors flex items-center justify-center gap-2">
              <mat-icon>forklift</mat-icon>
              <span>Ubicar Material</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  `
})
export class PendingPutawayComponent implements OnInit {
  private inv = inject(InventoryService);
  private router = inject(Router);

  isLoading = signal(true);
  pendingItems = signal<PendingPutawayItem[]>([]);

  ngOnInit() {
    this.loadPending();
  }

  loadPending() {
    this.isLoading.set(true);
    const warehouseId = this.inv.warehouses()[0]?.id;
    this.inv.getPendingPutaway(warehouseId).subscribe({
      next: (res) => {
        // Apply operational FIFO sorting: longest in dock first
        const sorted = (res.data || []).sort((a, b) => b.days_in_dock - a.days_in_dock);
        this.pendingItems.set(sorted);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
      }
    });
  }

  routeToPutAway(item: PendingPutawayItem) {
    // Navigate to put-away and pass state to autocomplete Step 1
    // For now we just go to the route. In inventory-put-away it should read history.state if needed,
    // or the operator can just see the SKU to type in. 
    // Passing movement_id and pedimento for context
    this.router.navigate(['/inventory/put-away'], { 
      state: { 
        product_id: item.product_id,
        quantity: item.available_quantity,
        pedimento: item.pedimento_number,
        is_from_queue: true
      } 
    });
  }
}
