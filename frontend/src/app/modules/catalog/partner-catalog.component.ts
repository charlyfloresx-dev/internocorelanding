import { Component, OnInit, inject, signal, computed, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MasterDataService, Partner, PartnerType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { TranslationService } from '../../core/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { PartnerFormComponent } from '../../shared/components/partner-form.component';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-partner-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            {{ t('catalog.partners.title', 'Socios de Negocio') }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            {{ t('catalog.partners.subtitle', 'Gestión de proveedores, clientes y trazabilidad forense') }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              placeholder="Buscar socio..."
              class="pl-12 pr-6 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64 outline-none"
            >
          </div>

          <div class="flex bg-surface-bg p-1 rounded-2xl border border-surface-border">
            <button 
              (click)="filterType.set('ALL')"
              [class.bg-white]="filterType() === 'ALL'"
              [class.dark:bg-white/10]="filterType() === 'ALL'"
              [class.shadow-sm]="filterType() === 'ALL'"
              class="px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all text-surface-text"
            >TODOS</button>
            <button 
              (click)="filterType.set('SUPPLIER')"
              [class.bg-white]="filterType() === 'SUPPLIER'"
              [class.dark:bg-white/10]="filterType() === 'SUPPLIER'"
              [class.shadow-sm]="filterType() === 'SUPPLIER'"
              class="px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all text-surface-text"
            >PROVEEDORES</button>
            <button 
              (click)="filterType.set('CUSTOMER')"
              [class.bg-white]="filterType() === 'CUSTOMER'"
              [class.dark:bg-white/10]="filterType() === 'CUSTOMER'"
              [class.shadow-sm]="filterType() === 'CUSTOMER'"
              class="px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all text-surface-text"
            >CLIENTES</button>
          </div>

          <button 
            (click)="openAddPartner()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-sm">person_add</mat-icon>
            {{ t('catalog.partners.new', 'Nuevo Socio') }}
          </button>
        </div>
      </div>

      <!-- Control Grid Table -->
      <div class="industrial-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50 border-b border-surface-border">
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">ID</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Código</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Razón Social / Nombre</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">RFC / Tax ID</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Tipo</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Último Movimiento</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (partner of filteredPartners(); track partner.id) {
                <tr class="group hover:bg-primary/5 transition-all duration-300">
                  <td class="px-8 py-6">
                    <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono text-surface-text-muted">
                      #{{ partner.id.slice(-4).toUpperCase() }}
                    </span>
                  </td>
                  <td class="px-8 py-6">
                    <span class="text-xs font-mono font-bold text-surface-text">{{ partner.code }}</span>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-full bg-surface-bg border border-surface-border flex items-center justify-center text-[10px] font-black text-primary">
                        {{ partner.name.slice(0, 2).toUpperCase() }}
                      </div>
                      <span class="text-sm font-black text-surface-text uppercase tracking-tight">{{ partner.name }}</span>
                    </div>
                  </td>
                  <td class="px-8 py-6">
                    <span class="text-xs font-mono text-surface-text-muted">{{ partner.tax_id }}</span>
                  </td>
                  <td class="px-8 py-6">
                    <span 
                      class="px-3 py-1 rounded-lg text-[8px] font-black uppercase tracking-widest border"
                      [ngClass]="{
                        'bg-blue-500/10 text-blue-500 border-blue-500/20': partner.type === 'SUPPLIER',
                        'bg-emerald-500/10 text-emerald-500 border-emerald-500/20': partner.type === 'CUSTOMER',
                        'bg-purple-500/10 text-purple-500 border-purple-500/20': partner.type === 'BOTH'
                      }"
                    >
                      {{ partner.type }}
                    </span>
                  </td>
                  <td class="px-8 py-6">
                    @if (partner.last_transaction_id) {
                      <div class="flex items-center gap-2 group/link cursor-pointer">
                        <mat-icon class="text-[10px] text-primary">link</mat-icon>
                        <span class="text-[10px] font-mono text-primary group-hover/link:underline">
                          {{ partner.last_transaction_id }}
                        </span>
                      </div>
                    } @else {
                      <span class="text-[9px] text-surface-text-muted italic">Sin historial</span>
                    }
                  </td>
                  <td class="px-8 py-6 text-right">
                    <div class="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all">
                      <button class="p-2 hover:bg-surface-bg text-surface-text-muted rounded-xl transition-all" title="Auditoría Forense">
                        <mat-icon class="text-sm">fingerprint</mat-icon>
                      </button>
                      <button class="p-2 hover:bg-surface-bg text-surface-text-muted rounded-xl transition-all">
                        <mat-icon class="text-sm">history</mat-icon>
                      </button>
                      <button 
                        (click)="openEditPartner(partner)"
                        class="p-2 hover:bg-primary/10 text-primary rounded-xl transition-all"
                      >
                        <mat-icon class="text-sm">edit</mat-icon>
                      </button>
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in {
      animation: fadeIn 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class PartnerCatalogComponent implements OnInit, OnDestroy {
  private masterData = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private translation = inject(TranslationService);
  private auth = inject(AuthService);
  private drawerService = inject(SideDrawerService);
  private refreshSub?: Subscription;

  partners = signal<Partner[]>([]);
  loading = signal(false);
  searchQuery = '';
  filterType = signal<'ALL' | 'SUPPLIER' | 'CUSTOMER'>('ALL');

  isAdmin = computed(() => this.auth.roles().includes('admin'));

  filteredPartners = computed(() => {
    let list = this.partners();
    
    if (this.filterType() !== 'ALL') {
      list = list.filter(p => p.type === this.filterType() || p.type === 'BOTH');
    }

    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(p => 
        p.name.toLowerCase().includes(q) || 
        p.code.toLowerCase().includes(q) ||
        p.tax_id.toLowerCase().includes(q)
      );
    }

    return list;
  });

  ngOnInit() {
    this.loadPartners();
    this.refreshSub = this.drawerService.refresh$.subscribe(() => this.loadPartners());
  }

  ngOnDestroy() {
    this.refreshSub?.unsubscribe();
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  loadPartners() {
    this.loading.set(true);
    this.masterData.getPartners().subscribe({
      next: (res) => {
        this.partners.set(res.data);
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading partners:', err);
        this.loading.set(false);
      }
    });
  }

  openAddPartner() {
    const defaultType = this.filterType() === 'ALL' ? PartnerType.BOTH : this.filterType() as unknown as PartnerType;
    this.drawerService.open(PartnerFormComponent, { 
      title: 'Alta de Socio',
      icon: 'person_add'
    }, { defaultType });
  }

  openEditPartner(partner: Partner) {
    this.drawerService.open(PartnerFormComponent, { 
      title: 'Edición de Socio',
      icon: 'edit'
    }, { partner });
  }
}
