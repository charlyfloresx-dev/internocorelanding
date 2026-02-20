import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-product-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <p class="text-gray-500 italic">
      Formulario de Producto (Creación/Edición)
    </p>
  `
})
export class ProductFormComponent { }