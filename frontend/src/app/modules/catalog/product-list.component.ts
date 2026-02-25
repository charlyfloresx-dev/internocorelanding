import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MasterDataService } from '../../core/services/master-data.service';
import { ProductRead } from '../../core/models/master-data.types';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container mx-auto p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800 dark:text-gray-100">Catálogo de Productos</h1>
        <button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
          Nuevo Producto
        </button>
      </div>

      <!-- Spinner de Carga -->
      <div *ngIf="masterDataService.loading()" class="flex justify-center py-10">
        <div class="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-blue-500"></div>
      </div>

      <!-- Tabla de Productos -->
      <div *ngIf="!masterDataService.loading()" class="overflow-x-auto bg-white dark:bg-gray-800 shadow-md rounded-lg">
        <table class="min-w-full leading-normal">
          <thead>
            <tr>
              <th class="px-5 py-3 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                SKU
              </th>
              <th class="px-5 py-3 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                Nombre
              </th>
              <th class="px-5 py-3 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900 text-center text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                Estado
              </th>
              <th class="px-5 py-3 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                Creado el
              </th>
              <th class="px-5 py-3 border-b-2 border-gray-200 dark:border-gray-700 bg-gray-100 dark:bg-gray-900"></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let product of products()" class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <td class="px-5 py-5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm">
                <span class="font-bold font-mono text-gray-900 dark:text-gray-100">{{ product.sku }}</span>
              </td>
              <td class="px-5 py-5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm">
                <p class="text-gray-900 dark:text-gray-200 whitespace-no-wrap">{{ product.name }}</p>
              </td>
              <td class="px-5 py-5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-center">
                <span [ngClass]="product.is_active ? 'bg-green-200 text-green-900' : 'bg-gray-200 text-gray-600'"
                      class="relative inline-block px-3 py-1 font-semibold leading-tight rounded-full">
                  <span aria-hidden="true" class="absolute inset-0 opacity-50 rounded-full"></span>
                  <span class="relative">{{ product.is_active ? 'Activo' : 'Inactivo' }}</span>
                </span>
              </td>
              <td class="px-5 py-5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm">
                <p class="text-gray-900 dark:text-gray-200 whitespace-no-wrap">
                  {{ product.created_at | date:'mediumDate' }}
                </p>
              </td>
              <td class="px-5 py-5 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-right">
                <button class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">
                  Ver Detalle
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `
})
export class ProductListComponent implements OnInit {
  masterDataService = inject(MasterDataService);
  products = signal<ProductRead[]>([]);

  ngOnInit(): void {
    this.masterDataService.getProducts().subscribe({
      next: (products) => {
        this.products.set(products);
        // Validación de Datos (Company ID Check)
        console.table(products);
      },
      error: (err) => console.error(err)
    });
  }
}