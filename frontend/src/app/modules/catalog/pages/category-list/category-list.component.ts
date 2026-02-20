import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-category-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full h-full flex flex-col p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-primary">Gestión de Categorías</h1>
        <button class="bg-primary text-white px-4 py-2 rounded shadow hover:bg-opacity-90 transition-colors">
          <i class="fa-solid fa-layer-group mr-2"></i>Nueva Categoría
        </button>
      </div>
      <div class="bg-white rounded-lg shadow p-6 flex-1 border border-gray-200">
        <p class="text-gray-500 italic">Category List Page - Jerarquía de productos.</p>
      </div>
    </div>
  `
})
export class CategoryListComponent {}