import { Component, inject, OnInit, signal, computed, HostListener, ViewChildren, QueryList, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, FormArray } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { Router, ActivatedRoute } from '@angular/router';

import { InventoryService } from '../../core/services/inventory.service';
import { AuthService } from '../../core/services/auth.service';
import { TranslationService } from '../../core/services/translation.service';
import { ToastService } from '../../core/services/toast.service';

import { StatusBadgeComponent } from '../../shared/components/status-badge.component';
import { AuditFooterComponent } from '../../shared/components/audit-footer.component';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';
import { ItemSearchComponent, InventoryItem } from '../../shared/components/item-search.component';
import { ExcelNavigationDirective } from '../../shared/directives/excel-navigation.directive';
import { ConceptType, CreateDocumentCommand } from '../../core/models/api.types';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

interface InternalDocumentItem {
  id: string;
  sku: string;
  name: string;
  variant?: string;
  brand?: string;
  mfgPartNumber?: string;
  quantity: number;
  uom: string;
  uoms: { unit: string; factor: number }[];
  selectedFactor: number;
  weight: number;
  location: string;
  availableStock: number;
  imageUrl?: string;
  isWeightMismatch?: boolean;
}

@Component({
  selector: 'app-inventory-document-editor',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ReactiveFormsModule, 
    MatIconModule, 
    StatusBadgeComponent, 
    AuditFooterComponent, 
    ItemSearchComponent, 
    TranslatePipe,
    ExcelNavigationDirective
  ],
  template: `
    <div class="space-y-8 animate-fade-in p-8 max-w-7xl mx-auto">
      
      <!-- Header Section -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="flex items-center gap-4">
          <div class="w-16 h-16 bg-primary/10 border border-primary/30 rounded-2xl flex items-center justify-center text-primary shadow-[0_0_20px_rgba(0,229,255,0.1)]">
            <mat-icon class="text-3xl">receipt_long</mat-icon>
          </div>
          <div>
            <div class="flex items-center gap-3 mb-1">
              <h1 class="text-3xl font-black text-surface-text tracking-tighter uppercase italic">{{ 'inventory.documents.new' | translate:'Nuevo Movimiento' }}</h1>
              <app-status-badge status="DRAFT" label="Borrador"></app-status-badge>
            </div>
            <p class="text-surface-text-muted font-mono text-[10px] tracking-widest uppercase">
              Registro de flujo de materiales en almacén
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button (click)="cancel()" class="px-6 py-3 bg-surface-bg border border-surface-border text-surface-text-muted rounded-xl font-bold text-[10px] uppercase tracking-widest hover:bg-surface-card transition-all">
            Cancelar
          </button>
          <button 
            [disabled]="!isValid() || service.loading()"
            (click)="confirmMovement()"
            class="btn-primary py-3 px-8 text-[10px] uppercase tracking-[0.2em] relative overflow-hidden group"
            [class.opacity-50]="!isValid() || service.loading()"
          >
            <div class="flex items-center gap-2 relative z-10">
              @if (service.loading()) {
                <mat-icon class="animate-gear-spin text-sm">settings</mat-icon>
                Procesando...
              } @else {
                <mat-icon class="text-sm">check_circle</mat-icon>
                Confirmar Movimiento
              }
            </div>
          </button>
        </div>
      </div>

      <!-- Form Grid -->
      <div class="flex flex-col gap-8">
        
        <!-- Top Section: Document Header -->
        <div class="w-full">
          <div class="industrial-card p-8">
            <h2 class="text-[10px] font-black text-surface-text uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
              <mat-icon class="text-primary text-sm">info</mat-icon>
              Encabezado de Transacción
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <label for="move-type" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2">Tipo de Movimiento</label>
                <div id="move-type" class="grid grid-cols-2 gap-2">
                  <button (click)="moveType.set(ConceptType.Entry)"
                    [ngClass]="{ 'bg-emerald-500/20 border-emerald-500/50 text-emerald-500': moveType() === ConceptType.Entry }"
                    class="py-3 border border-surface-border rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all hover:bg-white/5">
                    Entrada
                  </button>
                  <button (click)="moveType.set(ConceptType.Output)"
                    [ngClass]="{ 'bg-red-500/20 border-red-500/50 text-red-500': moveType() === ConceptType.Output }"
                    class="py-3 border border-surface-border rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all hover:bg-white/5">
                    Salida
                  </button>
                </div>
              </div>

              <div>
                <label class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2">Concepto</label>
                <select [(ngModel)]="conceptId" class="w-full input-industrial text-xs font-bold uppercase tracking-widest cursor-pointer">
                  <option value="" disabled>Seleccione Concepto...</option>
                  @for (c of availableConcepts(); track c.id) {
                    <option [value]="c.id">{{ c.name }}</option>
                  }
                </select>
              </div>

              <!-- External Entity (dynamic) -->
              @if (selectedConcept()?.requires_external_entity) {
                <div class="animate-fade-in">
                  <label class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2 flex items-center gap-1">
                    Proveedor / Cliente <mat-icon class="text-[10px] text-red-500">star</mat-icon>
                  </label>
                  <input 
                    [(ngModel)]="externalReference" required #exRef="ngModel"
                    [class.border-red-500]="exRef.invalid && (exRef.dirty || exRef.touched)"
                    placeholder="Escriba Beneficiario..."
                    class="w-full input-industrial text-xs font-bold uppercase tracking-widest"
                  >
                </div>
              } @else {
                <div class="opacity-50 pointer-events-none">
                  <label class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2">Proveedor / Cliente</label>
                  <select disabled class="w-full input-industrial text-xs font-bold uppercase tracking-widest bg-surface-bg/50">
                    <option value="">N/A</option>
                  </select>
                </div>
              }

              <!-- Warehouse(s) -->
                <!-- Principal / Origin -->
                <div class="w-full">
                  <label class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2 text-ellipsis overflow-hidden whitespace-nowrap">
                    {{ moveType() === ConceptType.Entry ? 'Almacén de Recepción' : (moveType() === ConceptType.Output ? 'Almacén de Despacho' : 'Almacén Origen/Destino') }}
                  </label>
                  <div class="relative group">
                    <mat-icon class="absolute left-3 top-1/2 -translate-y-1/2 text-primary text-sm z-10">business</mat-icon>
                    <select [(ngModel)]="warehouseId" class="w-full input-industrial pl-10 text-[10px] font-bold uppercase tracking-widest appearance-none cursor-pointer">
                      <option value="" disabled>Seleccione Almacén...</option>
                      @for (w of service.warehouses(); track w.id) {
                        <option [value]="w.id">{{ w.name }}</option>
                      }
                    </select>
                    <mat-icon class="absolute right-3 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm pointer-events-none group-hover:text-primary transition-colors">expand_more</mat-icon>
                  </div>
                </div>
            </div>

            <!-- Target (Dynamic row) -->
            @if (selectedConcept()?.requires_target_warehouse) {
              <div class="grid grid-cols-1 mt-6 animate-fade-in">
                <div>
                  <label class="block text-[9px] font-bold text-primary uppercase tracking-widest mb-2 text-ellipsis overflow-hidden whitespace-nowrap">Almacén Destino</label>
                  <div class="relative group">
                    <mat-icon class="absolute left-3 top-1/2 -translate-y-1/2 text-primary text-sm z-10">output</mat-icon>
                    <select [(ngModel)]="targetWarehouseId" required #twRef="ngModel" class="w-full input-industrial border-primary/50 bg-primary/5 shadow-inner pl-10 text-[10px] font-bold uppercase tracking-widest appearance-none cursor-pointer pb-2" [class.border-red-500]="twRef.invalid && (twRef.dirty || twRef.touched)">
                      <option value="" disabled>Seleccione Destino...</option>
                      @for (w of service.warehouses(); track w.id) {
                        @if (w.id !== warehouseId) {
                          <option [value]="w.id">{{ w.name }}</option>
                        }
                      }
                    </select>
                    <mat-icon class="absolute right-3 top-1/2 -translate-y-1/2 text-surface-text-muted text-sm pointer-events-none group-hover:text-primary transition-colors">expand_more</mat-icon>
                  </div>
                </div>
              </div>
            }

            <div class="mt-6">
              <label class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest mb-2">Notas / Referencia</label>
              <textarea 
                [(ngModel)]="notes"
                class="w-full input-industrial text-xs h-16 resize-none" 
                placeholder="Ej. Factura #4567, Orden de Compra..."
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Bottom Section: Item Table -->
        <div class="w-full space-y-6">
          <div class="industrial-card">
            <div class="p-6 border-b border-surface-border flex items-center justify-between bg-surface-bg/30 rounded-t-2xl overflow-hidden">
              <h2 class="text-[10px] font-black text-surface-text uppercase tracking-[0.2em] flex items-center gap-2">
                Partidas del Documento
              </h2>
              <button 
                (click)="addItem()"
                class="flex items-center gap-2 px-4 py-2 bg-primary/10 border border-primary/30 text-primary rounded-lg text-[9px] font-black uppercase tracking-widest hover:bg-primary hover:text-black transition-all group active:scale-95"
              >
                <mat-icon class="text-sm">add</mat-icon>
                Agregar SKU
                <span class="ml-2 px-1.5 py-0.5 bg-black/10 rounded text-[7px] opacity-80 group-hover:opacity-100 transition-opacity">Alt + A</span>
              </button>
            </div>

            <div class="overflow-x-auto min-h-[250px] custom-scrollbar" icExcelNav (smartPaste)="onSmartPaste($event)" (lastCellTab)="addItem()">
              <table class="w-full text-left border-collapse" [formGroup]="documentForm">
                <thead>
                  <tr class="bg-surface-bg/50">
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest w-[300px]">Material / SKU</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Localidad</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right">Cantidad</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest">UOM</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-right">Peso Masa (Kg)</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-widest text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody formArrayName="items" class="divide-y divide-surface-border">
                  @for (itemGroup of itemControls; track $index; let i = $index) {
                    <tr [formGroupName]="i" class="hover:bg-surface-bg/30 transition-colors group relative" [class.ic-cell-editing]="focusedRow() === i">
                      <td class="px-6 py-4">
                         <app-item-search 
                            [attr.data-row]="i" [attr.data-col]="0"
                            (itemSelected)="onItemSelected(i, $event)"
                            (focus)="focusedRow.set(i)">
                         </app-item-search>
                         @if (itemGroup.get('sku')?.value) {
                           <div class="mt-2 flex flex-col animate-fade-in">
                             <span class="text-[10px] font-black text-surface-text uppercase tracking-tight">{{ itemGroup.get('name')?.value }}</span>
                             <div class="flex items-center gap-2 mt-1 opacity-80">
                               <span class="text-[8px] text-primary font-bold uppercase font-mono">{{ itemGroup.get('sku')?.value }}</span>
                               @if (itemGroup.get('variant')?.value) {
                                 <div class="w-0.5 h-0.5 bg-surface-text-muted rounded-full"></div>
                                 <span class="text-[8px] text-surface-text-muted italic">{{ itemGroup.get('variant')?.value }}</span>
                               }
                             </div>
                           </div>
                         }
                      </td>
                      <td class="px-6 py-4">
                        <input formControlName="location" [attr.data-row]="i" [attr.data-col]="1" class="w-32 input-industrial text-[10px] font-bold px-2 py-1.5 uppercase text-center bg-transparent border-none">
                      </td>
                      <td class="px-6 py-4 text-right">
                        <input #qtyInput type="number" formControlName="quantity" [attr.data-row]="i" [attr.data-col]="2" class="w-20 input-industrial text-[11px] font-black text-right px-2 py-1.5 bg-transparent">
                      </td>
                      <td class="px-6 py-4">
                        <select formControlName="uom" [attr.data-row]="i" [attr.data-col]="3" class="w-20 input-industrial text-[10px] font-bold uppercase px-2 py-1.5 cursor-pointer appearance-none bg-transparent">
                           @for (u of (itemUoms[i] || []); track u.unit) {
                            <option [value]="u.unit">{{ u.unit }}</option>
                          }
                        </select>
                      </td>
                      <td class="px-6 py-4 text-right relative group/weight">
                        <input type="number" formControlName="weight" [attr.data-row]="i" [attr.data-col]="4"
                               [class.ic-invalid-weight]="itemGroup.get('isWeightMismatch')?.value"
                               class="w-24 input-industrial text-[11px] font-black text-right px-2 py-1.5 bg-transparent transition-all">
                        
                        <!-- Forensic Weight Tooltip -->
                        <div class="absolute right-0 bottom-full mb-3 hidden group-hover/weight:block z-[60] pointer-events-none animate-in fade-in slide-in-from-bottom-2 duration-300">
                           <div class="bg-slate-950/90 backdrop-blur-xl border border-ic-cyan/50 shadow-[0_0_30px_rgba(0,229,255,0.3)] p-3 rounded-xl min-w-[200px]">
                              <div class="flex items-center gap-3 mb-2 border-b border-ic-cyan/20 pb-2">
                                <mat-icon class="text-ic-cyan text-sm">calculate</mat-icon>
                                <span class="text-[10px] font-black text-white uppercase tracking-widest">Validación Forense</span>
                              </div>
                              <div class="space-y-1">
                                <div class="flex justify-between text-[8px] font-bold text-surface-text-muted uppercase">
                                  <span>Cálculo Esperado:</span>
                                  <span class="text-ic-cyan">{{ itemGroup.get('quantity')?.value }} × {{ itemGroup.get('uomFactor')?.value }}</span>
                                </div>
                                <div class="flex justify-between text-[11px] font-black text-ic-cyan font-mono">
                                  <span>Total:</span>
                                  <span>{{ (itemGroup.get('quantity')?.value * itemGroup.get('uomFactor')?.value).toFixed(4) }} Kg</span>
                                </div>
                              </div>
                           </div>
                           <!-- Neon Arrow -->
                           <div class="absolute left-1/2 -translate-x-1/2 top-full border-[6px] border-transparent border-t-ic-cyan/50"></div>
                        </div>
                      </td>
                      <td class="px-6 py-4 text-center">
                         <button (click)="removeItem(i)" class="p-2 text-red-500/60 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all">
                           <mat-icon class="text-sm">delete</mat-icon>
                         </button>
                      </td>
                    </tr>
                  }
                  @if (itemControls.length === 0) {
                    <tr>
                      <td colspan="6" class="py-16 text-center">
                         <div class="flex flex-col items-center opacity-30 text-surface-text-muted">
                           <mat-icon class="text-4xl mb-2">inventory_2</mat-icon>
                           <span class="text-[9px] font-black uppercase tracking-[0.3em]">No hay SKUs agregados</span>
                         </div>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
            
            <div class="p-6 bg-surface-bg/50 border-t border-surface-border flex justify-end gap-10">
               <div class="flex flex-col items-end">
                  <span class="text-[8px] text-surface-text-muted font-bold uppercase tracking-[0.2em] mb-1">Masa Bruta Total</span>
                  <span class="text-2xl font-black text-primary italic tracking-tighter">{{ totalWeight() | number:'1.2-2' }} <span class="text-xs uppercase ml-1">Kg</span></span>
               </div>
               <div class="flex flex-col items-end border-l border-surface-border pl-10">
                  <span class="text-[8px] text-surface-text-muted font-bold uppercase tracking-[0.2em] mb-1">Total Unidades</span>
                  <span class="text-2xl font-black text-surface-text italic tracking-tighter">{{ totalItems() | number }} <span class="text-xs uppercase ml-1">SKU</span></span>
               </div>
            </div>
          </div>
          <app-audit-footer [createdBy]="auth.userFullName()" [createdAt]="today"></app-audit-footer>
        </div>
      </div>
    </div>

    <!-- Success Portal & Print (High Fidelity Overlay) -->
    @if (confirmedDoc(); as doc) {
      <div class="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-slate-950/90 backdrop-blur-2xl animate-fade-in no-print">
        <div class="industrial-card max-w-md w-full p-10 text-center space-y-8 shadow-[0_0_100px_rgba(0,229,255,0.15)] border border-primary/20 rounded-[2rem]">
          <div class="flex flex-col items-center">
            <div class="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center text-primary mb-6 animate-bounce shadow-[0_0_30px_rgba(0,229,255,0.3)] border border-primary/30">
              <mat-icon class="text-4xl">check_circle</mat-icon>
            </div>
            <h2 class="text-2xl font-black text-surface-text uppercase tracking-tighter italic mb-2">¡Movimiento Registrado!</h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-[0.3em]">El documento ha sido persistido en el ledger</p>
          </div>

          <div class="p-6 bg-surface-bg/50 rounded-[2rem] border border-surface-border space-y-6">
             <div class="bg-white p-3 rounded-2xl inline-block shadow-lg">
               <img [src]="'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=' + (doc.folio || doc.id)" class="w-28 h-28" referrerpolicy="no-referrer" />
             </div>
             <div>
               <span class="text-[8px] text-surface-text-muted font-black uppercase tracking-widest block mb-1">Folio del Registro</span>
               <span class="text-2xl font-mono font-black text-primary tracking-tighter">{{ doc.folio || doc.id || 'PENDING...' }}</span>
             </div>
          </div>

          <div class="grid grid-cols-1 gap-3">
             <button (click)="print()" class="w-full py-4 bg-primary text-black rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] flex items-center justify-center gap-3 active:scale-95 shadow-lg shadow-primary/20 transition-all hover:brightness-110">
               <mat-icon>print</mat-icon> Imprimir Certificado
             </button>
             <button (click)="resetAndGoBack()" class="w-full py-4 bg-surface-bg border border-surface-border text-surface-text rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:bg-surface-card transition-all active:scale-95">
               Finalizar y Volver
             </button>
          </div>
        </div>
      </div>
    }
  `,
  styles: [`
    .ic-cell-editing {
      background: linear-gradient(90deg, rgba(0, 229, 255, 0.05) 0%, transparent 100%);
      border-left: 2px solid var(--primary);
    }
    .input-industrial:focus {
      outline: none;
      box-shadow: 0 0 15px rgba(0, 229, 255, 0.1);
    }
    .ic-invalid-weight {
      border-color: rgb(239 68 68) !important;
      box-shadow: 0 0 10px rgba(239,68,68,0.3);
    }
  `]
})
export class InventoryDocumentEditorComponent implements OnInit {
  public service = inject(InventoryService);
  public auth = inject(AuthService);
  public ts = inject(TranslationService);
  private toast = inject(ToastService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);

