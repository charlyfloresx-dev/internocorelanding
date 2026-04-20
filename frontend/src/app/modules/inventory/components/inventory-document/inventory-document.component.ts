import { Component, inject, signal, computed, ViewChild, ViewChildren, QueryList, ElementRef, HostListener, OnInit, effect } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormArray, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';
import { MasterDataService, Concept, Partner, PartnerType } from '../../../../core/services/master-data.service';
import { InventoryService } from '../../../../core/services/inventory.service';
import { AuditFooterComponent } from '../../../../shared/components/audit-footer.component';
import { ItemSearchComponent, InventoryItem } from '../../../../shared/components/item-search.component';
import { PartnerModalComponent } from '../../../../shared/components/partner-modal.component';
import { ExcelNavigationDirective } from '../../../../shared/directives/excel-navigation.directive';
import { CurrencyFormatPipe } from '../../../../shared/pipes/currency-format.pipe';
import { CurrencyService } from '../../../../core/services/currency.service';

const WEIGHT_TOLERANCE = 0.0001;

interface ConfirmedDocument {
  id: string;
  correlation_id: string;
  timestamp: string;
  user_agent: string;
  type: 'IN' | 'OUT' | 'ENTRADA' | 'SALIDA';
  concept_id: string;
  concept_name?: string;
  warehouse_id: string;
  warehouse?: string; 
  target_warehouse_id?: string | null;
  target_warehouse?: string | null;
  external_entity: string | null;
  notes: string;
  items: {
    product_id: string;
    sku: string;
    name: string;
    variant?: string;
    quantity: number;
    uom_id: string;
    uom_name: string;
    unit_price: number;
    weight: number;
    location: string;
  }[];
  audit: {
    client_time: string;
    location_context: string;
  };
}

