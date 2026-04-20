import { Component, Inject, inject, signal, OnInit, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MasterDataService, Product, ProductPrice, PartnerType, ProductType } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { InventoryService } from '../../core/services/inventory.service';
import { PartnerModalComponent } from '../../shared/components/partner-modal.component';

@Component({
  selector: 'app-product-price-list',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, MatIconModule, MatDialogModule, PartnerModalComponent],
  template: `
      <div class="ic-modal-container industrial-card w-[95vw] lg:w-[1000px] h-auto max-h-[90vh] flex flex-col overflow-hidden shadow-2xl border-emerald-500/30 m-auto rounded-3xl bg-surface-bg">

        
        <!-- Header -->
        <div class="p-8 border-b border-surface-border">
          <div class="flex items-start justify-between">
            <div class="flex items-center gap-6">
              <div class="w-12 h-12 bg-emerald-500/20 rounded-xl flex items-center justify-center text-emerald-400">
                <mat-icon class="text-2xl text-emerald-500">payments</mat-icon>
              </div>
              <div>
                <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">
                  GESTIÓN DE PRODUCTO: {{ product.sku }}
                </h2>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1 font-mono">
                  {{ product.name }} • Datos Maestros y Canales de Precio
                </p>
              </div>
            </div>
            <button (click)="close()" class="p-2 bg-surface-bg border border-surface-border rounded-lg text-surface-text-muted hover:text-white hover:border-red-500 transition-colors">
              <mat-icon class="text-sm">close</mat-icon>
            </button>
          </div>
        </div>

        <div class="ic-modal-body p-8 custom-scrollbar flex-1 overflow-y-auto">
          <!-- TABS -->
          <div class="flex items-center gap-6 mb-6 border-b border-surface-border">
            <button (click)="activeTab.set('INFO')" 
                    class="pb-3 text-[10px] font-black uppercase tracking-widest transition-all relative"
                    [class]="activeTab() === 'INFO' ? 'text-primary' : 'text-surface-text-muted hover:text-surface-text'">
              <div class="flex items-center gap-2">
                <mat-icon class="text-xs">inventory_2</mat-icon>
                <span>Datos Generales</span>
              </div>
              @if (activeTab() === 'INFO') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary rounded-t-full"></div> }
            </button>
            <button (click)="activeTab.set('GLOBAL')" 
                    class="pb-3 text-[10px] font-black uppercase tracking-widest transition-all relative"
                    [class]="activeTab() === 'GLOBAL' ? 'text-emerald-400' : 'text-surface-text-muted hover:text-surface-text'">
              <div class="flex items-center gap-2">
                <mat-icon class="text-xs">payments</mat-icon>
                <span>Listas de Precio</span>
              </div>
              @if (activeTab() === 'GLOBAL') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400 rounded-t-full"></div> }
            </button>
            <button (click)="activeTab.set('B2B')" 
                    class="pb-3 text-[10px] font-black uppercase tracking-widest transition-all relative"
                    [class]="activeTab() === 'B2B' ? 'text-cyan-400' : 'text-surface-text-muted hover:text-surface-text'">
              <div class="flex items-center gap-2">
                <mat-icon class="text-xs">handshake</mat-icon>
                <span>Acuerdos B2B</span>
              </div>
               @if (activeTab() === 'B2B') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-400 rounded-t-full"></div> }
            </button>
            <button (click)="activeTab.set('LOGISTICA')" 
                    class="pb-3 text-[10px] font-black uppercase tracking-widest transition-all relative"
                    [class]="activeTab() === 'LOGISTICA' ? 'text-amber-400' : 'text-surface-text-muted hover:text-surface-text'">
              <div class="flex items-center gap-2">
                <mat-icon class="text-xs">local_shipping</mat-icon>
                <span>Logística (Compra)</span>
              </div>
              @if (activeTab() === 'LOGISTICA') { <div class="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-t-full"></div> }
            </button>
          </div>

          <!-- GENERAL INFO TAB -->
          @if (activeTab() === 'INFO') {
            <form [formGroup]="infoForm" class="space-y-8 animate-fade-in p-2">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div class="space-y-6">
                  <div class="space-y-2">
                    <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block">Identificación Industrial</label>
                    <div class="grid grid-cols-3 gap-4">
                      <div class="col-span-1">
                        <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">SKU *</label>
                        <input formControlName="sku" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold text-primary outline-none focus:border-primary transition-all uppercase">
                      </div>
                      <div class="col-span-2">
                        <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Nombre Comercial *</label>
                        <input formControlName="name" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                      </div>
                    </div>
                  </div>

                  <div class="grid grid-cols-2 gap-6">
                    <div>
                      <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Tipo</label>
                      <select formControlName="product_type" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                        <option value="GOODS">Bien / Físico</option>
                        <option value="SERVICE">Servicio</option>
                      </select>
                    </div>
                    <div>
                      <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Unidad (UOM) *</label>
                      <select formControlName="uom_id" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all cursor-pointer">
                        @for (u of masterData.uoms(); track u.id) {
                          <option [value]="u.id">{{ u.abbreviation }} - {{ u.name }}</option>
                        }
                      </select>
                    </div>
                  </div>
                  
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Descripción Técnica</label>
                    <textarea formControlName="description" rows="3" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all resize-none"></textarea>
                  </div>
                </div>

                <div class="space-y-6">
                  <label class="text-[10px] font-black text-primary uppercase tracking-[0.2em] mb-2 block">Fiscal / Impuestos</label>
                  
                  <div class="grid grid-cols-2 gap-6 p-4 bg-emerald-500/5 rounded-2xl border border-emerald-500/20">
                    <div>
                      <label class="text-[9px] font-black text-emerald-500 uppercase tracking-widest mb-1 block">Código SAT</label>
                      <input formControlName="sat_product_code" type="text" class="w-full bg-surface-bg/50 border border-emerald-500/30 rounded-xl p-3 text-[11px] font-mono font-bold text-emerald-500 outline-none focus:border-emerald-500 transition-all" placeholder="8 dígitos">
                    </div>
                    <div>
                      <label class="text-[9px] font-black text-purple-400 uppercase tracking-widest mb-1 block">Fracción HTS</label>
                      <input formControlName="hts_code" type="text" class="w-full bg-surface-bg/50 border border-purple-400/30 rounded-xl p-3 text-[11px] font-mono font-bold text-purple-400 outline-none focus:border-purple-400 transition-all">
                    </div>
                  </div>

                  <div class="grid grid-cols-1 gap-2">
                    <div class="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl border border-transparent hover:border-white/5 transition-all">
                       <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Objeto de Impuesto (IVA)</span>
                       <label class="relative inline-flex items-center cursor-pointer">
                         <input type="checkbox" formControlName="is_taxable" class="sr-only peer">
                         <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                       </label>
                    </div>
                    <div class="flex items-center justify-between p-3 hover:bg-white/5 rounded-xl border border-transparent hover:border-white/5 transition-all">
                       <span class="text-[9px] font-black text-surface-text-muted uppercase tracking-widest">Trazabilidad por Lotes</span>
                       <label class="relative inline-flex items-center cursor-pointer">
                         <input type="checkbox" formControlName="requires_batch" class="sr-only peer">
                         <div class="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                       </label>
                    </div>
                  </div>

                  <div class="pt-4">
                    <button type="button" (click)="saveGeneralInfo()" [disabled]="infoForm.invalid || loadingInfo()"
                            class="w-full py-4 bg-primary text-slate-950 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] shadow-lg shadow-primary/20 hover:bg-primary-dark transition-all disabled:opacity-30 flex items-center justify-center gap-3 italic">
                      <mat-icon class="text-xs">{{ loadingInfo() ? 'sync' : 'save' }}</mat-icon>
                      <span>{{ loadingInfo() ? 'Guardando cambios...' : 'Actualizar Información Maestra' }}</span>
                    </button>
                  </div>
                </div>
              </div>
            </form>
          }

          <!-- GLOBAL TAB -->
          @if (activeTab() === 'GLOBAL') {
            <!-- Controls -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 bg-surface-bg/50 rounded-2xl border border-surface-border mb-8 animate-fade-in">
              <div>
                <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Moneda</label>
                <select [(ngModel)]="currency" (change)="loadPrices()" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                  <option value="USD">USD - Dólar Estadounidense</option>
                  <option value="MXN">MXN - Peso Mexicano</option>
                </select>
              </div>
              <div>
                <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Almacén (Opcional)</label>
                <select [(ngModel)]="warehouseId" (change)="loadPrices()" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                  <option [ngValue]="null">Precio Global (Empresa)</option>
                  @for (w of warehouses; track w.id) {
                    <option [ngValue]="w.id">{{ w.name }}</option>
                  }
                </select>
              </div>
              <div>
                <label class="block text-[9px] font-black text-primary uppercase tracking-widest mb-2">Tipo de Unidad</label>
                <select [(ngModel)]="unitType" (change)="loadPrices()" class="w-full bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-primary transition-all">
                  <option value="BASE">Unidad Base</option>
                  <option value="SALE">Unidad de Venta</option>
                </select>
              </div>
            </div>

            <!-- Price Grid -->
            <div class="border border-surface-border rounded-2xl bg-surface-card/30 overflow-hidden animate-fade-in">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-surface-bg/80 backdrop-blur-md border-b border-surface-border sticky top-0 z-10">
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] w-20 text-center border-r border-surface-border">LVL</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] border-r border-surface-border">Propósito Sugerido</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] w-48 border-r border-surface-border text-center bg-primary/5">Precio Unitario</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-center w-32 border-r border-surface-border">F. Modif.</th>
                    <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-center w-24">Acción</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-surface-border bg-transparent">
                  @for (tier of tiers; track tier) {
                    <tr class="hover:bg-primary/5 transition-colors group">
                      <td class="px-6 py-3 border-r border-surface-border text-center bg-surface-bg/30">
                        <span class="text-xs font-mono font-black text-surface-text-muted group-hover:text-primary transition-colors">
                          {{ tier }}
                        </span>
                      </td>
                      <td class="px-6 py-3 border-r border-surface-border">
                        <span class="text-[10px] text-surface-text-muted uppercase tracking-widest font-black group-hover:text-primary/80 transition-colors">
                          {{ getTierDescription(tier) }}
                        </span>
                      </td>
                      <td class="px-6 py-1 border-r border-surface-border bg-surface-bg/10 relative group/input">
                        <div class="flex items-center gap-3 h-full absolute inset-0 px-4">
                          <span class="text-[9px] font-bold text-surface-text-muted/60">{{ currency }}</span>
                          <input 
                            type="number" 
                            [(ngModel)]="tempPrices[tier]"
                            (keydown.enter)="savePrice(tier); focusNextRow(tier)"
                            [id]="'price-input-' + tier"
                            placeholder="--"
                            class="w-full h-full bg-transparent border-none text-xs font-mono font-bold text-surface-text outline-none text-right placeholder:text-surface-text-muted/30 focus:text-primary transition-all"
                          />
                        </div>
                      </td>
                      <td class="px-6 py-3 border-r border-surface-border text-center">
                        <span class="text-[9px] font-mono text-surface-text-muted" *ngIf="hasPrice(tier)">
                          {{ getPriceDate(tier) | date:'MM/dd/yy' }}
                        </span>
                        <span class="text-[9px] font-mono text-surface-text-muted/30" *ngIf="!hasPrice(tier)">
                          --
                        </span>
                      </td>
                      <td class="px-6 py-3 text-center bg-surface-bg/10">
                         <div class="flex items-center justify-center gap-2">
                            @if (hasPrice(tier) && tempPrices[tier] === getSavedPrice(tier)) {
                              <mat-icon class="text-base text-emerald-500" title="Guardado">check_circle</mat-icon>
                            } @else if (tempPrices[tier] && tempPrices[tier] !== getSavedPrice(tier)) {
                              <mat-icon class="text-base text-amber-500 animate-pulse" title="Cambios sin guardar">edit</mat-icon>
                            } @else {
                              <span class="text-xs font-black text-surface-text-muted/40">-</span>
                            }
                            <button 
                              (click)="savePrice(tier)"
                              [disabled]="!tempPrices[tier] || tempPrices[tier] === getSavedPrice(tier)"
                              class="p-1 rounded bg-primary/10 text-primary hover:bg-primary hover:text-white disabled:opacity-30 transition-all"
                              title="Guardar Precio (Enter)"
                            >
                              <mat-icon class="text-xs w-3 h-3 flex items-center justify-center">save</mat-icon>
                            </button>
                          </div>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          }

          <!-- B2B TAB -->
          @if (activeTab() === 'B2B') {
            <div class="animate-fade-in relative">
              <div class="flex items-center gap-4 mb-6">
                <div>
                  <label class="block text-[9px] font-black text-cyan-400 uppercase tracking-widest mb-2">Moneda B2B</label>
                  <select [(ngModel)]="currencyB2B" (change)="loadAgreements()" class="w-48 bg-surface-card border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-cyan-500 transition-all">
                    <option value="USD">USD</option>
                    <option value="MXN">MXN</option>
                  </select>
                </div>
                <div class="flex-1"></div>
                <button 
                  (click)="openAddPartnerModal()"
                  class="flex items-center gap-2 px-6 py-3 bg-cyan-900/30 text-cyan-400 border border-cyan-500/30 rounded-xl hover:bg-cyan-500 hover:text-white transition-all text-[10px] font-black uppercase tracking-widest shadow-lg shadow-cyan-500/10"
                >
                  <mat-icon class="text-xs">person_add</mat-icon>
                  Nuevo Socio
                </button>
              </div>

              <!-- PARTNER MODAL OVERLAY -->
              @if (isAddingPartner()) {
                <app-partner-modal 
                  #partnerModal 
                  (onSaved)="onPartnerSaved($event)" 
                  (onClosed)="isAddingPartner.set(false)"
                ></app-partner-modal>
              }

              <div class="border border-surface-border rounded-2xl bg-surface-card/30 overflow-hidden">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-surface-bg/80 backdrop-blur-md border-b border-surface-border">
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] border-r border-surface-border">Cliente / Partner</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] w-48 border-r border-surface-border text-center bg-cyan-900/10">Precio Pactado</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-center w-24">Acción</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-surface-border">
                    @for (partner of partners(); track partner.id) {
                      <tr class="hover:bg-cyan-900/5 transition-colors group">
                        <td class="px-6 py-3 border-r border-surface-border">
                          <span class="text-xs font-bold text-surface-text-muted group-hover:text-cyan-400 transition-colors">
                            {{ partner.name }}
                          </span>
                          <span class="ml-2 px-1.5 py-0.5 rounded bg-surface-bg border border-surface-border text-[8px] font-mono text-surface-text-muted">
                            {{ partner.code }}
                          </span>
                        </td>
                        <td class="px-6 py-1 border-r border-surface-border bg-surface-bg/10 relative group/input">
                          <div class="flex items-center gap-3 h-full absolute inset-0 px-4">
                            <span class="text-[9px] font-bold text-surface-text-muted/60">{{ currencyB2B }}</span>
                            <input 
                              type="number" 
                              [(ngModel)]="tempAgreements[partner.id]"
                              (keydown.enter)="saveAgreement(partner)"
                              placeholder="--"
                              class="w-full h-full bg-transparent border-none text-xs font-mono font-bold text-surface-text outline-none text-right placeholder:text-surface-text-muted/30 focus:text-cyan-400 transition-all"
                            />
                          </div>
                        </td>
                        <td class="px-6 py-3 text-center bg-surface-bg/10">
                           <div class="flex items-center justify-center gap-2">
                              @if (hasAgreement(partner.id) && tempAgreements[partner.id] === getSavedAgreement(partner.id)) {
                                <mat-icon class="text-base text-cyan-500" title="Guardado">check_circle</mat-icon>
                              } @else if (tempAgreements[partner.id] && tempAgreements[partner.id] !== getSavedAgreement(partner.id)) {
                                <mat-icon class="text-base text-amber-500 animate-pulse" title="Cambios sin guardar">edit</mat-icon>
                              } @else {
                                <span class="text-xs font-black text-surface-text-muted/40">-</span>
                              }
                              <button 
                                (click)="saveAgreement(partner)"
                                [disabled]="!tempAgreements[partner.id] || tempAgreements[partner.id] === getSavedAgreement(partner.id)"
                                class="p-1 rounded bg-cyan-900/30 text-cyan-400 hover:bg-cyan-500 hover:text-white disabled:opacity-30 transition-all"
                                title="Guardar Acuerdo"
                              >
                                <mat-icon class="text-xs w-3 h-3 flex items-center justify-center">save</mat-icon>
                              </button>
                            </div>
                        </td>
                      </tr>
                    }
                    @if (partners().length === 0) {
                      <tr>
                        <td colspan="3" class="px-6 py-8 text-center text-surface-text-muted text-xs">
                          No hay clientes (partners) registrados en el catálogo B2B.
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }

          <!-- LOGISTICA TAB -->
          @if (activeTab() === 'LOGISTICA') {
            <div class="animate-fade-in space-y-8 p-2">
              <div class="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6 mb-6">
                <div class="flex items-center gap-4 mb-6">
                  <div class="w-10 h-10 bg-amber-500/20 rounded-lg flex items-center justify-center text-amber-500">
                    <mat-icon>add_shopping_cart</mat-icon>
                  </div>
                  <div>
                    <h3 class="text-[11px] font-black text-amber-500 uppercase tracking-widest">Registrar Variante de Proveedor</h3>
                    <p class="text-[9px] text-surface-text-muted font-bold uppercase tracking-tight">Vincule números de parte industriales (MPN) a este SKU maestro</p>
                  </div>
                </div>

                <form [formGroup]="variantForm" (submit)="saveVariant()" class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Marca / Proveedor *</label>
                    <input formControlName="brand" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-bold outline-none focus:border-amber-500 transition-all uppercase" placeholder="EJ. BOSCH">
                  </div>
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">N° Parte (MPN) *</label>
                    <input formControlName="mfg_part_number" type="text" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold outline-none focus:border-amber-500 transition-all uppercase" placeholder="PART-000">
                  </div>
                  <div>
                    <label class="text-[9px] font-bold text-surface-text-muted uppercase mb-1 block">Precio Ref. (Compra)</label>
                    <input formControlName="unit_price" type="number" class="w-full bg-surface-bg border border-surface-border rounded-xl p-3 text-[11px] font-mono font-bold outline-none focus:border-amber-500 transition-all" placeholder="0.00">
                  </div>
                  <button type="submit" [disabled]="variantForm.invalid || loadingVariants()"
                          class="h-[46px] bg-amber-500 text-slate-950 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-amber-400 transition-all disabled:opacity-30">
                    {{ loadingVariants() ? 'Registrando...' : 'Agregar Variante' }}
                  </button>
                </form>
              </div>

              <div class="border border-surface-border rounded-2xl bg-surface-card/30 overflow-hidden">
                <table class="w-full text-left border-collapse">
                  <thead>
                    <tr class="bg-surface-bg/80 backdrop-blur-md border-b border-surface-border">
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] border-r border-surface-border">Proveedor / Marca</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] border-r border-surface-border">Part Number (MPN)</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-center w-32 border-r border-surface-border">Precio Compra</th>
                      <th class="px-6 py-4 text-[9px] font-black text-surface-text-muted uppercase tracking-[0.2em] text-center w-24">Acciones</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-surface-border">
                    @for (v of variants(); track v.id) {
                      <tr class="hover:bg-amber-500/5 transition-colors group">
                        <td class="px-6 py-4 border-r border-surface-border">
                          <span class="text-xs font-black text-surface-text group-hover:text-amber-400 transition-colors uppercase">
                            {{ v.brand }}
                          </span>
                        </td>
                        <td class="px-6 py-4 border-r border-surface-border">
                          <span class="text-xs font-mono font-bold text-amber-400 bg-amber-500/10 px-2 py-1 rounded">
                            {{ v.mfg_part_number }}
                          </span>
                        </td>
                        <td class="px-6 py-4 border-r border-surface-border text-center">
                          <span class="text-xs font-mono font-bold text-surface-text">
                            $ {{ v.unit_price | number:'1.2-2' }}
                          </span>
                        </td>
                        <td class="px-6 py-4 text-center bg-surface-bg/10">
                          <button (click)="removeVariant(v.id)" class="p-2 text-surface-text-muted hover:text-red-500 transition-colors">
                            <mat-icon class="text-sm">delete</mat-icon>
                          </button>
                        </td>
                      </tr>
                    }
                    @if (variants().length === 0) {
                      <tr>
                        <td colspan="4" class="px-6 py-12 text-center text-surface-text-muted text-[10px] font-bold uppercase tracking-widest">
                          No se han registrado variantes para este producto comercial.
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
            </div>
          }
        </div>

        <!-- Footer -->
        <div class="p-6 border-t border-surface-border bg-surface-bg/30 rounded-b-3xl">
          <div class="flex flex-col md:flex-row justify-between items-center gap-4">
            <p class="text-[9px] text-surface-text-muted font-mono tracking-widest uppercase">
              <span class="font-black text-primary">TIP:</span> ENTER PARA GUARDAR Y SIGUIENTE NIVEL
            </p>
            <div class="flex items-center gap-3">
              <button (click)="close()" class="px-6 py-2 rounded-xl border border-surface-border text-[9px] font-black uppercase tracking-[0.25em] text-surface-text-muted hover:border-surface-text-muted hover:text-white transition-all bg-surface-bg/50">
                Finalizar Gestión
              </button>
            </div>
          </div>
        </div>
      </div>
  `,
  styles: [`
    .ic-modal-container {
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .ic-modal-body {
        flex: 1;
        overflow-y: auto;
        padding-right: 8px;
    }
    .industrial-card {
      background: var(--surface-card);
      backdrop-filter: blur(20px);
      border: 1px solid var(--surface-border);
      border-radius: 24px;
    }
    .custom-scrollbar::-webkit-scrollbar {
      width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(0, 242, 255, 0.2);
      border-radius: 10px;
    }
  `]
})
export class ProductPriceListComponent implements OnInit {
  public product: Product;
  public dialogRef = inject(MatDialogRef<ProductPriceListComponent>);
  
