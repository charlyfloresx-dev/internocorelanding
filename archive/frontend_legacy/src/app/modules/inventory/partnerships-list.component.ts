
import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { NgIconComponent, provideIcons } from '@ng-icons/core';
import { heroPlus } from '@ng-icons/heroicons/outline';
import { InventoryService } from '@services/inventory.service';
import { PartnershipType, PartnershipStatus } from '@models/api.types';

@Component({
  selector: 'app-partnerships-list',
  standalone: true,
  imports: [CommonModule, NgIconComponent],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
           <h1 class="text-2xl font-bold text-surface-text tracking-tight">Socios Comerciales</h1>
           <p class="text-surface-text-muted text-sm">Directorio de Proveedores y Clientes</p>
        </div>
        <button class="bg-primary hover:bg-primary-dark text-surface-bg font-bold py-2 px-4 rounded-lg shadow-lg shadow-primary/20 transition-all flex items-center gap-2">
           <ng-icon name="heroPlus"></ng-icon> Registrar Socio
        </button>
      </div>

      <!-- Filters -->
      <div class="flex gap-2 border-b border-surface-border pb-1">
        <button class="px-4 py-2 text-sm font-bold text-primary border-b-2 border-primary">Todos</button>
        <button class="px-4 py-2 text-sm font-bold text-surface-text-muted hover:text-surface-text transition-colors">Proveedores</button>
        <button class="px-4 py-2 text-sm font-bold text-surface-text-muted hover:text-surface-text transition-colors">Clientes</button>
      </div>

      <!-- Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        @for (partner of service.partnerships(); track partner.id) {
          <div class="industrial-card p-5 hover:border-surface-text-muted group">
             
             <!-- Corner Badge -->
             <div class="absolute top-0 right-0 p-4">
                <span [class]="getBadgeClass(partner.type)">
                  {{ partner.type === 1 ? 'Cliente' : 'Proveedor' }}
                </span>
             </div>

             <div class="flex items-center gap-4 mb-4 relative z-10">
                <div class="w-12 h-12 rounded-full bg-surface-bg border border-surface-border flex items-center justify-center text-lg font-bold text-surface-text-muted group-hover:text-surface-text group-hover:border-primary transition-colors">
                   {{ partner.name.charAt(0) }}
                </div>
                <div>
                   <h3 class="text-surface-text font-bold truncate pr-16">{{ partner.name }}</h3>
                   <p class="text-xs text-surface-text-muted font-mono">{{ partner.code }}</p>
                </div>
             </div>
             
             <div class="space-y-2 text-sm text-surface-text-muted relative z-10">
               <div class="flex justify-between border-b border-surface-border pb-2">
                 <span>Estatus</span>
                 <span [class]="getStatusColor(partner.status)">{{ partner.status }}</span>
               </div>
               <div class="flex justify-between pt-1">
                 <span>Contacto</span>
                 <span class="text-surface-text">admin&#64;{{ partner.name.split(' ')[0].toLowerCase() }}.com</span>
               </div>
             </div>

             <!-- Actions Footer -->
             <div class="mt-4 pt-3 border-t border-surface-border flex justify-end gap-2 relative z-10">
               <button class="text-xs font-bold text-surface-text-muted hover:text-surface-text px-2 py-1">Historial</button>
               <button class="text-xs font-bold text-primary hover:text-primary-dark px-2 py-1">Editar</button>
             </div>
          </div>
        }
      </div>
    </div>
  `,
  providers: [provideIcons({ heroPlus })]
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
      return 'text-[10px] font-bold uppercase tracking-wider text-neon-green bg-neon-green/10 px-2 py-1 rounded border border-neon-green/20';
    }
    return 'text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-400/10 px-2 py-1 rounded border border-purple-400/20';
  }

  getStatusColor(status: PartnershipStatus): string {
    switch (status) {
      case PartnershipStatus.Platinum: return 'text-primary font-bold';
      case PartnershipStatus.Gold: return 'text-yellow-400 font-bold';
      case PartnershipStatus.Silver: return 'text-surface-text-muted font-bold';
      default: return 'text-surface-text-muted';
    }
  }
}
