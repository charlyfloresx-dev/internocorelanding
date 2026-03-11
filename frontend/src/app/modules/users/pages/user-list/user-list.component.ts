import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserApiService } from '../../services/user-api.service';
import { ApiResponse } from '../../../../core/models/api.types';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6">
      <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Usuarios de la Empresa</h1>
        <div class="flex gap-2">
          <button class="bg-indigo-600 text-white px-4 py-2 rounded shadow hover:bg-indigo-700 transition-colors">
            <i class="fa-solid fa-user-plus mr-2"></i>Invitar Usuario
          </button>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usuario</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol Principal</th>
              <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
              <th scope="col" class="relative px-6 py-3">
                <span class="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <!-- Los datos se poblarán desde el servicio -->
            <tr class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                  <div class="h-10 w-10 flex-shrink-0">
                    <img class="h-10 w-10 rounded-full" src="https://ui-avatars.com/api/?name=Admin+User" alt="">
                  </div>
                  <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">Admin User</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">admin&#64;interno.com</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded-md text-xs font-semibold uppercase">Administrator</span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Activo</span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button class="text-indigo-600 hover:text-indigo-900 mr-3">Editar</button>
                <button class="text-red-600 hover:text-red-900">Suspender</button>
              </td>
            </tr>
          </tbody>
        </table>
        
        <div class="p-8 text-center" *ngIf="isLoading()">
           <p class="text-gray-400 italic">Cargando usuarios...</p>
        </div>
      </div>
    </div>
  `
})
export class UserListComponent implements OnInit {
  private userApi = inject(UserApiService);
  isLoading = signal(false);

  ngOnInit() {
    // Implementación real cuando el mocking esté listo
    console.log('[UserList] Administrando usuarios de Admin v2');
  }
}
