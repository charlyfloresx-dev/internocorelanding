import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { heroPlus, heroGlobeAmericas } from '@ng-icons/heroicons/outline';
import { MasterDataService } from '../../../../core/services/master-data.service';
import { ProductRead, ApiResponse } from '../../../../core/models/master-data.types';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  template: `
    <div class="w-full h-full flex flex-col p-6">
      <header class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-surface-text tracking-tight">Gestión de Productos</h1>
        <button class="bg-primary text-surface-bg px-4 py-2 rounded-lg flex items-center gap-2 shadow-sm hover:bg-primary-dark transition-colors text-sm font-medium">
          <ng-icon name="heroPlus"></ng-icon>Nuevo Producto
        </button>
      </header>

      <main class="industrial-card p-6 flex-1">
        @if (masterDataService.loading()) {
          <p class="text-surface-text-muted italic">Cargando productos desde Master Data Service...</p>
        } @else if (error()) {
          <p class="text-red-500 font-semibold">Error: {{ error() }}</p>
        } @else {
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-surface-border">
              <thead class="bg-surface-bg border-b border-surface-border">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-surface-text-muted uppercase tracking-wider">SKU</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-surface-text-muted uppercase tracking-wider">Nombre</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-semibold text-surface-text-muted uppercase tracking-wider">Estado</th>
                </tr>
              </thead>
              <tbody class="bg-surface-card divide-y divide-surface-border">
                @for (product of products(); track product.id) {
                  <tr class="hover:bg-surface-bg transition-colors">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-surface-text">{{ product.sku }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-surface-text-muted">
                      <div class="flex items-center gap-2">
                        {{ product.name }}
                        @if (product.is_global_in_group) {
                          <span class="bg-surface-bg text-primary text-[10px] font-bold px-1.5 py-0.5 rounded border border-primary/30 uppercase flex items-center gap-1 neon-glow-cyan shadow-none">
                            <ng-icon name="heroGlobeAmericas"></ng-icon> Grupal
                          </span>
                        }
                      </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <span [ngClass]="product.is_active ? 'bg-neon-green/20 text-neon-green border-neon-green/30' : 'bg-red-500/20 text-red-500 border-red-500/30'" class="px-2 border inline-flex text-xs leading-5 font-semibold rounded-full">
                        {{ product.is_active ? 'Activo' : 'Inactivo' }}
                      </span>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }
      </main>
    </div>
  `,
  providers: [provideIcons({ heroPlus, heroGlobeAmericas })]
})
export class ProductListComponent implements OnInit {
  masterDataService = inject(MasterDataService);

  products = signal<ProductRead[]>([]);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.masterDataService.getProducts().pipe(
      catchError(err => {
        this.error.set('No se pudo conectar con el servicio de Master Data. Verifique que el puerto 8003 esté disponible.');
        return of({ status: 'error', data: [], message: 'Error de conexión', meta: {} } as ApiResponse<ProductRead[]>);
      })
    ).subscribe((response: ApiResponse<ProductRead[]>) => {
      this.products.set(response.data ?? []);
    });
  }
}