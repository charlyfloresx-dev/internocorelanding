import { Component, OnInit, inject, signal, computed, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { MasterDataService, Concept } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { TranslationService } from '../../core/services/translation.service';
import { AuthService } from '../../core/services/auth.service';
import { ConceptModalComponent } from '../../shared/components/concept-modal.component';

@Component({
  selector: 'app-concept-catalog',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule, ConceptModalComponent],
  template: `
    <div class="p-8 space-y-8 animate-fade-in">
      <!-- Header -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <h1 class="text-4xl font-black text-surface-text uppercase tracking-tighter italic leading-none">
            {{ t('catalog.concepts.title', 'Conceptos de Movimiento') }}
          </h1>
          <p class="text-surface-text-muted font-mono text-[10px] uppercase tracking-[0.3em]">
            {{ t('catalog.concepts.subtitle', 'Configuración de lógica transaccional y smart forms') }}
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-4">
          <div class="relative group">
            <mat-icon class="absolute left-4 top-1/2 -translate-y-1/2 text-surface-text-muted group-focus-within:text-primary transition-colors">search</mat-icon>
            <input 
              type="text" 
              [(ngModel)]="searchQuery"
              placeholder="Buscar concepto..."
              class="pl-12 pr-6 py-3 bg-surface-bg border border-surface-border rounded-2xl text-xs font-mono focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all w-64 outline-none"
            >
          </div>

          <button 
            (click)="loadConcepts()"
            class="p-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-2xl transition-all"
          >
            <mat-icon class="text-sm">refresh</mat-icon>
          </button>

          <button 
            (click)="openAddModal()"
            class="flex items-center gap-3 px-8 py-3 bg-primary text-white dark:text-slate-950 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary/20"
          >
            <mat-icon class="text-sm">add</mat-icon>
            {{ t('catalog.concepts.new', 'Nuevo Concepto') }}
          </button>
        </div>
      </div>

      <!-- Modal Wrapper -->
      @if (isModalVisible()) {
        <app-concept-modal #conceptModal (saved)="onConceptSaved($event)"></app-concept-modal>
      }

      <!-- Control Grid Table -->
      <div class="industrial-card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-bg/50 border-b border-surface-border">
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">ID</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Código</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Nombre</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted text-center">Dirección</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Tipo Operación</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Smart Logic</th>
                <th class="px-8 py-6 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted text-right">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-border">
              @for (concept of filteredConcepts(); track concept.id) {
                <tr class="group hover:bg-primary/5 transition-all duration-300">
                  <td class="px-8 py-6">
                    <span class="px-3 py-1 bg-surface-bg border border-surface-border rounded-full text-[9px] font-mono text-surface-text-muted">
                      #{{ concept.id.slice(-4).toUpperCase() }}
                    </span>
                  </td>
                  <td class="px-8 py-6">
                    <span class="text-xs font-mono font-bold text-surface-text">{{ concept.code }}</span>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex items-center gap-3">
                      @if (masterData.isGlobal(concept)) {
                        <mat-icon class="text-[10px] text-primary" title="Global">public</mat-icon>
                      }
                      <span class="text-sm font-black text-surface-text uppercase tracking-tight">{{ concept.name }}</span>
                    </div>
                  </td>
                  <td class="px-8 py-6 text-center">
                    <span 
                      class="px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest"
                      [ngClass]="{
                        'bg-emerald-500/10 text-emerald-500': concept.type === 'ENTRADA' || concept.type === 'IN',
                        'bg-rose-500/10 text-rose-500': concept.type === 'SALIDA' || concept.type === 'OUT',
                        'bg-cyan-500/10 text-cyan-400': concept.type === 'TRASPASO'
                      }"
                    >
                      {{ concept.type === 'ENTRADA' || concept.type === 'IN' ? 'Entrada' : 
                         concept.type === 'SALIDA' || concept.type === 'OUT' ? 'Salida' : 'Traspaso' }}
                    </span>
                  </td>
                  <td class="px-8 py-6">
                    <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">{{ concept.operation_type }}</span>
                  </td>
                  <td class="px-8 py-6">
                    <div class="flex gap-2">
                      @if (concept.requires_target_warehouse) {
                        <span class="p-1.5 bg-blue-500/10 text-blue-500 rounded-lg" title="Requiere Almacén Destino">
                          <mat-icon class="text-xs">swap_horiz</mat-icon>
                        </span>
                      }
                      @if (concept.requires_external_entity) {
                        <span class="p-1.5 bg-amber-500/10 text-amber-500 rounded-lg" title="Requiere Entidad Externa">
                          <mat-icon class="text-xs">business</mat-icon>
                        </span>
                      }
                      @if (!concept.requires_target_warehouse && !concept.requires_external_entity) {
                        <span class="text-[9px] text-surface-text-muted italic">Simple</span>
                      }
                    </div>
                  </td>
                  <td class="px-8 py-6 text-right">
                    <div class="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all">
                      <button class="p-2 hover:bg-surface-bg border border-transparent hover:border-surface-border text-surface-text-muted rounded-xl transition-all">
                        <mat-icon class="text-sm">history</mat-icon>
                      </button>
                      <button class="p-2 hover:bg-surface-bg border border-transparent hover:border-surface-border text-surface-text-muted rounded-xl transition-all">
                        <mat-icon class="text-sm">content_copy</mat-icon>
                      </button>
                      @if (masterData.isGlobal(concept) && !isAdmin()) {
                        <button class="p-2 text-surface-text-muted/30 cursor-not-allowed">
                          <mat-icon class="text-sm">lock</mat-icon>
                        </button>
                      } @else {
                        <button (click)="onEditConcept(concept)" class="p-2 hover:bg-primary/10 text-primary rounded-xl transition-all">
                          <mat-icon class="text-sm">edit</mat-icon>
                        </button>
                      }
                    </div>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>

      <!-- Smart Form Preview Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div class="industrial-card p-10 space-y-8">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 bg-primary/20 rounded-2xl flex items-center justify-center text-primary">
              <mat-icon>psychology</mat-icon>
            </div>
            <div>
              <h2 class="text-xl font-black text-surface-text uppercase tracking-tight italic">Smart Form Preview</h2>
              <p class="text-[10px] text-surface-text-muted font-mono uppercase tracking-widest">Simulación de lógica dinámica</p>
            </div>
          </div>

          <div class="space-y-6">
            <div class="space-y-2">
              <label for="preview-concept-select" class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest">Seleccionar Concepto para Probar</label>
              <select 
                id="preview-concept-select"
                [(ngModel)]="previewConceptId"
                class="w-full bg-surface-bg border border-surface-border rounded-2xl py-4 px-6 text-sm font-bold text-surface-text outline-none focus:border-primary transition-all appearance-none"
              >
                @for (c of concepts(); track c.id) {
                  <option [value]="c.id">{{ c.name }} ({{ c.operation_type }})</option>
                }
              </select>
            </div>

            @if (activePreviewConcept(); as cp) {
              <div class="p-6 bg-surface-bg/50 rounded-[2rem] border border-surface-border space-y-6 animate-fade-in">
                <div class="flex items-center gap-3">
                  <div class="w-2 h-2 rounded-full bg-primary animate-pulse"></div>
                  <span class="text-[10px] font-black text-primary uppercase tracking-widest">Formulario Dinámico Generado</span>
                </div>

                <div class="grid grid-cols-1 gap-4">
                  <div class="p-4 bg-surface-bg border border-surface-border rounded-xl opacity-50">
                    <span class="text-[9px] text-surface-text-muted uppercase font-black">Almacén Origen</span>
                    <p class="text-xs text-surface-text font-bold">WH-TIJ (Tijuana Central)</p>
                  </div>

                  @if (cp.requires_target_warehouse) {
                    <div class="p-4 bg-primary/10 rounded-xl border border-primary/20 animate-in slide-in-from-top-2">
                      <span class="text-[9px] text-primary uppercase font-black">Almacén Destino (Requerido)</span>
                      <select class="w-full bg-transparent border-none text-xs text-surface-text font-bold outline-none mt-1">
                        <option>Seleccione destino...</option>
                        <option>WH-MEX (CDMX Hub)</option>
                        <option>WH-MTY (Monterrey)</option>
                      </select>
                    </div>
                  }

                  @if (cp.requires_external_entity) {
                    <div class="p-4 bg-amber-500/10 rounded-xl border border-amber-500/20 animate-in slide-in-from-top-2">
                      <span class="text-[9px] text-amber-500 uppercase font-black">
                        {{ cp.type === 'IN' ? 'Proveedor' : 'Cliente' }} (Requerido)
                      </span>
                      <div class="flex items-center gap-2 mt-1">
                        <mat-icon class="text-sm text-amber-500/50">search</mat-icon>
                        <input type="text" placeholder="Buscar entidad..." class="bg-transparent border-none text-xs text-surface-text font-bold outline-none w-full">
                      </div>
                    </div>
                  }

                  <div class="p-4 bg-surface-bg border border-surface-border rounded-xl">
                    <span class="text-[9px] text-surface-text-muted uppercase font-black">Notas / Referencia</span>
                    <textarea class="w-full bg-transparent border-none text-xs text-surface-text font-bold outline-none mt-1 resize-none" rows="2" placeholder="Ingrese notas..."></textarea>
                  </div>
                </div>
              </div>
            }
          </div>
        </div>

        <div class="industrial-card p-10 flex flex-col justify-center items-center text-center space-y-6">
          <div class="w-24 h-24 bg-surface-bg border border-surface-border rounded-full flex items-center justify-center text-surface-text-muted/20">
            <mat-icon class="text-5xl">settings_suggest</mat-icon>
          </div>
          <div class="space-y-2">
            <h3 class="text-2xl font-black text-surface-text uppercase tracking-tight italic">Lógica de Negocio</h3>
            <p class="text-sm text-surface-text-muted max-w-xs mx-auto">
              Los conceptos definen el comportamiento de cada transacción en el sistema, habilitando campos condicionales y validaciones forenses.
            </p>
          </div>
          <div class="flex flex-wrap justify-center gap-2">
            <span class="px-4 py-2 bg-surface-bg border border-surface-border rounded-xl text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Traspasos</span>
            <span class="px-4 py-2 bg-surface-bg border border-surface-border rounded-xl text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Ajustes</span>
            <span class="px-4 py-2 bg-surface-bg border border-surface-border rounded-xl text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Compras</span>
            <span class="px-4 py-2 bg-surface-bg border border-surface-border rounded-xl text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Ventas</span>
          </div>
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
export class ConceptCatalogComponent implements OnInit {
  masterData = inject(MasterDataService);
  notifications = inject(NotificationService);
  translation = inject(TranslationService);
  auth = inject(AuthService);

  concepts = signal<Concept[]>([]);
  loading = signal(false);
  searchQuery = '';
  previewConceptId = '';
  isModalVisible = signal(false);

  @ViewChild('conceptModal') conceptModal!: ConceptModalComponent;

  isAdmin = computed(() => this.auth.roles().includes('admin'));

  filteredConcepts = computed(() => {
    let list = this.concepts();
    if (this.searchQuery) {
      const q = this.searchQuery.toLowerCase();
      list = list.filter(c => 
        c.name.toLowerCase().includes(q) || 
        c.code.toLowerCase().includes(q)
      );
    }
    return list;
  });

  activePreviewConcept = computed(() => 
    this.concepts().find(c => c.id === this.previewConceptId)
  );

  ngOnInit() {
    this.loadConcepts();
  }

  t(key: string, fallback: string): string {
    return this.translation.translate(key, fallback);
  }

  loadConcepts() {
    this.loading.set(true);
    this.masterData.getConcepts().subscribe({
      next: (res) => {
        this.concepts.set(res.data);
        if (res.data.length > 0) this.previewConceptId = res.data[0].id;
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error loading concepts:', err);
        const mock: Concept[] = [
          { id: 'c1', name: 'Compra de Material', code: 'COM-MAT', type: 'IN', operation_type: 'ENTRADA', requires_external_entity: true, requires_target_warehouse: false, company_id: null },
          { id: 'c2', name: 'Traspaso entre Almacenes', code: 'TRS-INT', type: 'OUT', operation_type: 'TRASPASO', requires_external_entity: false, requires_target_warehouse: true, company_id: null },
          { id: 'c3', name: 'Ajuste por Inventario', code: 'AJU-INV', type: 'OUT', operation_type: 'AJUSTE', requires_external_entity: false, requires_target_warehouse: false, company_id: null },
          { id: 'c4', name: 'Devolución de Cliente', code: 'DEV-CLI', type: 'IN', operation_type: 'ENTRADA', requires_external_entity: true, requires_target_warehouse: false, company_id: null }
        ];
        this.concepts.set(mock);
        this.previewConceptId = mock[0].id;
        this.loading.set(false);
      }
    });
  }

  openAddModal() {
    this.isModalVisible.set(true);
    setTimeout(() => this.conceptModal.open());
  }

  onEditConcept(concept: Concept) {
    this.isModalVisible.set(true);
    setTimeout(() => this.conceptModal.open(concept));
  }

  onConceptSaved(concept: Concept) {
    this.loadConcepts();
    this.isModalVisible.set(false);
  }
}