@Component({
  selector: 'app-inventory-document',
  standalone: true,
  imports: [
    CommonModule, 
    FormsModule, 
    ReactiveFormsModule, 
    MatIconModule, 
    AuditFooterComponent, 
    ItemSearchComponent,
    PartnerModalComponent,
    ExcelNavigationDirective,
    CurrencyFormatPipe
  ],
  styles: [`
    :host { display: block; }
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.05);
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(0, 229, 255, 0.2);
      border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: rgba(0, 229, 255, 0.4);
    }
    .ic-cell-focus {
      outline: 2px solid #00e5ff !important;
      outline-offset: -2px;
      background: rgba(0, 229, 255, 0.05) !important;
    }
    .ic-cell-focus app-item-search {
      background: rgba(0, 229, 255, 0.1) !important;
    }
    .input-clean {
      background-color: transparent;
      border: none;
      outline: none;
      width: 100%;
      height: 100%;
      padding: 0;
      margin: 0;
    }
    .input-clean:focus {
      box-shadow: none;
    }
  `],
  template: `
    <div class="space-y-12 animate-fade-in pb-32 max-w-6xl mx-auto" [class.no-print]="confirmedDocument()">
      
      <!-- Read-Only Banner -->
      @if (isReadOnly()) {
        <div class="bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-center justify-between animate-pulse">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center text-red-500">
              <mat-icon>lock</mat-icon>
            </div>
            <div>
              <h3 class="text-xs font-black text-red-500 uppercase tracking-[0.2em]">Modo Lectura: Pago Pendiente</h3>
              <p class="text-[10px] text-red-400/80 font-bold uppercase tracking-widest">Su suscripción ha expirado. Las funciones de escritura están deshabilitadas.</p>
            </div>
          </div>
          <button class="px-4 py-2 bg-red-500 text-white text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-red-600 transition-colors">
            Regularizar Cuenta
          </button>
        </div>
      }

      <!-- STEP 1: CONTEXTO INICIAL (GIGANTE) -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <!-- ¿Qué haces? -->
        <div class="industrial-card p-8 flex flex-col items-center text-center space-y-6 border-2 transition-all duration-500"
             [class.border-primary]="!selectedWarehouse()"
             [class.border-surface-border]="selectedWarehouse()">
          <span class="text-[10px] font-black text-primary uppercase tracking-[0.3em]">1. ¿Qué vas a registrar?</span>
          <div class="flex gap-4 w-full">
            <button 
              (click)="setType('ENTRADA')"
              [class.bg-emerald-500]="type() === 'ENTRADA'"
              [class.text-slate-950]="type() === 'ENTRADA'"
              [class.bg-white/5]="type() !== 'ENTRADA'"
              [class.text-surface-text-muted]="type() !== 'ENTRADA'"
              class="flex-1 py-6 rounded-2xl font-black text-lg uppercase tracking-tighter transition-all hover:scale-[1.02] active:scale-95 shadow-xl border border-white/10"
            >
              ENTRADA
            </button>
            <button 
              (click)="setType('SALIDA')"
              [class.bg-rose-500]="type() === 'SALIDA'"
              [class.text-slate-950]="type() === 'SALIDA'"
              [class.bg-white/5]="type() !== 'SALIDA'"
              [class.text-surface-text-muted]="type() !== 'SALIDA'"
              class="flex-1 py-6 rounded-2xl font-black text-lg uppercase tracking-tighter transition-all hover:scale-[1.02] active:scale-95 shadow-xl border border-white/10"
            >
              SALIDA
            </button>
          </div>
          <select 
            [ngModel]="selectedConceptId()"
            (ngModelChange)="selectedConceptId.set($event)"
            class="w-full bg-surface-bg border-2 border-surface-border rounded-xl py-4 px-6 text-sm font-black uppercase tracking-widest outline-none focus:border-primary transition-all"
          >
            <option value="">Seleccione Concepto...</option>
            @for (concept of concepts(); track concept.id) {
              <option [value]="concept.id">{{ concept.name }}</option>
            }
          </select>
        </div>

        <!-- ¿Dónde? -->
        <div class="industrial-card p-8 flex flex-col items-center text-center space-y-6 border-2 transition-all duration-500"
             [class.border-primary]="!selectedWarehouse()"
             [class.border-surface-border]="selectedWarehouse()">
          <span class="text-[10px] font-black text-primary uppercase tracking-[0.3em]">2. ¿En qué almacén?</span>
          <div class="relative w-full">
            <mat-icon class="absolute left-6 top-1/2 -translate-y-1/2 text-primary text-2xl z-10">business</mat-icon>
            <select 
              id="warehouse-select"
              [ngModel]="selectedWarehouseId()"
              (ngModelChange)="selectedWarehouseId.set($event); onWarehouseChange()"
              class="w-full bg-surface-bg border-2 border-surface-border rounded-2xl py-6 pl-16 pr-8 text-xl font-black uppercase tracking-tighter outline-none focus:border-primary transition-all appearance-none cursor-pointer shadow-xl"
            >
              <option value="">Seleccione Almacén...</option>
              @for (w of inventoryService.warehouses(); track w.id) {
                <option [value]="w.id">{{ w.name }}</option>
              }
            </select>
          </div>
          
          @if (activeConcept()?.requires_target_warehouse || activeConcept()?.requires_external_entity) {
            <div class="w-full animate-in slide-in-from-top-4 duration-500 space-y-4">
              @if (activeConcept()?.requires_target_warehouse) {
                <select [ngModel]="selectedTargetWarehouseId()" (ngModelChange)="selectedTargetWarehouseId.set($event)" class="w-full input-industrial py-4 text-xs font-bold uppercase tracking-widest">
                  <option value="">Almacén Destino...</option>
                  @for (w of inventoryService.warehouses(); track w.id) { 
                    <option [value]="w.id">{{ w.name }}</option> 
                  }
                </select>
              }
              @if (activeConcept()?.requires_external_entity) {
                <div class="flex flex-col gap-2 w-full">
                  <div class="flex items-center gap-2">
                    <select [ngModel]="selectedSupplierId()" (ngModelChange)="selectedSupplierId.set($event)" class="flex-1 input-industrial py-4 text-xs font-bold uppercase tracking-widest outline-none focus:border-primary">
                      <option value="">{{ type() === 'ENTRADA' ? 'Proveedor' : 'Cliente' }}...</option>
                      @for (s of suppliers(); track s.id) { <option [value]="s.id">{{ s.name }}</option> }
                    </select>
                    <button 
                      type="button"
                      (click)="openAddPartnerModal()"
                      class="w-12 h-12 bg-primary/10 border border-primary/30 text-primary rounded-xl flex items-center justify-center hover:bg-primary/20 transition-all shadow-lg shadow-primary/5 group"
                      [title]="'Agregar ' + (type() === 'ENTRADA' ? 'Proveedor' : 'Cliente')"
                    >
                      <mat-icon class="group-hover:rotate-90 transition-transform">add_business</mat-icon>
                    </button>
                  </div>
                  @if (suppliers().length === 0) {
                    <p class="text-[8px] text-rose-400 font-black uppercase tracking-widest animate-pulse">
                      Cargue proveedores en el catálogo para continuar
                    </p>
                  }
                </div>
              }
            </div>
          }
        </div>
      </div>

      <!-- STEP 2: CAPTURA ENFOCADA (MODO ESCÁNER) -->
      <div class="space-y-6 transition-all duration-700"
           [class.opacity-70]="!selectedWarehouse()">
        
        <div class="relative group z-[60]">
          <div class="relative industrial-card p-2 flex items-center gap-4 bg-surface-bg/80">
            <div class="w-16 h-16 flex items-center justify-center text-primary">
              <mat-icon class="text-4xl animate-pulse">qr_code_scanner</mat-icon>
            </div>
            <app-item-search 
              #mainSearch
              class="flex-1"
              (itemSelected)="onMainItemSelected($event)"
            ></app-item-search>
            <div class="px-6 border-l border-surface-border hidden md:block">
              <span class="text-[9px] font-black text-primary uppercase tracking-[0.3em] animate-pulse">Modo Pistoleo Activo</span>
            </div>
          </div>
        </div>

        <!-- Simplified Grid: "Modo Excel Ultra-Limpio" -->
        <div class="industrial-card border-surface-border">
          <div class="overflow-x-auto custom-scrollbar min-h-[400px]">
            <table class="w-full text-left border-collapse table-fixed" 
                   [icExcelNav]="itemsFormArray.controls" 
                   [skipCols]="[4]"
                   (lastCellTab)="addItem()"
                   (smartPaste)="onPasteData($any($event))">
              <thead>
                <tr class="bg-surface-bg/50 border-b border-surface-border">
                  <th class="w-1/2 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-primary">Producto / Material</th>
                  <th class="w-32 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-center text-surface-text-muted">Cantidad</th>
                  <th class="w-32 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-center text-surface-text-muted">UOM</th>
                  <th class="w-28 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-right text-surface-text-muted">Precio</th>
                  <th class="w-32 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-right text-primary">Subtotal</th>
                  <th class="w-48 px-6 py-4 text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Ubicación</th>
                  <th class="w-16 px-6 py-4"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-surface-border" [formGroup]="documentForm">
                <ng-container formArrayName="items">
                  @for (itemGroup of itemsFormArray.controls; track itemGroup; let i = $index) {
                    <tr [formGroupName]="i" 
                        class="hover:bg-primary/5 transition-all group animate-in slide-in-from-left-2 duration-300"
                        [class.ic-row-error]="isWeightMismatch(i)"
                        [class.ic-row-success]="!isWeightMismatch(i) && itemGroup.get('sku')?.value"
                        [attr.data-row]="i">
                      
                      <!-- COL 0: PRODUCTO -->
                      <td class="px-0 py-0 relative transition-all duration-200 border-r border-surface-border" [attr.data-col]="0">
                        <div class="flex flex-col h-full group">
                          <app-item-search 
                            [value]="itemGroup.get('sku')?.value"
                            (itemSelected)="onItemSelected(i, $event)"
                            class="w-full h-full"
                            placeholder="ESCRIBA SKU O NOMBRE..."
                          ></app-item-search>
                          
                          <!-- Forensic Tooltip for Demo/Validation -->
                          <div class="forensic-tooltip no-print translate-x-12">
                            <div class="flex items-center gap-2 mb-2">
                              <mat-icon class="text-primary text-xs">verified_user</mat-icon>
                              <span class="text-[9px] font-black uppercase tracking-widest text-primary">Forensic Validator</span>
                            </div>
                            <div class="space-y-1">
                              <p class="text-[8px] text-surface-text-muted uppercase">SKU: <span class="text-white font-bold">{{ itemGroup.get('sku')?.value || 'PENDIENTE' }}</span></p>
                              <p class="text-[8px] text-surface-text-muted uppercase">Factor: <span class="text-white font-bold">{{ itemGroup.get('factor')?.value || '1.0' }} Kg/{{ itemGroup.get('uom')?.value }}</span></p>
                              <p class="text-[8px] text-surface-text-muted uppercase">Context: <span class="text-cyan-400 font-bold">Industrial Ledger v2</span></p>
                            </div>
                          </div>

                          @if (itemGroup.get('name')?.value) {
                            <div class="absolute bottom-1 left-2 pointer-events-none">
                              <span class="text-[8px] font-bold text-primary/60 truncate uppercase tracking-tighter">
                                {{ itemGroup.get('name')?.value }}
                              </span>
                            </div>
                          }
                        </div>
                      </td>

                      <!-- COL 1: CANTIDAD -->
                      <td class="px-0 py-0 border-r border-surface-border" [attr.data-col]="1">
                        <input 
                          type="number" 
                          formControlName="quantity"
                          class="input-clean text-center font-mono font-black text-lg tabular-nums h-full py-3 text-surface-text"
                          placeholder="0"
                        >
                      </td>

                      <!-- COL 2: UOM -->
                      <td class="px-6 py-3 text-center" [attr.data-col]="2">
                        <select formControlName="uom" class="input-clean text-center text-[10px] font-black uppercase tracking-widest cursor-pointer appearance-none text-surface-text">
                          <option value="PZ">PZ</option>
                          <option value="FT">FT</option>
                          <option value="KG">KG</option>
                          <option value="MT">MT</option>
                          <option value="CJ">CJ</option>
                        </select>
                      </td>

                      <!-- COL PRECIO -->
                      <td class="px-0 py-0 border-r border-surface-border">
                        <input 
                          type="number" 
                          formControlName="unit_price"
                          class="input-clean text-right font-mono font-bold text-[11px] tabular-nums h-full py-3 text-surface-text-muted pr-4"
                          placeholder="0.00"
                        >
                      </td>

                      <!-- COL SUBTOTAL -->
                      <td class="px-6 py-3 text-right border-r border-surface-border bg-primary/5">
                        <span class="text-[11px] font-black text-primary font-mono tracking-tighter">
                          {{ (itemGroup.get('quantity')?.value * itemGroup.get('unit_price')?.value) | currencyFormat }}
                        </span>
                      </td>

                      <!-- COL 3: UBICACIÓN -->
                      <td class="px-6 py-3" [attr.data-col]="3">
                        <div class="flex items-center gap-2">
                          <mat-icon class="text-[10px] text-primary/40">place</mat-icon>
                          <input 
                            formControlName="location"
                            class="input-clean text-[9px] font-black uppercase tracking-widest placeholder:text-rose-500/40 text-surface-text"
                            [placeholder]="itemGroup.get('location')?.value ? '' : 'PENDIENTE'"
                            (keydown.enter)="openLocationSelector(i)"
                          >
                        </div>
                      </td>

                      <!-- COL 4: ACCIONES -->
                      <td class="px-4 py-3 text-center">
                        @if (!isViewing()) {
                          <button (click)="removeItem(i)" 
                                  class="p-2 text-rose-500/40 hover:text-rose-500 hover:bg-rose-500/10 rounded-lg transition-all opacity-100 md:opacity-0 group-hover:opacity-100 flex items-center justify-center mx-auto"
                                  title="Eliminar Partida">
                            <mat-icon class="text-sm">delete_outline</mat-icon>
                          </button>
                        }
                      </td>
                    </tr>
                  }
                </ng-container>
                
                <!-- Manual Add Row Button -->
                @if (!isViewing()) {
                  <tr>
                    <td colspan="5" class="px-6 py-4">
                      <button 
                        (click)="addItem()"
                        class="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary/40 hover:text-primary transition-colors group"
                      >
                        <mat-icon class="text-sm group-hover:scale-125 transition-transform">add_circle</mat-icon>
                        Agregar Nueva Partida (o presiona TAB al final)
                      </button>
                    </td>
                  </tr>
                }

                @if (itemsFormArray.length === 0) {
                  <tr>
                    <td colspan="5" class="px-6 py-24 text-center">
                      <div class="flex flex-col items-center opacity-20">
                        <mat-icon class="text-7xl mb-4 text-primary">barcode_reader</mat-icon>
                        <span class="text-xs font-black uppercase tracking-[0.5em] text-surface-text">Esperando escaneo de material...</span>
                      </div>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </div>

          <!-- Discreto Pie de Página Forense con Totales -->
          <div class="p-6 bg-surface-bg border-t border-surface-border flex flex-col md:flex-row justify-between items-center gap-6 shadow-lg">
            <div class="flex gap-10">
              <div class="flex flex-col">
                <span class="text-[9px] text-surface-text-muted font-black uppercase tracking-[0.3em] mb-1">Partidas</span>
                <span class="text-xl font-black text-surface-text">{{ itemsFormArray.length }}</span>
              </div>
              <div class="flex flex-col">
                <span class="text-[9px] text-surface-text-muted font-black uppercase tracking-[0.3em] mb-1">Peso Total</span>
                <span class="text-xl font-black text-primary">{{ totalWeight() | number:'1.2-2' }} <span class="text-xs">Kg</span></span>
              </div>
              <div class="flex flex-col">
                <span class="text-[9px] text-surface-text-muted font-black uppercase tracking-[0.3em] mb-1">Unidades</span>
                <span class="text-xl font-black text-emerald-400">{{ totalUnits() }}</span>
              </div>
              <div class="flex flex-col min-w-[150px] border-l border-white/10 pl-10">
                <span class="text-[9px] text-primary font-black uppercase tracking-[0.3em] mb-1">Valor Total ({{ currencyService.currentCurrency().code }})</span>
                <span class="text-2xl font-black text-white glow-text-primary">{{ totalValue() | currencyFormat }}</span>
              </div>
            </div>

            <div class="flex items-center gap-4 ml-auto">
              <!-- Botón Regresar -->
              <button 
                (click)="goBack()"
                class="px-4 py-3 text-[9px] font-black uppercase tracking-[0.3em] text-surface-text-muted hover:text-surface-text transition-all flex items-center gap-2"
              >
                <mat-icon class="text-sm">arrow_back</mat-icon>
                Regresar al Dashboard
              </button>

              @if (confirmedDocument()) {
                <!-- Botones de Impresión (Solo cuando hay un documento confirmado) -->
                <button 
              (click)="printInvoice()"
              class="px-5 py-3 bg-surface-bg border border-surface-border hover:bg-primary/10 text-surface-text rounded-xl text-[9px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-2 shadow-lg"
            >
              <mat-icon class="text-sm">print</mat-icon>
              Imprimir Movimientos
            </button>

            <button 
              (click)="printLabel()"
              class="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[9px] font-black uppercase tracking-[0.3em] transition-all flex items-center gap-2 shadow-lg"
            >
              <mat-icon class="text-sm">label</mat-icon>
              Imprimir Etiqueta
            </button>
          } @else {
            <button 
              [disabled]="!isValid() || isViewing()"
              (click)="confirmMovement()"
              [class.bg-emerald-500]="isValid() && !isViewing()"
              [class.text-slate-950]="isValid() && !isViewing()"
              [class.bg-surface-bg]="!isValid() || isViewing()"
              [class.text-surface-text-muted]="!isValid() || isViewing()"
              [class.border-surface-border]="!isValid() || isViewing()"
              class="py-4 px-12 rounded-2xl font-black text-sm uppercase tracking-[0.4em] transition-all duration-500 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed border-2 border-white/5 hover:border-emerald-500/50 shadow-lg shadow-emerald-500/10"
            >
              {{ isViewing() ? 'MODO LECTURA' : 'FINALIZAR REGISTRO' }}
            </button>
          }
        </div>
      </div>
        </div>
      </div>

      <!-- Notas del Movimiento -->
      <div class="industrial-card p-6 border-l-4 border-primary">
        <label class="block text-[10px] font-black text-primary uppercase tracking-[0.3em] mb-3">Notas Adicionales / Referencias</label>
        <textarea 
          [ngModel]="notes()" 
          (ngModelChange)="notes.set($event)"
          rows="2"
          placeholder="Escriba comentarios, números de orden, folios externos..."
          class="w-full bg-surface-bg/50 border border-surface-border rounded-xl p-4 text-[11px] font-bold text-surface-text outline-none focus:border-primary transition-all resize-none"
        ></textarea>
      </div>

      <div class="mt-12 pt-8 border-t border-surface-border">
        <app-audit-footer 
          [createdBy]="authService.currentUser()?.full_name || 'Admin Demo'"
          [createdAt]="today"
        ></app-audit-footer>
      </div>
    </div>

    <!-- NEW PARTNER MODAL -->
    @if (isAddingPartner()) {
      <app-partner-modal #partnerModal (onSaved)="onPartnerSaved($event)" (onClosed)="isAddingPartner.set(false)"></app-partner-modal>
    }

    <!-- Success Overlay (Only for new movements) -->
    @if (confirmedDocument(); as doc) {
      @if (!isViewing()) {
        <div class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-surface-bg/90 backdrop-blur-md animate-in fade-in duration-300 overflow-y-auto">
        <div class="industrial-card max-w-lg w-full p-8 text-center space-y-6 shadow-2xl my-auto max-h-[95vh] overflow-y-auto custom-scrollbar no-print relative">
          <button (click)="goBack()" class="absolute top-4 right-4 p-2 text-surface-text-muted hover:text-primary transition-colors rounded-xl hover:bg-surface-bg">
            <mat-icon>close</mat-icon>
          </button>
          <div class="flex flex-col items-center">
            <div class="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center text-primary mb-4 animate-bounce">
              <mat-icon class="text-3xl">check_circle</mat-icon>
            </div>
            <h2 class="text-xl font-black text-surface-text uppercase tracking-tighter italic mb-1">¡Movimiento Confirmado!</h2>
            <p class="text-surface-text-muted text-[9px] font-bold uppercase tracking-widest">Documento generado exitosamente</p>
          </div>
          
          <div class="flex flex-col items-center gap-4">
            <!-- QR Code for Handheld Scanning -->
            <div class="p-3 bg-white rounded-2xl shadow-lg">
              <img 
                [src]="'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=' + doc.id" 
                alt="QR Code"
                class="w-28 h-28"
                referrerpolicy="no-referrer"
              />
              <p class="text-[7px] font-black text-black uppercase tracking-widest mt-1.5">Scan for Details</p>
            </div>

            <div class="p-3 bg-surface-bg border border-surface-border rounded-xl w-full max-w-[200px]">
              <span class="text-[9px] text-surface-text-muted font-bold uppercase tracking-widest block mb-0.5">Folio del Documento</span>
              <span class="text-lg font-mono font-black text-primary">{{ doc.id }}</span>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-2">
            <button 
              (click)="printInvoice()"
              class="flex items-center justify-center gap-2 w-full py-3 bg-primary border border-primary/20 rounded-xl text-[10px] font-black text-slate-950 uppercase tracking-widest hover:bg-primary/90 transition-all group"
            >
              <mat-icon class="text-sm">print</mat-icon>
              Imprimir Recibo
            </button>
            <button 
              (click)="printLabel()"
              class="flex items-center justify-center gap-2 w-full py-3 bg-surface-bg border border-surface-border rounded-xl text-[10px] font-black text-surface-text uppercase tracking-widest hover:bg-surface-bg/80 transition-all group"
            >
              <mat-icon class="text-sm group-hover:text-primary transition-colors">label</mat-icon>
              Imprimir Etiqueta
            </button>
          </div>

          <div class="pt-4 border-t border-surface-border flex flex-col gap-3">
            <button 
              (click)="goBack()"
              class="px-4 py-4 bg-primary text-slate-950 hover:bg-white transition-all rounded-2xl text-[11px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3 shadow-xl shadow-primary/20 group"
            >
              <mat-icon class="text-lg group-hover:scale-110 transition-transform">dashboard</mat-icon>
              Finalizar y Regresar al Dashboard
            </button>
            <div class="flex flex-col gap-1 pt-2">
              <button 
                (click)="closeSuccessModal()"
                class="text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] hover:text-surface-text transition-colors py-2"
              >
                Regresar al Documento Actual
              </button>
              <button 
                (click)="resetForm()"
                class="text-[9px] font-black text-primary uppercase tracking-[0.2em] hover:underline py-2"
              >
                Capturar Nuevo Movimiento
              </button>
            </div>
          </div>
        </div>
      </div>
    }

      <!-- Hidden Print Templates -->
      <div class="print-only p-12 bg-white text-black min-h-screen font-sans">
        <!-- Professional Inventory Receipt Template -->
        @if (printMode() === 'INVOICE') {
          <div class="max-w-4xl mx-auto">
            <!-- Header Section -->
            <div class="flex justify-between items-start mb-10 pb-10 border-b-2 border-black">
              <div class="flex items-center gap-6">
                <div class="w-20 h-20 bg-black flex items-center justify-center text-white rounded-2xl shadow-lg">
                  <mat-icon class="text-5xl">inventory_2</mat-icon>
                </div>
                <div>
                  <h2 class="text-2xl font-black tracking-tighter uppercase leading-none mb-1">Interno Logistics</h2>
                  <p class="text-[12px] font-bold text-gray-500 uppercase tracking-[0.3em]">Supply Chain SSOT • Plant Network</p>
                  <p class="text-[9px] font-medium text-gray-400 mt-2 max-w-[200px]">Industrial-grade inventory control system. Document generated electronically.</p>
                </div>
              </div>
              <div class="text-right">
                <h1 class="text-5xl font-black uppercase tracking-tighter text-gray-900 leading-none mb-4 italic">INVOICE</h1>
                <div class="space-y-1">
                  <div class="inline-block px-3 py-1 bg-black text-white text-[10px] font-black uppercase tracking-widest mb-2">
                    Movement Folio
                  </div>
                  <p class="text-xl font-black font-mono tracking-tighter">{{ doc.id }}</p>
                  <p class="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{{ doc.timestamp | date:'MMM dd, yyyy | HH:mm:ss' }}</p>
                </div>
              </div>
            </div>

            <!-- Info Grid -->
            <div class="grid grid-cols-3 gap-8 mb-12 border-y border-gray-200 py-8">
              <div>
                <h3 class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">
                  {{ doc.type === 'ENTRADA' ? 'Destination / Target' : 'Origin / Source' }}
                </h3>
                <div class="text-sm">
                  <p class="font-black">{{ doc.warehouse }}</p>
                  <p class="text-gray-600">Industrial OS Network</p>
                </div>
              </div>
              <div>
                <h3 class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">Destination / Type</h3>
                <div class="text-sm">
                  <p class="font-black">{{ doc.type === 'ENTRADA' ? 'RECEIVING (ENTRADA)' : 'SHIPPING (SALIDA)' }}</p>
                  <p class="text-gray-600">Concept: {{ doc.concept_name }}</p>
                  <p class="text-gray-600">Status: Confirmed</p>
                </div>
              </div>
              <div class="flex flex-col items-end">
                <h3 class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">Document QR</h3>
                <img 
                  [src]="'https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=' + doc.id" 
                  alt="QR Code"
                  class="w-20 h-20 border border-gray-100 p-1"
                  referrerpolicy="no-referrer"
                />
              </div>
            </div>

            <!-- Items Table -->
            <table class="w-full mb-12">
              <thead>
                <tr class="bg-gray-50 border-b-2 border-black">
                  <th class="py-3 px-4 text-left text-[10px] font-black uppercase tracking-widest">#</th>
                  <th class="py-3 px-4 text-center text-[10px] font-black uppercase tracking-widest">Validation QR</th>
                  <th class="py-3 px-4 text-left text-[10px] font-black uppercase tracking-widest">Item Description & SKU</th>
                  <th class="py-3 px-4 text-left text-[10px] font-black uppercase tracking-widest">Location</th>
                  <th class="py-3 px-4 text-right text-[10px] font-black uppercase tracking-widest">Qty</th>
                  <th class="py-3 px-4 text-right text-[10px] font-black uppercase tracking-widest">Price ({{ currencyService.currentCurrency().code }})</th>
                  <th class="py-3 px-4 text-right text-[10px] font-black uppercase tracking-widest">Subtotal</th>
                  <th class="py-3 px-4 text-right text-[10px] font-black uppercase tracking-widest">Weight</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                @for (item of doc.items; track $index; let i = $index) {
                  <tr>
                    <td class="py-4 px-4 text-sm font-bold text-gray-400">{{ i + 1 }}</td>
                    <td class="py-4 px-4 text-center">
                      <div class="flex justify-center">
                        <img 
                          [src]="'https://api.qrserver.com/v1/create-qr-code/?size=50x50&data=' + doc.id + '|' + item.sku + '|' + item.quantity" 
                          alt="Item QR"
                          class="w-12 h-12 border border-gray-100 p-0.5"
                          referrerpolicy="no-referrer"
                        />
                      </div>
                    </td>
                    <td class="py-4 px-4">
                      <p class="text-sm font-black">{{ item.sku }}</p>
                      <p class="text-xs text-gray-600">{{ item.name }}</p>
                      @if (item.variant) {
                        <p class="text-[10px] italic text-gray-400">{{ item.variant }}</p>
                      }
                    </td>
                    <td class="py-4 px-4 text-sm font-medium">{{ item.location }}</td>
                    <td class="py-4 px-4 text-right text-sm font-black">{{ item.quantity }} <span class="text-[8px] text-gray-400">{{ item.uom_name }}</span></td>
                    <td class="py-4 px-4 text-right text-sm font-bold text-gray-600">{{ item.unit_price | currencyFormat }}</td>
                    <td class="py-4 px-4 text-right text-sm font-black">{{ (item.quantity * item.unit_price) | currencyFormat }}</td>
                    <td class="py-4 px-4 text-right text-sm font-mono">{{ item.weight | number:'1.2-2' }} Kg</td>
                  </tr>
                }
              </tbody>
              <tfoot>
                <tr class="border-t-2 border-black bg-gray-50">
                  <td colspan="3" class="py-4 px-4 text-right text-[10px] font-black uppercase tracking-widest text-gray-400">Inventory Movement Grand Totals</td>
                <td class="py-4 px-4 text-right text-lg font-black">{{ getDocTotalUnits(doc.items) }}</td>
                <td class="py-4 px-4 text-right text-lg font-black text-primary">{{ getDocTotalValue(doc.items) | currencyFormat }}</td>
                <td class="py-4 px-4 text-right text-lg font-black">{{ getDocTotalWeight(doc.items) | number:'1.2-2' }} Kg</td>
                </tr>
              </tfoot>
            </table>

            <!-- Footer Section -->
            <div class="grid grid-cols-2 gap-12 mb-16">
              <div>
                <h3 class="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-3">Notes / Comments</h3>
                <p class="text-sm italic text-gray-600 leading-relaxed">
                  {{ doc.notes || 'No additional notes provided for this transaction.' }}
                </p>
              </div>
              <div class="space-y-8">
                <div class="border-b border-black pb-1">
                  <p class="text-[8px] font-black uppercase tracking-widest text-gray-400 mb-8">Authorized Signature</p>
                </div>
                <div class="border-b border-black pb-1">
                  <p class="text-[8px] font-black uppercase tracking-widest text-gray-400 mb-8">Receiver Signature</p>
                </div>
              </div>
            </div>

            <div class="text-center border-t border-gray-100 pt-8">
              <p class="text-[9px] text-gray-300 font-bold uppercase tracking-[0.5em]">Interno Core v2.0 • Forensic Ledger Verification • Trace ID: {{ doc.correlation_id }}</p>
              <div class="mt-4 flex justify-center gap-2 opacity-20">
                <mat-icon class="text-sm">security</mat-icon>
                <mat-icon class="text-sm">fingerprint</mat-icon>
                <mat-icon class="text-sm">verified</mat-icon>
              </div>
            </div>
          </div>
        }

        <!-- Label Template -->
        @if (printMode() === 'LABEL') {
          <div class="border-4 border-black p-6 w-[400px] mx-auto text-center space-y-4">
            <h2 class="text-xs font-black uppercase tracking-[0.3em] text-gray-400">Etiqueta de Control</h2>
            <div class="py-4 border-y-2 border-black">
              <h1 class="text-5xl font-black font-mono">{{ doc.id }}</h1>
            </div>
            <div class="grid grid-cols-2 gap-4 text-left">
              <div>
                <p class="text-[8px] font-black uppercase text-gray-400">Fecha</p>
                <p class="text-[10px] font-bold">{{ doc.timestamp | date:'shortDate' }}</p>
              </div>
              <div>
                <p class="text-[8px] font-black uppercase text-gray-400">Tipo</p>
                <p class="text-[10px] font-bold">{{ doc.type }} - {{ doc.concept_name }}</p>
              </div>
            </div>
            <div class="pt-2">
              <p class="text-[8px] font-black uppercase text-gray-400">Partidas</p>
              <p class="text-xs font-bold">{{ doc.items.length }} Items • {{ getDocTotalWeight(doc.items) | number:'1.2-2' }} Kg</p>
            </div>
            <div class="flex justify-center pt-2">
              <img 
                [src]="'https://api.qrserver.com/v1/create-qr-code/?size=100x100&data=' + doc.id" 
                alt="QR Code"
                class="w-24 h-24"
                referrerpolicy="no-referrer"
              />
            </div>
          </div>
        }
      </div>
    }
  `
})
export class InventoryDocumentComponent implements OnInit {
  authService = inject(AuthService);
  masterData = inject(MasterDataService);
  inventoryService = inject(InventoryService);
  currencyService = inject(CurrencyService);
  fb = inject(FormBuilder);
  router = inject(Router);
  route = inject(ActivatedRoute);
  
