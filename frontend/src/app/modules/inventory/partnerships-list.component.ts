
import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InventoryService } from '@services/inventory.service';
import { PartnershipType, PartnershipStatus } from '@models/api.types';

@Component({
  selector: 'app-partnerships-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <h1 class="text-2xl font-bold text-white tracking-tight">Socios Comerciales</h1>
           <p class="text-slate-400 text-sm">Directorio de Proveedores y Clientes</p>
        </div>
        <button class="bg-sky-600 hover:bg-sky-500 text-white font-bold py-2 px-4 rounded-lg shadow-lg shadow-sky-900/20 transition-all flex items-center gap-2">
           <i class="fa-solid fa-plus"></i> Registrar Socio
        </button>
      </div>

      <!-- Filters -->
      <div class="flex gap-2 border-b border-slate-700 pb-1">
        <button class="px-4 py-2 text-sm font-bold text-sky-400 border-b-2 border-sky-400">Todos</button>
        <button class="px-4 py-2 text-sm font-bold text-slate-400 hover:text-white transition-colors">Proveedores</button>
        <button class="px-4 py-2 text-sm font-bold text-slate-400 hover:text-white transition-colors">Clientes</button>
      </div>

      <!-- Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        @for (partner of service.partnerships(); track partner.id) {
          <div class="bg-slate-800 rounded-xl border border-slate-700 p-5 hover:border-slate-500 transition-colors group relative overflow-hidden">
             
             <!-- Corner Badge -->
             <div class="absolute top-0 right-0 p-4">
                <span [class]="getBadgeClass(partner.type)">
                  {{ partner.type === 1 ? 'Cliente' : 'Proveedor' }}
                </span>
             </div>

             <div class="flex items-center gap-4 mb-4">
                <div class="w-12 h-12 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-lg font-bold text-slate-400 group-hover:text-white group-hover:border-sky-500 transition-colors">
                   {{ partner.name.charAt(0) }}
                </div>
                <div>
                   <h3 class="text-white font-bold truncate pr-16">{{ partner.name }}</h3>
                   <p class="text-xs text-slate-500 font-mono">{{ partner.code }}</p>
                </div>
             </div>
             
             <div class="space-y-2 text-sm text-slate-400">
               <div class="flex justify-between border-b border-slate-700/50 pb-2">
                 <span>Estatus</span>
                 <span [class]="getStatusColor(partner.status)">{{ partner.status }}</span>
               </div>
               <div class="flex justify-between pt-1">
                 <span>Contacto</span>
                 <span class="text-slate-300">admin&#64;{{ partner.name.split(' ')[0].toLowerCase() }}.com</span>
               </div>
             </div>

             <!-- Actions Footer -->
             <div class="mt-4 pt-3 border-t border-slate-700 flex justify-end gap-2">
               <button class="text-xs font-bold text-slate-400 hover:text-white px-2 py-1">Historial</button>
               <button class="text-xs font-bold text-sky-500 hover:text-sky-400 px-2 py-1">Editar</button>
             </div>
          </div>
        }
      </div>
    </div>
  `
})
export class PartnershipsListComponent implements OnInit {
  public service = inject(InventoryService);
  
  // Expose Enum to Template
  PartnershipType = PartnershipType; 

  ngOnInit() {
    this.service.loadCatalogs();
  }

  getBadgeClass(type: PartnershipType): string {
    if (type === PartnershipType.Customer) {
      return 'text-[10px] font-bold uppercase tracking-wider text-green-400 bg-green-400/10 px-2 py-1 rounded border border-green-400/20';
    }
    return 'text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-400/10 px-2 py-1 rounded border border-purple-400/20';
  }

  getStatusColor(status: PartnershipStatus): string {
    switch(status) {
      case PartnershipStatus.Platinum: return 'text-sky-400 font-bold';
      case PartnershipStatus.Gold: return 'text-yellow-400 font-bold';
      case PartnershipStatus.Silver: return 'text-slate-300 font-bold';
      default: return 'text-slate-500';
    }
  }
}
