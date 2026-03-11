import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserApiService } from '../../services/user-api.service';
import { RoleResponse } from '../../../../core/models/api.types';

@Component({
  selector: 'app-user-roles',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6">
      <header class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Gestión de Roles (v2)</h1>
        <p class="text-gray-500">Asignación precisa de roles por empresa.</p>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Roles Disponibles -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
            <i class="fa-solid fa-shield-halved text-indigo-500"></i>
            Catálogo de Roles
          </h2>
          
          <div class="space-y-3">
            @for (role of roles(); track role.id) {
              <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div>
                  <span class="font-medium text-gray-700">{{ role.name }}</span>
                  <p class="text-xs text-gray-400">ID: {{ role.id }}</p>
                </div>
                <button class="text-sm text-indigo-600 hover:underline">Ver Permisos</button>
              </div>
            } @empty {
              <p class="text-gray-400 italic">Cargando roles desde el servidor...</p>
            }
          </div>
        </div>

        <!-- Formulario de Asignación -->
        <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
            <i class="fa-solid fa-user-tag text-emerald-500"></i>
            Asignar Nuevo Rol
          </h2>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email del Usuario</label>
              <input type="email" placeholder="usuario&#64;ejemplo.com" 
                     class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Seleccionar Rol</label>
              <select class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500">
                @for (role of roles(); track role.id) {
                  <option [value]="role.id">{{ role.name }}</option>
                }
              </select>
            </div>

            <button class="w-full bg-emerald-600 text-white py-2 rounded-md font-semibold hover:bg-emerald-700 transition-colors">
              Confirmar Asignación
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class UserRolesComponent implements OnInit {
  private userApi = inject(UserApiService);
  roles = signal<RoleResponse[]>([]);

  ngOnInit() {
    this.userApi.getRoles().subscribe(res => {
      this.roles.set(res.data ?? []);
    });
  }
}