  @ViewChildren('qtyInput') qtyInputs!: QueryList<ElementRef<HTMLInputElement>>;

  documentForm: FormGroup;
  moveType = signal<ConceptType>(ConceptType.Entry);
  conceptId = '';
  warehouseId = '';
  targetWarehouseId = '';
  externalReference = '';
  notes = '';
  confirmedDoc = signal<any | null>(null);
  today = new Date();
  isEdit = false;
  
  focusedRow = signal<number | null>(null);
  itemUoms: { [key: number]: { unit: string; factor: number }[] } = {};

  public ConceptType = ConceptType;

  constructor() {
    this.documentForm = this.fb.group({
      items: this.fb.array([])
    });

    // Reactive Weight Validation Stream
    const WEIGHT_TOLERANCE = 0.0001;
    this.documentForm.get('items')?.valueChanges.pipe(
      debounceTime(50),
      distinctUntilChanged((prev, curr) => JSON.stringify(prev) === JSON.stringify(curr))
    ).subscribe(rows => {
      rows.forEach((row: any, index: number) => {
        const expected = row.quantity * row.uomFactor;
        const mismatch = Math.abs(expected - row.weight) > WEIGHT_TOLERANCE;

        // Update mismatch flag silently if changed
        const control = this.itemsArray.at(index);
        if (control.get('isWeightMismatch')?.value !== mismatch) {
          control.get('isWeightMismatch')?.patchValue(mismatch, { emitEvent: false });
        }
      });
    });
  }