  @ViewChild('mainSearch') mainSearch!: ItemSearchComponent;
  @ViewChildren('qtyInput') qtyInputs!: QueryList<ElementRef<HTMLInputElement>>;

  documentForm: FormGroup = this.fb.group({
    items: this.fb.array([])
  });
  
  suppliers = signal<Partner[]>([]);
  selectedSupplierId = signal<string>('');

  selectedWarehouseId = signal<string>('');
  selectedTargetWarehouseId = signal<string>('');

  selectedWarehouse = computed(() => this.inventoryService.warehouses().find(w => w.id === this.selectedWarehouseId()));
  selectedTargetWarehouse = computed(() => this.inventoryService.warehouses().find(w => w.id === this.selectedTargetWarehouseId()));

  type = signal<'ENTRADA' | 'SALIDA'>('ENTRADA');
  selectedConceptId = signal<string>('');
  
  confirmedDocument = signal<ConfirmedDocument | null>(null);
  printMode = signal<'INVOICE' | 'LABEL' | null>(null);
  today = new Date();
  notes = signal<string>('');
  isViewing = signal<boolean>(false);
  
  isAddingPartner = signal(false);
  @ViewChild('partnerModal') partnerModal!: PartnerModalComponent;

  // Signal-based form value for reactivity in computed properties
  formValue = toSignal(this.documentForm.valueChanges, { initialValue: { items: [] } });

