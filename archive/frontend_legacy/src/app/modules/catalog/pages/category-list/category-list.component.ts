import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { heroQueueList } from '@ng-icons/heroicons/outline';

@Component({
  selector: 'app-category-list',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  template: `
    <div class="w-full h-full flex flex-col p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-surface-text tracking-tight">Gestión de Categorías</h1>
        <button class="bg-primary text-surface-bg px-4 py-2 rounded-lg shadow-sm hover:bg-primary-dark transition-colors text-sm font-medium flex items-center gap-2">
          <ng-icon name="heroQueueList"></ng-icon>Nueva Categoría
        </button>
      </div>
      <div class="industrial-card p-6 flex-1">
        <p class="text-surface-text-muted italic">Category List Page - Jerarquía de productos.</p>
      </div>
    </div>
  `,
  providers: [provideIcons({ heroQueueList })]
})
export class CategoryListComponent { }