  get itemsArray() {
    return this.documentForm.get('items') as FormArray;
  }

  get itemControls() {
    return this.itemsArray.controls as FormGroup[];
  }

  availableConcepts = computed(() => {
    return this.service.concepts().filter(c => c.type === this.moveType());
  });

  selectedConcept = computed(() => {
    return this.availableConcepts().find(c => c.id === this.conceptId) || null;
  });

  totalItems = computed(() => {
    return this.itemControls.reduce((acc, ctrl) => acc + (ctrl.get('quantity')?.value || 0), 0);
  });

  totalWeight = computed(() => {
    return this.itemControls.reduce((acc, ctrl) => acc + (ctrl.get('weight')?.value || 0), 0);
  });

  isValid = computed(() => {
    if (this.itemControls.length === 0 || !this.conceptId || !this.warehouseId) return false;
    if (this.totalWeight() <= 0) return false;

    const concept = this.selectedConcept();
    if (concept) {
      if ((concept as any).requires_external_entity && !this.externalReference.trim()) return false;
      if ((concept as any).requires_target_warehouse) {
        if (!this.targetWarehouseId) return false;
        if (this.targetWarehouseId === this.warehouseId) return false;
      }
    }

    // Validate rows (no mismatches and quantities > 0)
    for (const ctrl of this.itemControls) {
      if (ctrl.get('quantity')?.value <= 0) return false;
      if (ctrl.get('isWeightMismatch')?.value) return false;
      if (!ctrl.get('sku')?.value) return false;
    }

    return true;
  });

