import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-product-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="industrial-card p-6">
      <p class="text-surface-text-muted italic">
        Formulario de Producto (Creación/Edición)
      </p>
    </div>
  `
})
export class ProductFormComponent { }