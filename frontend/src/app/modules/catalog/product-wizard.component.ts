import {
  Component, inject, signal, computed, output, OnInit,
  ElementRef, ViewChildren, QueryList, AfterViewInit
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, Product, ProductPrice } from '../../core/services/master-data.service';
import { NotificationService } from '../../core/services/notification.service';
import { AuthService } from '../../core/services/auth.service';
import { InventoryService } from '../../core/services/inventory.service';

interface ProductRow {
  _id: number;           // internal row id
  sku: string;
  name: string;
  product_type: 'GOODS' | 'SERVICE';
  uom_id: string;
  price: number | null;
  category_id: string;
  sat_product_code: string;
  // physical/opening
  initial_qty: number;
  warehouse_id: string;
  // state
  status: 'idle' | 'saving' | 'saved' | 'error';
  error: string | null;
  saved_product_id: string | null;
}

let _rowCounter = 0;

function makeRow(): ProductRow {
  return {
    _id: ++_rowCounter,
    sku: '', name: '', product_type: 'GOODS',
    uom_id: '', price: null, category_id: '',
    sat_product_code: '',
    initial_qty: 0,
    warehouse_id: '',
    status: 'idle', error: null, saved_product_id: null
  };
}

@Component({
  selector: 'app-product-wizard',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="fixed inset-0 z-[120] flex flex-col bg-slate-950/98 backdrop-blur-sm"
         [class.pointer-events-none]="isBulkSaving()">

      <!-- ── Toolbar ── -->
      <div class="flex items-center gap-4 px-6 py-3 border-b border-white/5 bg-slate-900/80 flex-shrink-0">
        <div class="flex items-center gap-3">
          <mat-icon class="text-primary text-lg">table_rows</mat-icon>
          <div>
            <span class="text-xs font-black text-white uppercase tracking-widest">Alta Rápida de Productos</span>
            <span class="text-[9px] text-slate-500 font-mono ml-3">Tab = siguiente campo · Enter = nueva fila · Esc = cerrar</span>
          </div>
        </div>

        <div class="flex-1"></div>

        <!-- Stats -->
        <div class="flex items-center gap-4 text-[9px] font-mono">
          <span class="text-slate-500">{{ rows().length }} fila(s)</span>
          <span class="text-emerald-400">{{ savedCount() }} guardadas</span>
          @if (errorCount() > 0) {
            <span class="text-red-400">{{ errorCount() }} error(es)</span>
          }
        </div>

        <!-- Apertura Toggle -->
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-amber-500/20 bg-amber-500/5 group cursor-pointer transition-all hover:bg-amber-500/10"
             (click)="isAperturaChecked.set(!isAperturaChecked())">
          <mat-icon class="text-sm" [class.text-amber-500]="isAperturaChecked()" [class.text-slate-600]="!isAperturaChecked()">
            {{ isAperturaChecked() ? 'check_box' : 'check_box_outline_blank' }}
          </mat-icon>
          <span class="text-[9px] font-black uppercase tracking-widest" [class.text-amber-200]="isAperturaChecked()" [class.text-slate-500]="!isAperturaChecked()">
            Apertura Express
          </span>
        </div>

        <button (click)="addRow()"
                class="flex items-center gap-2 px-4 py-2 border border-white/10 hover:border-primary/50 rounded-lg text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-primary transition-all">
          <mat-icon class="text-sm">add</mat-icon>
          Fila
        </button>

        <button (click)="saveAll()"
                [disabled]="isBulkSaving() || !hasPendingRows()"
                class="flex items-center gap-2 px-5 py-2 bg-primary text-slate-950 rounded-lg text-[10px] font-black uppercase tracking-widest hover:opacity-90 transition-all disabled:opacity-30">
          @if (isBulkSaving()) {
            <mat-icon class="text-sm animate-spin">sync</mat-icon>
            <span>Guardando...</span>
          } @else {
            <mat-icon class="text-sm">save</mat-icon>
            <span>Guardar Todo</span>
          }
        </button>

        <button (click)="closePanel()"
                class="p-2 text-slate-500 hover:text-white transition-colors rounded-lg hover:bg-white/5">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <!-- ── Column Headers ── -->
      <div class="flex-shrink-0 bg-slate-900 border-b border-white/5">
        <div class="grid text-[9px] font-black text-slate-500 uppercase tracking-widest px-3 py-2"
             [style.grid-template-columns]="gridCols()">
          <div class="pl-3">#</div>
          <div>SKU <span class="text-red-400">*</span></div>
          <div>Nombre <span class="text-red-400">*</span></div>
          <div>Tipo</div>
          <div>UOM <span class="text-red-400">*</span></div>
          <div>Precio ({{ activeCurrency() }})</div>
          <div>Categoría</div>
          <div>Cód. SAT</div>
          @if (isAperturaChecked()) {
            <div class="text-amber-400">Almacén</div>
            <div class="text-amber-400">Cant. Ini</div>
          }
          <div class="text-center">Estado</div>
          <div></div>
        </div>
      </div>

      <!-- ── Rows ── -->
      <div class="flex-1 overflow-y-auto" #scrollArea>
        @for (row of rows(); track row._id; let i = $index) {
          <div class="grid border-b border-white/5 group transition-all"
               [style.grid-template-columns]="gridCols()"
               [class.bg-emerald-950/20]="row.status === 'saved'"
               [class.bg-red-950/20]="row.status === 'error'"
               [class.bg-white/3]="row.status === 'idle' || row.status === 'saving'"
               [class.opacity-70]="row.status === 'saving'">

            <!-- Row Number -->
            <div class="flex items-center px-4 py-2 text-[9px] font-mono text-slate-600">
              {{ i + 1 }}
            </div>

            <!-- SKU -->
            <div class="flex items-center px-1 py-1">
              <input [(ngModel)]="row.sku"
                     (keydown)="onKeyDown($event, i, 'sku')"
                     [disabled]="row.status === 'saved' || row.status === 'saving'"
                     class="cell-input font-mono text-primary"
                     [class.border-red-500/50]="row.error && !row.sku"
                     placeholder="MAT-001">
            </div>

            <!-- Name -->
            <div class="flex items-center px-1 py-1">
              <input [(ngModel)]="row.name"
                     (keydown)="onKeyDown($event, i, 'name')"
                     [disabled]="row.status === 'saved' || row.status === 'saving'"
                     class="cell-input"
                     [class.border-red-500/50]="row.error && !row.name"
                     placeholder="Nombre del producto">
            </div>

            <!-- Type -->
            <div class="flex items-center px-1 py-1">
              <select [(ngModel)]="row.product_type"
                      [disabled]="row.status === 'saved' || row.status === 'saving'"
                      class="cell-input cursor-pointer">
                <option value="GOODS">Bien</option>
                <option value="SERVICE">Servicio</option>
              </select>
            </div>

            <!-- UOM -->
            <div class="flex items-center px-1 py-1">
              <select [(ngModel)]="row.uom_id"
                      [disabled]="row.status === 'saved' || row.status === 'saving'"
                      class="cell-input cursor-pointer"
                      [class.border-red-500/50]="row.error && !row.uom_id">
                <option value="">UOM…</option>
                @for (u of masterData.uoms(); track u.id) {
                  <option [value]="u.id">{{ u.abbreviation }}</option>
                }
              </select>
            </div>

            <!-- Price -->
            <div class="flex items-center px-1 py-1">
              <input [(ngModel)]="row.price"
                     (keydown)="onKeyDown($event, i, 'price')"
                     [disabled]="row.status === 'saved' || row.status === 'saving'"
                     type="number" min="0" step="0.01"
                     class="cell-input font-mono text-emerald-400"
                     placeholder="0.00">
            </div>

            <!-- Category -->
            <div class="flex items-center px-1 py-1">
              <select [(ngModel)]="row.category_id"
                      [disabled]="row.status === 'saved' || row.status === 'saving'"
                      class="cell-input cursor-pointer">
                <option value="">—</option>
                @for (c of masterData.categories(); track c.id) {
                  <option [value]="c.id">{{ c.name }}</option>
                }
              </select>
            </div>

            <!-- SAT Code -->
            <div class="flex items-center px-1 py-1">
              <input [(ngModel)]="row.sat_product_code"
                     (keydown)="onKeyDown($event, i, 'sat')"
                     [disabled]="row.status === 'saved' || row.status === 'saving'"
                     class="cell-input font-mono text-xs text-blue-300"
                     placeholder="00000000" maxlength="8">
            </div>

            <!-- Apertura Fields (Optional) -->
            @if (isAperturaChecked()) {
              <div class="flex items-center px-1 py-1">
                <select [(ngModel)]="row.warehouse_id"
                        [disabled]="row.status === 'saved' || row.status === 'saving'"
                        class="cell-input border-amber-500/20 text-amber-200 cursor-pointer">
                  <option value="">Almacén…</option>
                  @for (w of masterData.warehouses(); track w.id) {
                    <option [value]="w.id">{{ w.code }}-{{ w.name }}</option>
                  }
                </select>
              </div>
              <div class="flex items-center px-1 py-1">
                <input [(ngModel)]="row.initial_qty"
                       type="number" min="0"
                       [disabled]="row.status === 'saved' || row.status === 'saving'"
                       class="cell-input font-mono text-amber-500 text-center"
                       placeholder="0">
              </div>
            }

            <!-- Status -->
            <div class="flex items-center justify-center px-2 py-1">
              @switch (row.status) {
                @case ('saved') {
                  <span class="flex items-center gap-1 text-[9px] font-black text-emerald-400">
                    <mat-icon class="text-xs w-3 h-3">check_circle</mat-icon>
                    OK
                  </span>
                }
                @case ('error') {
                  <span class="flex items-center gap-1 text-[9px] font-black text-red-400"
                        [title]="row.error || ''">
                    <mat-icon class="text-xs w-3 h-3">error</mat-icon>
                    Error
                  </span>
                }
                @case ('saving') {
                  <mat-icon class="text-sm text-primary animate-spin">sync</mat-icon>
                }
                @default {
                  <span class="text-[9px] text-slate-600 font-mono">—</span>
                }
              }
            </div>

            <!-- Row Actions -->
            <div class="flex items-center justify-center gap-1 pr-2 opacity-0 group-hover:opacity-100 transition-all">
              @if (row.status !== 'saved' && row.status !== 'saving') {
                <button (click)="saveRow(i)"
                        [disabled]="!isRowValid(row)"
                        class="p-1.5 rounded hover:bg-emerald-500/10 text-emerald-500 disabled:opacity-20 transition-all"
                        title="Guardar esta fila">
                  <mat-icon class="text-xs" style="font-size:14px;width:14px;height:14px;">save</mat-icon>
                </button>
                <button (click)="removeRow(i)"
                        class="p-1.5 rounded hover:bg-red-500/10 text-red-400 transition-all"
                        title="Eliminar fila">
                  <mat-icon class="text-xs" style="font-size:14px;width:14px;height:14px;">delete</mat-icon>
                </button>
              }
              @if (row.status === 'error') {
                <button (click)="retryRow(i)"
                        class="p-1.5 rounded hover:bg-amber-500/10 text-amber-400 transition-all"
                        title="Reintentar">
                  <mat-icon class="text-xs" style="font-size:14px;width:14px;height:14px;">refresh</mat-icon>
                </button>
              }
            </div>
          </div>
        }

        <!-- ── Add Row Button (inline) ── -->
        <div class="border-b border-white/5">
          <button (click)="addRow()"
                  class="w-full text-left px-6 py-3 text-[10px] font-mono text-slate-600 hover:text-primary hover:bg-white/3 transition-all flex items-center gap-3">
            <mat-icon class="text-sm">add</mat-icon>
            Agregar fila (o presiona Enter en la última celda)
          </button>
        </div>
      </div>

      <!-- ── Bottom Status Bar ── -->
      <div class="flex-shrink-0 flex items-center gap-4 px-6 py-2 border-t border-white/5 bg-slate-900/60 text-[9px] font-mono text-slate-500">
        <span>{{ rows().length }} producto(s) en lista</span>
        <span>·</span>
        <span class="text-emerald-500">{{ savedCount() }} guardados</span>
        @if (errorCount() > 0) {
          <span>·</span>
          <span class="text-red-400">{{ errorCount() }} con error</span>
        }
        <div class="flex-1"></div>
        <span>Moneda activa: <strong class="text-white">{{ activeCurrency() }}</strong></span>
        <span>·</span>
        <span>Empresa: <strong class="text-white">{{ activeCompanyName() }}</strong></span>
      </div>
    </div>
  `,
  styles: [`
    :host { display: contents; }
    .cell-input {
      width: 100%;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 4px;
      padding: 5px 8px;
      font-size: 11px;
      font-weight: 600;
      color: #e2e8f0;
      outline: none;
      transition: border-color 0.1s, background 0.1s;
    }
    .cell-input:focus {
      border-color: rgba(56, 189, 248, 0.5);
      background: rgba(56, 189, 248, 0.05);
    }
    .cell-input:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .cell-input option {
      background: #0f172a;
      color: #e2e8f0;
    }
    select.cell-input {
      appearance: none;
      cursor: pointer;
    }
  `]
})
export class ProductWizardComponent implements OnInit {
  masterData  = inject(MasterDataService);
  private notifications = inject(NotificationService);
  private auth = inject(AuthService);
  private inventory = inject(InventoryService);

  onSaved  = output<Product>();
  onClosed = output<void>();

  rows       = signal<ProductRow[]>([makeRow(), makeRow(), makeRow()]);
  isBulkSaving = signal(false);
  isAperturaChecked = signal(false);

  gridCols = computed(() => 
    this.isAperturaChecked() 
      ? '40px 140px 1fr 90px 90px 110px 130px 100px 120px 80px 70px 70px'
      : '40px 140px 1fr 90px 90px 110px 130px 100px 70px 70px'
  );

  savedCount  = computed(() => this.rows().filter(r => r.status === 'saved').length);
  errorCount  = computed(() => this.rows().filter(r => r.status === 'error').length);
  hasPendingRows = computed(() => this.rows().some(r => r.status === 'idle' && this.isRowValid(r)));

  activeCurrency = computed(() => {
    const name = (this.auth.session() as any)?.company_name || '';
    return name.toLowerCase().includes('usa') || name.toLowerCase().includes('california') ? 'USD' : 'MXN';
  });

  activeCompanyName = computed(() =>
    (this.auth.session() as any)?.company_name || 'Empresa Activa'
  );

  ngOnInit() {
    if (!this.masterData.uoms().length) {
      this.masterData.refreshCatalogs();
    }
  }

  open() {
    this.rows.set([makeRow(), makeRow(), makeRow()]);
    this.isBulkSaving.set(false);
  }

  closePanel() {
    if (this.savedCount() > 0) this.onSaved.emit({} as Product);
    this.onClosed.emit();
  }

  addRow() {
    this.rows.update(r => [...r, makeRow()]);
    // Scroll + focus after DOM update
    setTimeout(() => {
      const inputs = document.querySelectorAll<HTMLInputElement>('.cell-input[placeholder="MAT-001"]');
      if (inputs.length) inputs[inputs.length - 1].focus();
    }, 50);
  }

  removeRow(i: number) {
    this.rows.update(r => r.filter((_, idx) => idx !== i));
    if (this.rows().length === 0) this.addRow();
  }

  isRowValid(row: ProductRow): boolean {
    return !!(row.sku.trim() && row.name.trim() && row.uom_id);
  }

  onKeyDown(e: KeyboardEvent, rowIndex: number, field: string) {
    if (e.key === 'Enter') {
      e.preventDefault();
      // If last row, add a new one
      if (rowIndex === this.rows().length - 1) {
        this.addRow();
      } else {
        // Focus first cell of next row
        this.focusCell(rowIndex + 1, 0);
      }
    }
    if (e.key === 'Escape') {
      this.closePanel();
    }
  }

  private focusCell(rowIndex: number, colIndex: number) {
    setTimeout(() => {
      const allRows = document.querySelectorAll<HTMLElement>('[style*="grid-template-columns"]');
      const targetRow = allRows[rowIndex + 1]; // +1 because header is first
      if (targetRow) {
        const inputs = targetRow.querySelectorAll<HTMLElement>('input, select');
        if (inputs[colIndex]) inputs[colIndex].focus();
      }
    }, 20);
  }

  async saveRow(i: number) {
    const rows = this.rows();
    const row  = rows[i];
    if (!this.isRowValid(row)) return;

    row.status = 'saving';
    row.error  = null;
    this.rows.set([...rows]);

    try {
      const payload: any = {
        sku:          row.sku.trim(),
        name:         row.name.trim(),
        product_type: row.product_type,
        uom_id:       row.uom_id,
        category_id:  row.category_id || null,
        sat_product_code: row.sat_product_code?.trim() || null,
        is_taxable:   true,
        allow_price_override: true,
      };

      const res = await this.masterData.createProduct(payload).toPromise();
      if (!res || res.status !== 'success') throw new Error('Error del servidor');

      const productId = res.data.id;
      row.saved_product_id = productId;

      // Save price if defined
      if (row.price && row.price > 0) {
        const pricePayload: Partial<ProductPrice> = {
          product_id:       productId,
          price_list_index: 1,
          amount:           row.price,
          currency:         this.activeCurrency(),
          unit_type:        'SALE',
          warehouse_id:     null,
          is_active:        true,
        };
        await this.masterData.upsertPrice(pricePayload).toPromise();
      }

      // Step 3: Express Opening (Internal Inventory)
      if (this.isAperturaChecked() && row.initial_qty > 0 && row.warehouse_id) {
        await this.inventory.createOpeningBalance(
          productId,
          row.warehouse_id,
          row.initial_qty,
          row.uom_id
        );
      }

      row.status = 'saved';
      this.notifications.success('Guardado', row.sku);
    } catch (err: any) {
      row.status = 'error';
      row.error  = err?.error?.detail || err?.message || 'Error desconocido';
      this.notifications.error('Error', `SKU: ${row.sku} — ${row.error}`);
    }

    this.rows.set([...this.rows()]);
  }

  retryRow(i: number) {
    const rows = [...this.rows()];
    rows[i].status = 'idle';
    rows[i].error  = null;
    this.rows.set(rows);
    this.saveRow(i);
  }

  async saveAll() {
    this.isBulkSaving.set(true);
    const pendingIndices = this.rows()
      .map((r, i) => ({ r, i }))
      .filter(({ r }) => r.status === 'idle' && this.isRowValid(r))
      .map(({ i }) => i);

    for (const i of pendingIndices) {
      await this.saveRow(i);
    }

    this.isBulkSaving.set(false);

    if (this.savedCount() > 0 && this.errorCount() === 0) {
      this.notifications.success('Alta completada', `${this.savedCount()} producto(s) guardados`);
    }
  }
}