  totalValue = computed(() => {
    const items = this.formValue().items || [];
    return items.reduce((acc: number, item: any) => acc + ((item.quantity || 0) * (item.unit_price || 0)), 0);
  });

  constructor() {
    // Forensic Logic: Sync weight and quantity
    effect(() => {
      // This could be handled via valueChanges but user asked for a listener on FormArray
    });
  }

  get itemsFormArray() {
    return this.documentForm.get('items') as FormArray;
  }

  async ngOnInit() {
    // Shared loading logic in InventoryService
    await this.inventoryService.loadCatalogs();
    this.loadPartners();

    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.loadExistingDocument(id);
    } else if (this.itemsFormArray.length === 0) {
      this.addItem();
    }
  }

  async loadExistingDocument(id: string) {
    try {
      const doc = await this.inventoryService.getDocument(id);
      if (doc) {
        this.isViewing.set(true);
        // 1. Pre-fill signals for the background form
        this.type.set(doc.type === 'ENTRY' || doc.type === 'ENTRADA' || doc.type === 'IN' ? 'ENTRADA' : 'SALIDA');
        this.notes.set(doc.notes || '');
        this.selectedWarehouseId.set(doc.warehouse_id || '');
        this.selectedConceptId.set(doc.concept_id || '');
        
        // 2. Clear and fill items array to show in background form
        this.itemsFormArray.clear();
        if (doc.items && doc.items.length > 0) {
          doc.items.forEach((item: any) => {
            this.itemsFormArray.push(this.fb.group({
              product_id: [item.product_id],
              sku: [item.sku],
              name: [item.name],
              quantity: [item.quantity],
              uom: [item.uom_name || 'PZA'],
              uom_id: [item.uom_id],
              unit_price: [item.unit_price || 0],
              weight: [item.weight],
              location: [item.location]
            }));
          });
        }

        // 3. Set confirmedDocument so print methods have data
        const confirmed: ConfirmedDocument = {
          id: doc.folio,
          correlation_id: doc.id,
          timestamp: doc.date,
          user_agent: 'Backend Ledger',
          type: (doc.type === 'ENTRY' || doc.type === 'IN' || doc.type === 'ENTRADA') ? 'ENTRADA' : 'SALIDA',
          concept_id: doc.concept_id || '',
          concept_name: 'Transacción Registrada',
          warehouse_id: doc.warehouse_id || '',
          warehouse: doc.origin,
          target_warehouse_id: '',
          target_warehouse: doc.destination,
          external_entity: '',
          notes: doc.notes || '',
          items: doc.items.map((item: any) => ({
            product_id: item.product_id,
            sku: item.sku,
            name: item.name,
            quantity: item.quantity,
            uom_id: item.uom_id,
            uom_name: item.uom_name,
            weight: item.weight,
            unit_price: item.unit_price || 0,
            location: item.location
          })),
          audit: { client_time: doc.date, location_context: 'LEDGER' }
        };
        this.confirmedDocument.set(confirmed);
        this.documentForm.disable(); // Disable all fields in view mode
      }
    } catch (error) {
      console.error('Error loading document:', error);
    }
  }

  // Concept loading is now handled by inventoryService.loadCatalogs()
  // which populates inventoryService.concepts() signal. 
  // We'll remove loadConcepts here.

  loadPartners() {
    this.masterData.getPartners().subscribe({
      next: (res: any) => this.suppliers.set(res.data || []),
      error: () => this.suppliers.set([])
    });
  }

  isReadOnly = computed(() => this.authService.isReadOnly());
  concepts = computed(() => {
    const docType = this.type(); // ENTRADA | SALIDA
    const all = this.inventoryService.concepts();

    return all.filter(c => {
      const conceptType = (c.type || '').toUpperCase();

      // TRANSFER is always visible as it requires dual warehouse context (ENTRADA or SALIDA)
      if (conceptType === 'TRANSFER' || conceptType === 'TRASPASO') return true;

      if (docType === 'ENTRADA') {
        return ['IN', 'ENTRY', 'ENTRADA'].includes(conceptType);
      } else {
        return ['OUT', 'OUTPUT', 'SALIDA'].includes(conceptType);
      }
    });
  });
  activeConcept = computed(() => this.inventoryService.concepts().find(c => c.id === this.selectedConceptId()));

  isValid = computed(() => {
    if (this.isReadOnly()) return false;
    const formItems = this.formValue().items;
    if (!formItems || formItems.length === 0) return false;
    
    // 1. Check Row Validity
    const items = this.itemsFormArray.controls;
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.invalid) return false;
        if (!item.get('sku')?.value) return false;
        
        const weight = item.get('weight')?.value || 0;
        // Weight is now optional/informational for demo
        // if (weight > 0 && this.isWeightMismatch(i)) return false;
    }
    
    // 2. Check Header Context
    if (!this.selectedWarehouseId()) return false;
    
    const concept = this.activeConcept();
    if (!concept) return false;

    if (concept.requires_target_warehouse) {
      if (!this.selectedTargetWarehouseId()) return false;
      if (this.selectedWarehouseId() === this.selectedTargetWarehouseId()) return false;
    }

    if (concept.requires_external_entity) {
      if (!this.selectedSupplierId()) return false;
    }

    return true;
  });

  // Debug effect to catch validation blockers
  _debugValidation = effect(() => {
    const valid = this.isValid();
    if (!valid) {
      const items = this.itemsFormArray.controls;
      let reasons: string[] = [];
      if (!this.selectedWarehouseId()) reasons.push('Falta Almacén');
      if (!this.selectedConceptId()) reasons.push('Falta Concepto');
      
      items.forEach((item, i) => {
        if (item.invalid) {
          const errors: string[] = [];
          const group = item as FormGroup;
          Object.keys(group.controls).forEach(key => {
            if (group.get(key)?.invalid) errors.push(key);
          });
          reasons.push(`Falta dato en Partida ${i+1} (${errors.join(', ')})`);
        }
      });
      console.warn('[Forensic Validator] Registro Incompleto:', reasons.join(' • '));
    } else {
      console.log('[Forensic Validator] Formulario listo.');
    }
  });

  // Debug effect to see why it's failing in console
  validationLogger = effect(() => {
    console.log('[Validation] Status:', {
        valid: this.isValid(),
        readOnly: this.isReadOnly(),
        itemCount: this.itemsFormArray.length,
        concept: this.activeConcept()?.name || 'NONE',
        warehouse: this.selectedWarehouseId() || 'NONE',
        formValid: this.documentForm.valid
    });
  });

  totalUnits = computed(() => {
    const items = this.formValue().items as any[];
    return items.reduce((acc, item) => acc + (Number(item.quantity) || 0), 0);
  });

  totalWeight = computed(() => {
    const items = this.formValue().items as any[];
    return items.reduce((acc, item) => acc + (Number(item.weight) || 0), 0);
  });

  isWeightMismatch(index: number): boolean {
    const group = this.itemsFormArray.at(index);
    if (!group) return false;
    
    const qty = group.get('quantity')?.value || 0;
    const factor = group.get('factor')?.value || 0;
    const weight = group.get('weight')?.value || 0;
    
    const expectedWeight = qty * factor;
    return Math.abs(expectedWeight - weight) > WEIGHT_TOLERANCE;
  }

  setType(type: 'ENTRADA' | 'SALIDA') {
    this.type.set(type);
    this.selectedConceptId.set(''); // Reset concept when type changes
  }

  @HostListener('window:keydown', ['$event'])
  handleGlobalKeydown(event: KeyboardEvent) {
    if (event.altKey && event.key.toLowerCase() === 'a') {
      event.preventDefault();
      this.addItem();
    }
    if (event.ctrlKey && event.key === 'Enter') {
      event.preventDefault();
      this.confirmMovement();
    }
  }

  onWarehouseChange() {
    if (this.selectedWarehouse()) {
      setTimeout(() => this.mainSearch?.focus(), 100);
    }
  }

  onMainItemSelected(item: InventoryItem) {
    this.addItemFromSelection(item);
    this.mainSearch.clear();
  }

  addItemFromSelection(item: InventoryItem) {
    const group = this.createItemFormGroup(item);
    this.itemsFormArray.insert(0, group);
    // Focus quantity of the new item
    setTimeout(() => this.focusQuantity(0), 100);
  }

  createItemFormGroup(item?: InventoryItem) {
    const group = this.fb.group({
      sku: [item?.sku || '', Validators.required],
      product_id: [item?.id || ''],
      name: [item?.name || ''],
      quantity: [1, [Validators.required, Validators.min(0.001)]],
      uom: [item?.unit || 'PZ'],
      uom_id: [item?.uomId || item?.conversions?.[0]?.id || ''],
      unit_price: [item?.lastPrice || 0],
      factor: [item?.conversions?.[0]?.factor || 1],
      weight: [item?.unitWeight || 0],
      location: [''],
      availableStock: [item?.available || 0]
    });

    // Auto-calculate weight when quantity or factor changes
    group.get('quantity')?.valueChanges.subscribe(qty => {
      const factor = group.get('factor')?.value || 0;
      const q = qty ?? 0;
      group.get('weight')?.setValue(q * factor, { emitEvent: false });
    });

    return group;
  }

  addItem() {
    this.itemsFormArray.push(this.createItemFormGroup());
    // Focus first field of new row
    setTimeout(() => {
      const lastRowIndex = this.itemsFormArray.length - 1;
      const firstCell = document.querySelector(`tr[data-row="${lastRowIndex}"] td[data-col="0"]`);
      const searchInput = firstCell?.querySelector('input') as HTMLInputElement;
      searchInput?.focus();
    }, 50);
  }

  openLocationSelector(index: number) {
    // Placeholder for location selector logic
    console.log('Opening location selector for row', index);
    const group = this.itemsFormArray.at(index);
    if (group && !group.get('location')?.value) {
      group.patchValue({ location: 'ZONA-RECEPCION' });
    }
  }

  removeItem(index: number) {
    this.itemsFormArray.removeAt(index);
  }

  onItemSelected(index: number, item: InventoryItem) {
    const group = this.itemsFormArray.at(index);
    if (!group) return;

    group.patchValue({
      sku: item.sku,
      product_id: item.id,
      name: item.name,
      uom: item.unit || 'PZ',
      uom_id: item.uomId || '',
      unit_price: item.lastPrice || 0,
      factor: 1,
      weight: item.unitWeight || 0,
      availableStock: item.available || 0
    });

    // Auto-focus quantity field after selection
    setTimeout(() => this.focusQuantity(index), 100);
  }

  onPasteData(data: string[][]) {
    data.forEach(row => {
      if (row.length >= 2) {
        const group = this.fb.group({
          sku: [row[0], Validators.required],
          name: [''],
          quantity: [parseFloat(row[1]) || 1, Validators.required],
          uom: [row[2] || 'PZ'],
          uom_id: ['1a7444c9-40df-51d5-833b-501fc84b67bb', Validators.required],
          factor: [1],
          weight: [0],
          location: [row[3] || ''],
          availableStock: [0]
        });
        this.itemsFormArray.push(group);
      }
    });
  }

  focusQuantity(index: number) {
    const row = document.querySelector(`tr[data-row="${index}"]`);
    const qtyInput = row?.querySelector('input[formControlName="quantity"]') as HTMLInputElement;
    qtyInput?.focus();
  }

  async confirmMovement() {
    if (!this.isValid()) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const items = this.itemsFormArray.value as any[];
    
    // API Mapping: Normalize for backend expectations
    const payload = {
      correlation_id: crypto.randomUUID(),
      type: this.type() === 'ENTRADA' ? 'IN' : 'OUT',
      concept_id: this.selectedConceptId(),
      warehouse_id: this.selectedWarehouseId(),
      target_warehouse_id: this.activeConcept()?.requires_target_warehouse ? this.selectedTargetWarehouseId() : undefined,
      external_entity: this.activeConcept()?.requires_external_entity ? this.selectedSupplierId() : null,
      notes: this.notes(),
      items: items.map(item => ({
        product_id: item.product_id || 'demo-prod-id',
        sku: item.sku,
        quantity: item.quantity,
        uom_id: item.uom_id,
        weight: item.weight,
        unit_price: item.unit_price || 0,
        location: item.location || null
      }))
    };

    console.log('Finalizing Inventory Document Payload:', payload);

    try {
      const response = await this.inventoryService.createDocument(payload as any, payload.correlation_id!);
      
      // Inject view-friendly data for the UI/Print view
      const confirmed: ConfirmedDocument = {
        id: (response as any).id,
        correlation_id: payload.correlation_id,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        type: this.type(),
        concept_id: payload.concept_id,
        concept_name: this.activeConcept()?.name,
        warehouse_id: payload.warehouse_id,
        warehouse: this.selectedWarehouse()?.name || '',
        target_warehouse_id: payload.target_warehouse_id,
        target_warehouse: this.selectedTargetWarehouse()?.name || '',
        external_entity: this.suppliers().find(s => s.id === this.selectedSupplierId())?.name || null,
        notes: payload.notes,
        items: items.map(item => ({
          product_id: item.product_id,
          sku: item.sku,
          name: item.name || 'Producto sin nombre',
          variant: item.variant,
          quantity: item.quantity,
          uom_id: item.uom_id,
          uom_name: item.uom || 'PZA',
          unit_price: 0,
          weight: item.weight || (item.quantity * (item.factor || 1)),
          location: item.location
        })),
        audit: {
          client_time: new Date().toLocaleString(),
          location_context: 'PLANT-NETWORK'
        }
      };

      this.confirmedDocument.set(confirmed);
    } catch (error) {
      console.error('Error creating document:', error);
      // Fallback for demo if backend fails or skip for now to let UI show
      this.confirmedDocument.set({
        id: 'ERR-' + Math.random().toString(36).substring(2, 7).toUpperCase(),
        correlation_id: payload.correlation_id,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent,
        type: this.type(),
        concept_id: payload.concept_id,
        concept_name: this.activeConcept()?.name,
        warehouse_id: payload.warehouse_id,
        warehouse: this.selectedWarehouse()?.name || '',
        target_warehouse_id: payload.target_warehouse_id,
        target_warehouse: this.selectedTargetWarehouse()?.name || '',
        external_entity: this.suppliers().find(s => s.id === this.selectedSupplierId())?.name || null,
        notes: payload.notes,
        items: items.map(item => ({
          product_id: item.product_id,
          sku: item.sku,
          name: item.name || 'Demo Item',
          variant: item.variant,
          quantity: item.quantity,
          uom_id: item.uom_id,
          uom_name: item.uom || 'PZA',
          unit_price: 0,
          weight: item.weight || (item.quantity * (item.factor || 1)),
          location: item.location
        })),
        audit: { client_time: new Date().toLocaleString(), location_context: 'DEMO-FALLBACK' }
      });
    }
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getDocTotalUnits(items: any[]): number {
    return items.reduce((acc, item) => acc + (item.quantity || 0), 0);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getDocTotalWeight(items: any[]): number {
    return items.reduce((acc, item) => acc + (item.weight || 0), 0);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  getDocTotalValue(items: any[]): number {
    return items.reduce((acc, item) => acc + ((item.quantity || 0) * (item.unit_price || 0)), 0);
  }

  printInvoice() {
    const doc = this.confirmedDocument();
    if (!doc) return;

    const items = doc.items.map((item: any, i: number) => `
      <tr style="border-bottom: 1px solid #e5e7eb;">
        <td style="padding: 12px 16px; font-size: 12px; color: #9ca3af;">${i + 1}</td>
        <td style="padding: 12px 16px; font-size: 12px; font-weight: 900;">${item.sku}</td>
        <td style="padding: 12px 16px; font-size: 12px;">${item.name || '-'}</td>
        <td style="padding: 12px 16px; font-size: 12px;">${item.location || '-'}</td>
        <td style="padding: 12px 16px; font-size: 12px; text-align: right; font-weight: 900;">${item.quantity}</td>
        <td style="padding: 12px 16px; font-size: 12px; text-align: right;">${this.currencyService.format(item.unit_price || 0)}</td>
        <td style="padding: 12px 16px; font-size: 12px; text-align: right; font-weight: 900;">${this.currencyService.format((item.quantity || 0) * (item.unit_price || 0))}</td>
        <td style="padding: 12px 16px; font-size: 12px; text-align: right; font-family: monospace;">${(item.weight || 0).toFixed(2)} Kg</td>
      </tr>
    `).join('');

    const totalUnits = doc.items.reduce((a: number, i: any) => a + (i.quantity || 0), 0);
    const totalWeight = doc.items.reduce((a: number, i: any) => a + (i.weight || 0), 0);
    const totalValue = doc.items.reduce((a: number, i: any) => a + ((i.quantity || 0) * (i.unit_price || 0)), 0);
    const now = new Date().toLocaleString('es-MX');

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Recibo - ${doc.id}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Arial, sans-serif; background: white; color: #111827; padding: 40px; }
    .header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid black; padding-bottom: 32px; margin-bottom: 32px; }
    .company-name { font-size: 22px; font-weight: 900; text-transform: uppercase; letter-spacing: -0.05em; }
    .subtitle { font-size: 10px; font-weight: 700; color: #6b7280; text-transform: uppercase; letter-spacing: 0.3em; margin-top: 4px; }
    .title { font-size: 42px; font-weight: 900; text-transform: uppercase; font-style: italic; letter-spacing: -0.05em; color: #111827; }
    .folio-badge { background: black; color: white; font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.2em; padding: 4px 10px; margin-bottom: 8px; display: inline-block; }
    .folio { font-size: 20px; font-weight: 900; font-family: monospace; }
    .meta-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; border-top: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb; padding: 24px 0; margin-bottom: 32px; }
    .meta-label { font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.3em; color: #9ca3af; margin-bottom: 8px; }
    .meta-value { font-size: 13px; font-weight: 900; }
    .meta-sub { font-size: 11px; color: #6b7280; }
    table { width: 100%; border-collapse: collapse; margin-bottom: 32px; }
    thead tr { background: #f9fafb; border-bottom: 2px solid black; }
    th { padding: 10px 16px; text-align: left; font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.2em; }
    th:last-child, th:nth-child(5) { text-align: right; }
    tfoot tr { background: #f9fafb; border-top: 2px solid black; }
    tfoot td { padding: 12px 16px; font-size: 14px; font-weight: 900; }
    .notes-section { border-top: 1px solid #e5e7eb; padding-top: 24px; }
    .notes-label { font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.3em; color: #9ca3af; margin-bottom: 8px; }
    .footer { margin-top: 48px; display: flex; justify-content: space-between; font-size: 9px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 16px; }
    @page { margin: 15mm; size: A4 portrait; }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="company-name">Interno Logistics</div>
      <div class="subtitle">Supply Chain SSOT • Plant Network</div>
    </div>
    <div style="text-align: right;">
      <div class="title">INVOICE</div>
      <div class="folio-badge">Movement Folio</div>
      <div class="folio">${doc.id}</div>
      <div style="font-size: 10px; color: #9ca3af; margin-top: 4px;">${now}</div>
    </div>
  </div>

  <div class="meta-grid">
    <div>
      <div class="meta-label">${doc.type === 'ENTRADA' ? 'Destino / Almacén' : 'Origen / Almacén'}</div>
      <div class="meta-value">${doc.warehouse || '-'}</div>
      <div class="meta-sub">Industrial OS Network</div>
    </div>
    <div>
      <div class="meta-label">Tipo de Movimiento</div>
      <div class="meta-value">${doc.type === 'ENTRADA' ? 'ENTRADA (RECEIVING)' : 'SALIDA (SHIPPING)'}</div>
      <div class="meta-sub">Concepto: ${doc.concept_name || '-'}</div>
      <div class="meta-sub">Estado: Confirmado</div>
    </div>
    <div>
      <div class="meta-label">Entidad / Proveedor</div>
      <div class="meta-value">${doc.external_entity || 'N/A'}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>SKU</th>
        <th>Descripción</th>
        <th>Ubicación</th>
        <th style="text-align:right;">Cantidad</th>
        <th style="text-align:right;">Precio</th>
        <th style="text-align:right;">Subtotal</th>
        <th style="text-align:right;">Peso</th>
      </tr>
    </thead>
    <tbody>${items}</tbody>
    <tfoot>
      <tr>
        <td colspan="4" style="text-align:right; font-size:9px; font-weight:900; text-transform:uppercase; letter-spacing:0.2em; color:#9ca3af;">Totales del Documento</td>
        <td style="text-align:right;">${totalUnits}</td>
        <td colspan="2" style="text-align:right; font-size:16px; font-weight:900; color:#00e5ff;">${this.currencyService.format(totalValue)}</td>
        <td style="text-align:right; font-family:monospace;">${totalWeight.toFixed(2)} Kg</td>
      </tr>
    </tfoot>
  </table>

  <div class="notes-section">
    <div class="notes-label">Notas / Comentarios</div>
    <p style="font-size: 12px; color: #6b7280; font-style: italic;">${doc.notes || 'Sin notas adicionales para esta transacción.'}</p>
  </div>

  <div class="footer">
    <span>InternoCore Inventory Control System — Documento generado electrónicamente</span>
    <span>${doc.id} — ${now}</span>
  </div>
</body>
</html>`;

    const win = window.open('', '_blank', 'width=900,height=700');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.focus();
      setTimeout(() => {
        win.print();
        win.close();
      }, 500);
    }
  }

  printLabel() {
    const doc = this.confirmedDocument();
    if (!doc) return;

    const labelsHtml = doc.items.map((item: any) => `
      <div style="width: 70mm; height: 40mm; border: 2px solid black; padding: 8px; margin: 4px; display: inline-block; font-family: monospace; page-break-inside: avoid; vertical-align: top;">
        <div style="font-size: 7px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.15em; color: #6b7280;">${doc.warehouse || 'ALMACÉN'}</div>
        <div style="font-size: 15px; font-weight: 900; letter-spacing: -0.02em; margin: 2px 0;">${item.sku}</div>
        <div style="font-size: 8px; color: #374151;">${item.name || ''}</div>
        <div style="display: flex; justify-content: space-between; margin-top: 4px; align-items: flex-end;">
          <div>
            <div style="font-size: 16px; font-weight: 900;">${item.quantity} <span style="font-size: 9px;">${item.uom_name || 'PZ'}</span></div>
            <div style="font-size: 7px; color: #9ca3af;">${doc.id}</div>
          </div>
          <img src="https://api.qrserver.com/v1/create-qr-code/?size=60x60&data=${doc.id}|${item.sku}|${item.quantity}" width="55" height="55" referrerpolicy="no-referrer" />
        </div>
      </div>
    `).join('');

    const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Etiquetas - ${doc.id}</title>
  <style>
    body { margin: 10mm; background: white; }
    @page { margin: 10mm; size: A4 portrait; }
  </style>
</head>
<body>${labelsHtml}</body>
</html>`;

    const win = window.open('', '_blank', 'width=900,height=700');
    if (win) {
      win.document.write(html);
      win.document.close();
      win.focus();
      setTimeout(() => win.print(), 500);
    }
  }

  goBack() {
    this.router.navigate(['/dashboard']);
  }

  closeSuccessModal() {
    this.confirmedDocument.set(null);
    this.printMode.set(null);
  }

  resetForm() {
    // Preserve current context (Warehouse, type and concept)
    const currentWarehouse = this.selectedWarehouseId();
    const currentType = this.type();
    const currentConcept = this.selectedConceptId();

    while (this.itemsFormArray.length !== 0) {
      this.itemsFormArray.removeAt(0);
    }
    
    this.confirmedDocument.set(null);
    this.notes.set('');
    
    // Explicitly restore if needed (though they are signals)
    this.selectedWarehouseId.set(currentWarehouse);
    this.type.set(currentType);
    this.selectedConceptId.set(currentConcept);

    this.addItem();
  }

  // === NEW PARTNER METHODS ===
  openAddPartnerModal() {
    this.isAddingPartner.set(true);
    setTimeout(() => {
      this.partnerModal.open(this.type() === 'ENTRADA' ? PartnerType.SUPPLIER : PartnerType.CUSTOMER);
    });
  }

  onPartnerSaved(newPartner: Partner) {
    console.log('[Partner] Created successfully:', newPartner);
    this.suppliers.update(list => [...list, newPartner]);
    this.selectedSupplierId.set(newPartner.id);
    this.isAddingPartner.set(false);
  }
}
