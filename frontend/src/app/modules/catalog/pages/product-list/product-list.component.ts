import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MasterDataService } from '../../../../core/services/master-data.service';
import { ProductRead } from '../../../../core/models/master-data.types';
import { catchError, of } from 'rxjs';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full h-full flex flex-col p-6">
      <header class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-primary">Gestión de Productos</h1>
        <button class="bg-primary text-white px-4 py-2 rounded shadow hover:bg-opacity-90 transition-colors">
          <i class="fa-solid fa-plus mr-2"></i>Nuevo Producto
        </button>
      </header>

      <main class="bg-white rounded-lg shadow p-6 flex-1 border border-gray-200">
        @if (masterDataService.loading()) {
          <p class="text-gray-500 italic">Cargando productos desde Master Data Service...</p>
        } @else if (error()) {
          <p class="text-red-500 font-semibold">Error: {{ error() }}</p>
        } @else {
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                  <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                @for (product of products(); track product.id) {
                  <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ product.sku }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ product.name }}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                      <span [ngClass]="product.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full">
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
  `
})
export class ProductListComponent implements OnInit {
  masterDataService = inject(MasterDataService);

  products = signal<ProductRead[]>([]);
  error = signal<string | null>(null);

  ngOnInit(): void {
    this.masterDataService.getProducts().pipe(
      catchError(err => {
        this.error.set('No se pudo conectar con el servicio de Master Data. Verifique que el puerto 8003 esté disponible.');
        return of([]);
      })
    ).subscribe(products => {
      this.products.set(products);
    });
  }
}