  @ViewChild('partnerModal') partnerModal!: PartnerModalComponent;

  constructor(@Inject(MAT_DIALOG_DATA) public data: { product: Product, activeTab?: 'INFO' | 'GLOBAL' | 'B2B' | 'LOGISTICA' }) {
    this.product = data.product;
    if (data.activeTab) this.activeTab.set(data.activeTab);
  }

  masterData = inject(MasterDataService);
  inventoryService = inject(InventoryService);
  
  currency = 'USD';
  warehouseId: string | null = null;
  unitType: 'BASE' | 'SALE' = 'BASE';
  
  warehouses: any[] = [];
  prices = signal<ProductPrice[]>([]);
  tempPrices: { [key: number]: number } = {};
  tiers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

  activeTab = signal<'INFO' | 'GLOBAL' | 'B2B' | 'LOGISTICA'>('INFO');
  currencyB2B = 'USD';
  partners = signal<any[]>([]);
  agreements = signal<any[]>([]);
  tempAgreements: { [key: string]: number } = {};
  isAddingPartner = signal(false);
  
  loadingInfo = signal(false);
  loadingVariants = signal(false);
  variants = signal<any[]>([]);
  private fb = inject(FormBuilder);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);

  infoForm = this.fb.group({
    sku: ['', [Validators.required]],
    name: ['', [Validators.required]],
    product_type: ['GOODS' as ProductType],
    uom_id: ['', [Validators.required]],
    category_id: [null as string | null],
    brand_id: [null as string | null],
    description: [''],
    sat_product_code: [''],
    hts_code: [''],
    is_taxable: [true],
    requires_batch: [false],
    requires_expiration: [false]
  });

  variantForm = this.fb.group({
    brand: ['', [Validators.required]],
    mfg_part_number: ['', [Validators.required]],
    unit_price: [0, [Validators.required, Validators.min(0)]]
  });

  ngOnInit() {
    this.patchInfoForm();
    this.loadWarehouses();
    this.loadPrices();
    this.loadPartners();
    this.loadAgreements();
    this.loadVariants();
  }

  patchInfoForm() {
    this.infoForm.patchValue({
      sku: this.product.sku,
      name: this.product.name,
      product_type: this.product.product_type,
      uom_id: this.product.base_uom_id || (this.product as any).uom_id,
      category_id: this.product.category_id,
      brand_id: this.product.brand_id,
      description: this.product.description,
      sat_product_code: this.product.sat_product_code,
      hts_code: this.product.hts_code,
      is_taxable: this.product.is_taxable,
      requires_batch: this.product.requires_batch,
      requires_expiration: this.product.requires_expiration
    });
    
    // Check permissions
    const roles = this.auth.roles();
    const isAdmin = roles.includes('admin') || roles.includes('owner') || roles.includes('superadmin');
    if (!isAdmin || this.masterData.isGlobal(this.product)) {
      this.infoForm.disable();
    }
  }

  saveGeneralInfo() {
    if (this.infoForm.invalid) return;
    this.loadingInfo.set(true);
    const data = this.infoForm.getRawValue();

    this.masterData.updateProduct(this.product.id, data as any).subscribe({
      next: (res) => {
        this.product = res.data;
        this.notifications.success('Éxito', 'Información actualizada correctamente');
        this.loadingInfo.set(false);
      },
      error: (err) => {
        this.notifications.error('Error', err?.error?.detail || 'No se pudo actualizar el producto');
        this.loadingInfo.set(false);
      }
    });
  }

  close() {
    this.dialogRef.close(true);
  }

  loadWarehouses() {
    this.masterData.getWarehouses().subscribe(res => {
      this.warehouses = res.data;
    });
  }

  loadPartners() {
    this.masterData.getPartners().subscribe(res => {
      this.partners.set(res.data);
    });
  }

  loadAgreements() {
    this.masterData.getAgreements(this.product.id, this.currencyB2B).subscribe(res => {
      this.agreements.set(res.data);
      this.tempAgreements = {};
      res.data.forEach(a => {
        this.tempAgreements[a.partner_id] = a.amount;
      });
    });
  }

  hasAgreement(partnerId: string): boolean {
    return this.agreements().some(a => a.partner_id === partnerId);
  }

  getSavedAgreement(partnerId: string): number | undefined {
    return this.agreements().find(a => a.partner_id === partnerId)?.amount;
  }

  saveAgreement(partner: any) {
    const amount = this.tempAgreements[partner.id];
    if (!amount) return;

    const payload = {
      product_id: this.product.id,
      partner_id: partner.id,
      amount: amount,
      currency: this.currencyB2B
    };

    this.masterData.upsertAgreement(payload).subscribe({
      next: () => {
        this.loadAgreements();
      }
    });
  }

  openAddPartnerModal() {
    this.isAddingPartner.set(true);
    setTimeout(() => {
      this.partnerModal.open(PartnerType.CUSTOMER);
    });
  }

  onPartnerSaved(partner: any) {
    this.loadPartners();
    this.isAddingPartner.set(false);
  }
  loadPrices() {
    this.masterData.getPrices(this.product.id, this.warehouseId, this.currency, this.unitType).subscribe(res => {
      this.prices.set(res.data);
      this.tempPrices = {};
      res.data.forEach(p => {
        this.tempPrices[p.price_list_index] = p.amount;
      });
    });
  }

  hasPrice(tier: number): boolean {
    return this.prices().some(p => p.price_list_index === tier);
  }

  getPriceDate(tier: number): string | undefined {
    return this.prices().find(p => p.price_list_index === tier)?.effective_date;
  }

  savePrice(tier: number) {
    const amount = this.tempPrices[tier];
    if (!amount) return;

    const payload: Partial<ProductPrice> = {
      product_id: this.product.id,
      price_list_index: tier,
      amount: amount,
      currency: this.currency,
      unit_type: this.unitType,
      warehouse_id: this.warehouseId,
      is_active: true
    };

    this.masterData.upsertPrice(payload).subscribe({
      next: () => {
        this.loadPrices();
      }
    });
  }
  getSavedPrice(tier: number): number | undefined {
    return this.prices().find(p => p.price_list_index === tier)?.amount;
  }

  getTierDescription(tier: number): string {
    const descriptions: { [key: number]: string } = {
      1: 'Público General / Retail',
      2: 'Mayorista',
      3: 'Distribuidor Autorizado',
      4: 'Transferencia Inter-Compañía',
      5: 'Contrato Gubernamental',
      6: 'Preferencial A',
      7: 'Preferencial B',
      8: 'Promoción Especial',
      9: 'Costo Base + Margen Estándar',
      10: 'Liquidación / Remate'
    };
    return descriptions[tier] || 'Personalizado';
  }

  focusNextRow(currentTier: number) {
    if (currentTier < 10) {
      setTimeout(() => {
        const nextInput = document.getElementById(`price-input-${currentTier + 1}`);
        if (nextInput) {
          nextInput.focus();
        }
      }, 50);
    }
  }

  async loadVariants() {
    try {
      const data = await this.inventoryService.getProductVariants(this.product.id);
      this.variants.set(data || []);
    } catch (err) {
      console.error('[Variants] Error loading:', err);
    }
  }

  async saveVariant() {
    if (this.variantForm.invalid) return;
    this.loadingVariants.set(true);

    const data = {
      ...this.variantForm.value,
      product_id: this.product.id,
      internal_sku: this.product.sku
    };

    try {
      await this.inventoryService.upsertVariant(data);
      this.notifications.success('Éxito', 'Variante registrada correctamente');
      this.variantForm.reset({ unit_price: 0 });
      await this.loadVariants();
    } catch (err: any) {
      this.notifications.error('Error', err?.error?.message || 'No se pudo registrar la variante');
    } finally {
      this.loadingVariants.set(false);
    }
  }

  async removeVariant(id: string) {
    if (!confirm('¿Está seguro de eliminar esta variante?')) return;
    try {
      await this.inventoryService.deleteVariant(id);
      this.notifications.success('Éxito', 'Variante eliminada');
      await this.loadVariants();
    } catch (err) {
      console.error('[Variants] Error deleting:', err);
    }
  }
}