  ngOnInit() {
    this.service.loadCatalogs();
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.isEdit = true;
    }

    if (this.itemControls.length === 0) {
      this.addItem();
    }
  }

  @HostListener('window:keydown', ['$event'])
  handleGlobalKeydown(event: KeyboardEvent) {
    if (event.altKey && event.key.toLowerCase() === 'a') {
      event.preventDefault();
      this.addItem();
    }
  }

  addItem(data?: Partial<InternalDocumentItem>) {
    const itemGroup = this.fb.group({
      id: [data?.id || Math.random().toString(36).substring(2, 9)],
      sku: [data?.sku || ''],
      name: [data?.name || ''],
      variant: [data?.variant || ''],
      brand: [data?.brand || ''],
      quantity: [data?.quantity || 1],
      uom: [data?.uom || 'PZ'],
      uomFactor: [data?.selectedFactor || 1],
      weight: [data?.weight || (data?.quantity || 1) * (data?.selectedFactor || 1)],
      location: [data?.location || 'TIJ-ALMACEN-01'],
      isWeightMismatch: [false]
    });

    const index = this.itemsArray.length;
    this.itemUoms[index] = data?.uoms || [{ unit: 'PZ', factor: 1 }];
    this.itemsArray.push(itemGroup);
  }

  removeItem(index: number) {
    this.itemsArray.removeAt(index);
    // Re-map UOMs (simplified for now)
    delete this.itemUoms[index];
  }

  onItemSelected(index: number, item: InventoryItem) {
    const row = this.itemsArray.at(index);
    row.patchValue({
      sku: item.sku,
      name: item.name,
      variant: item.variant,
      brand: item.brand,
      availableStock: item.available
    });

    if (item.conversions && item.conversions.length > 0) {
      this.itemUoms[index] = item.conversions;
      const uom = item.unit || item.conversions[0].unit;
      const factor = item.conversions.find((c: any) => c.unit === uom)?.factor || 1;
      row.patchValue({ uom, uomFactor: factor, weight: (row.get('quantity')?.value || 1) * factor });
    } else {
      const uom = item.unit || 'PZ';
      this.itemUoms[index] = [{ unit: uom, factor: 1 }];
      row.patchValue({ uom, uomFactor: 1, weight: row.get('quantity')?.value || 1 });
    }

    // Auto-focus jump to quantity
    setTimeout(() => {
      const inputs = this.qtyInputs.toArray();
      if (inputs[index]) {
        inputs[index].nativeElement.focus();
        inputs[index].nativeElement.select();
      }
    }, 50);
  }

  onSmartPaste(data: string[][]) {
    // Parse CSV/TSV data and bulk add rows
    data.forEach(rowCells => {
      if (rowCells.length >= 2) {
        const sku = rowCells[0].trim();
        const qty = parseFloat(rowCells[1]) || 1;
        // In a real app, we'd look up the SKU here. For now, we mock it.
        this.addItem({ sku, quantity: qty });
      }
    });
    this.toast.info(`Cargadas ${data.length} partidas desde el portapapeles`, 'Smart-Paste');
  }

  confirmMovement() {
    if (this.itemControls.length === 0 || !this.conceptId) {
      this.toast.error('Complete todos los campos requeridos', 'Validación');
      return;
    }

    const movements = this.itemControls.map(ctrl => ({
      productId: ctrl.get('id')?.value,
      sku: ctrl.get('sku')?.value,
      quantity: ctrl.get('quantity')?.value,
      unitPrice: 0
    }));

    const command: CreateDocumentCommand = {
      conceptId: this.conceptId,
      warehouseId: this.warehouseId,
      description: this.notes,
      reference: this.externalReference,
      deliveryDate: new Date().toISOString(),
      movements: movements as any
    };

    this.service.createDocument(command).then((res) => {
      if (res) {
        this.toast.success('Documento confirmado en el ledger', 'Sincronizado');
        this.confirmedDoc.set({ id: 'doc-mock', folio: 'MOCK-FOL-' + Math.floor(Math.random() * 1000) });
      } else {
        this.toast.error('Error al sincronizar con el backend', 'Falla Crítica');
      }
    });
  }

  print() {
    window.print();
  }

  resetAndGoBack() {
    this.router.navigate(['/inventory/documents']);
  }

  cancel() {
    this.router.navigate(['/inventory/documents']);
  }
}
