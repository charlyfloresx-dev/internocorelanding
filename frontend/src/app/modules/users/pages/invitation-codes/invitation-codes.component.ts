import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { UserApiService } from '../../services/user-api.service';
import { InvitationResponse, RoleResponse } from '../../../../core/models/api.types';

@Component({
  selector: 'app-invitation-codes',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6">
      <header class="mb-6 flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">Códigos de Invitación</h1>
          <p class="text-gray-500">Genera accesos para nuevos integrantes.</p>
        </div>
      </header>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Generador -->
        <div class="lg:col-span-1 bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-fit">
          <h2 class="text-lg font-semibold mb-4">Nueva Invitación</h2>
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Email Destino</label>
              <input type="email" #emailInput placeholder="colega&#64;empresa.com" 
                     class="w-full px-3 py-2 border border-gray-300 rounded-md">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rol a Asignar</label>
              <select #roleSelect class="w-full px-3 py-2 border border-gray-300 rounded-md">
                @for (role of roles(); track role.id) {
                  <option [value]="role.id">{{ role.name }}</option>
                }
              </select>
            </div>
            <button (click)="createInvitation(emailInput.value, roleSelect.value)"
                    class="w-full bg-indigo-600 text-white py-2 rounded-md font-semibold hover:bg-indigo-700 transition-colors">
              Generar Código
            </button>
          </div>
        </div>

        <!-- Lista de Invitaciones -->
        <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div class="p-4 bg-gray-50 border-b border-gray-200">
            <h2 class="font-semibold text-gray-700">Invitaciones Activas</h2>
          </div>
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Código</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estado</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expira</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              @for (inv of invitations(); track inv.id) {
                <tr class="hover:bg-gray-50">
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ inv.email }}</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <code class="bg-gray-100 px-2 py-1 rounded text-indigo-600 font-mono text-xs">{{ inv.code }}</code>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span [class]="inv.is_used ? 'text-gray-400' : 'text-green-600 font-medium'" class="text-xs">
                       {{ inv.is_used ? 'Utilizado' : 'Pendiente' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-500">
                    {{ inv.expires_at | date:'short' }}
                  </td>
                </tr>
              } @empty {
                <tr>
                  <td colspan="4" class="px-6 py-10 text-center text-gray-400 italic">No hay invitaciones registradas</td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class InvitationCodesComponent implements OnInit {
  private userApi = inject(UserApiService);
  roles = signal<RoleResponse[]>([]);
  invitations = signal<InvitationResponse[]>([]);

  ngOnInit() {
    this.userApi.getRoles().subscribe(res => this.roles.set(res.data ?? []));
    // En una implementación real, aquí se cargarían las invitaciones existentes
  }

  createInvitation(email: string, role_id: string) {
    if (!email || !role_id) return;
    this.userApi.inviteUser({ email, role_id }).subscribe({
      next: (res) => {
        if (res.status === 'success' && res.data) {
          this.invitations.update(list => [res.data!, ...list]);
        }
      },
      error: (err) => console.error('Error creating invitation:', err)
    });
  }
}
