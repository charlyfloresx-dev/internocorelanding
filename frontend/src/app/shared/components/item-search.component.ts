import { Component, ElementRef, HostListener, Output, EventEmitter, signal, computed, effect, inject, input, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MasterDataService, ApiResponse, Product } from '../../core/services/master-data.service';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, map, tap } from 'rxjs/operators';
import { InventoryService } from '../../core/services/inventory.service';
import { ToastService } from '../../core/services/toast.service';

export interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  variant?: string;
  brand?: string;
  mfg_part_number?: string;
  available: number;
  unitWeight: number; // in kg
  unitVolume: number; // in m3
  imageUrl?: string;
  unit?: string;
  uomId?: string;
  conversions?: { unit: string; factor: number; id?: string }[];
  lastPrice?: number;
  currency?: string;
  kardex?: { type: 'IN' | 'OUT'; qty: number; date: string }[];
}

@Component({
  selector: 'app-item-search',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="relative w-full group h-full">
      <div class="relative flex items-center h-full">
        <input 
          #searchInput
          type="text" 
          [ngModel]="query()"
          (ngModelChange)="onQueryChange($event)"
          (focus)="onFocus()"
          (keydown.arrowdown)="onArrowDown($event)"
          (keydown.arrowup)="onArrowUp($event)"
          (keydown.enter)="onEnter($event)"
          (keydown.escape)="onEscape()"
          [disabled]="disabled()"
          [placeholder]="disabled() ? 'Seleccione Almacén primero' : placeholder()"
          class="w-full bg-transparent border-none pl-2 pr-2 py-2 text-xs font-mono font-bold text-surface-text outline-none transition-all placeholder:text-surface-text-muted/50 uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed"
        >
      </div>

      <!-- Glassmorphism Results Dropdown -->
      @if (isOpen() && filteredItems().length > 0) {
        <div class="absolute z-50 mt-0 w-full min-w-[400px] left-0 bg-slate-900/95 backdrop-blur-2xl border-x border-b border-primary/30 shadow-[0_20px_60px_rgba(0,0,0,0.8)] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
          <div class="max-h-80 overflow-y-auto divide-y divide-white/10 custom-scrollbar">
            @for (item of filteredItems(); track item.id; let i = $index) {
              <button 
                (click)="selectItem(item)"
                [class.bg-primary/30]="selectedIndex() === i"
                class="w-full px-4 py-3 text-left hover:bg-white/10 transition-colors flex items-center gap-4 group/item"
              >
                <div class="flex-grow min-w-0">
                  <div class="flex items-center gap-3 mb-1">
                    <span class="px-2 py-0.5 bg-primary/20 rounded-sm text-[10px] font-black text-primary tracking-widest uppercase border border-primary/30">{{ item.sku }}</span>
                    <span class="text-[11px] font-bold text-white truncate">{{ item.name }}</span>
                  </div>
                    <div class="flex flex-col gap-1">
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-black text-white tracking-widest group-hover/item:text-primary transition-colors">{{ item.sku }}</span>
                      @if (item.lastPrice === null) {
                        <span class="text-[8px] bg-red-500/20 text-red-500 border border-red-500/30 px-1.5 py-0.5 rounded font-black animate-pulse uppercase tracking-tighter">PRECIO REQUERIDO</span>
                      }
                    </div>
                    <span class="text-[10px] text-surface-text-muted font-bold truncate max-w-[200px]">{{ item.name }}</span>
                  </div>
                </div>
                
                <div class="ml-auto text-right">
                  <div class="flex flex-col items-end">
                    <span 
                      class="text-[10px] font-black tracking-tighter transition-all"
                      [class.text-red-500]="item.lastPrice === null"
                      [class.text-primary]="item.lastPrice !== null"
                    >
                      {{ item.lastPrice === null ? '--.--' : (item.lastPrice | currency: (item.currency || 'USD')) }}
                    </span>
                    <span class="text-[8px] text-surface-text-muted font-bold uppercase tracking-widest">{{ item.currency || '---' }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-1.5 ml-auto">
                  <span class="text-[8px] text-surface-text-muted uppercase font-bold">Stock:</span>
                  <span class="text-[10px] font-black" [class.text-emerald-400]="item.available > 10" [class.text-amber-400]="item.available <= 10">
                    {{ item.available }} {{ item.unit }}
                  </span>
                </div>
              </button>
            }
          </div>
          <div class="p-2 bg-slate-800/50 text-center border-t border-white/10">
            <p class="text-[7px] text-surface-text-muted font-black uppercase tracking-[0.3em]">
              SELECCIÓN RÁPIDA: ↑ ↓ • ENTER
            </p>
          </div>
        </div>
      } @else if (isOpen() && query().length >= 2) {
        <div class="absolute z-50 mt-2 w-[300px] left-0 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl p-6 text-center shadow-2xl animate-in fade-in slide-in-from-top-2 duration-200">
          <mat-icon class="text-surface-text-muted mb-2">inventory_2</mat-icon>
          <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">No se encontraron coincidencias</p>
        </div>
      }
    </div>
  `,
  styles: [`
    :host { display: block; width: 100%; }
  `]
})
export class ItemSearchComponent implements OnInit {
  @Output() itemSelected = new EventEmitter<InventoryItem>();
  @Output() arrowDownPressed = new EventEmitter<void>();
  @Output() arrowUpPressed = new EventEmitter<void>();

  disabled = input<boolean>(false);
  value = input<string>('');
  placeholder = input<string>('SKU / Material');
  warehouseId = input<string | null>(null);

  private elementRef = inject(ElementRef);
  private masterData = inject(MasterDataService);
  private inventoryService = inject(InventoryService);
  private toast = inject(ToastService);

  private allItems = signal<InventoryItem[]>([]);

  inputRef = signal<HTMLInputElement | null>(null);
  query = signal('');
  isOpen = signal(false);
  selectedIndex = signal(-1);

  private searchSubject = new Subject<string>();

  private isLoadingProducts = false;

  ngOnInit() {
    // Live Search Pipeline
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        if (q.length < 2) return of({ data: [] as Product[] } as ApiResponse<Product[]>);
        return this.masterData.getProducts(q, this.warehouseId() || undefined);
      })
    ).subscribe({
      next: (res) => {
        const mapped = res.data.map(p => ({
          id: p.id,
          sku: p.sku,
          name: p.name,
          variant: p.description,
          available: (p as any).current_stock || 0,
          unitWeight: (p as any).weight || 0,
          unitVolume: 0,
          unit: 'PZ',
          uomId: p.base_uom_id,
          lastPrice: p.last_price,
          currency: p.currency || '---'
        } as InventoryItem));
        
        if (mapped.length > 0) {
          this.allItems.set(mapped);
        }
      }
    });
  }

  private async enrichWithStock() {
    const whId = this.warehouseId();
    if (!whId) return;

    const inventory = inject(InventoryService); // Re-injecting if needed, but I'll use the class-level one.
    const currentItems = this.allItems();
    
    // We update stock for the visible items or all? 
    // For now, let's keep it simple. If the backend returned it (via join), great.
  }

  onQueryChange(value: string) {
    this.query.set(value);
    this.searchSubject.next(value);
    this.onFocus();
  }

  onFocus() {
    this.isOpen.set(true);
    if (this.allItems().length === 0 && !this.isLoadingProducts) {
      this.loadBackendProducts();
    }
  }

  private loadBackendProducts() {
    this.isLoadingProducts = true;
    this.masterData.getProducts().subscribe({
      next: (res) => {
        const mapped = res.data.map(p => ({
          id: p.id,
          sku: p.sku,
          name: p.name,
          variant: p.description,
          available: (p as any).current_stock || 0,
          unitWeight: (p as any).weight || 0,
          unitVolume: 0,
          unit: 'PZ',
          uomId: p.base_uom_id,
          lastPrice: p.last_price || 0
        } as InventoryItem));
        this.allItems.set(mapped);
        this.isLoadingProducts = false;
      },
      error: (err) => {
        console.error('[ItemSearch] Error loading from backend', err);
        this.allItems.set([]);
        this.isLoadingProducts = false;
      }
    });
  }


  filteredItems = computed(() => {
    const q = this.query().toLowerCase().trim();
    if (q.length < 2) return [];
    return this.allItems().filter(item => 
      item.sku.toLowerCase().includes(q) || 
      item.name.toLowerCase().includes(q) || 
      (item.variant && item.variant.toLowerCase().includes(q))
    ).slice(0, 8);
  });

  constructor() {
    // Industrial Guard: Reset search results if warehouse context is lost or search is disabled
    effect(() => {
      const isSearchDisabled = this.disabled();
      const whId = this.warehouseId();
      if (isSearchDisabled || !whId) {
        this.allItems.set([]);
        this.query.set('');
        this.isOpen.set(false);
      }
    });

    effect(() => {
      // Sync query with value input
      const val = this.value();
      if (val !== undefined) {
        this.query.set(val);
      }
    });

    effect(() => {
      // Reset selection when results change
      if (this.filteredItems()) {
        this.selectedIndex.set(-1);
      }
    });
  }

  @HostListener('document:click', ['$event'])
  onClickOutside(event: Event) {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }

  focus() {
    const input = this.elementRef.nativeElement.querySelector('input');
    if (input) {
      input.focus();
    }
  }


  onArrowDown(event: Event) {
    event.preventDefault();
    if (!this.isOpen()) {
      if (this.query().length >= 2) {
        this.isOpen.set(true);
      } else {
        this.arrowDownPressed.emit();
      }
      return;
    }
    const next = this.selectedIndex() + 1;
    if (next < this.filteredItems().length) {
      this.selectedIndex.set(next);
    }
  }

  onArrowUp(event: Event) {
    event.preventDefault();
    if (!this.isOpen()) {
      this.arrowUpPressed.emit();
      return;
    }
    const prev = this.selectedIndex() - 1;
    if (prev >= 0) {
      this.selectedIndex.set(prev);
    }
  }

  onEnter(event: Event) {
    event.preventDefault();
    const selected = this.filteredItems()[this.selectedIndex()];
    if (selected) {
      this.selectItem(selected);
    } else if (this.filteredItems().length > 0) {
      this.selectItem(this.filteredItems()[0]);
    }
  }

  onEscape() {
    this.isOpen.set(false);
  }

  clear() {
    this.query.set('');
    this.isOpen.set(false);
    this.selectedIndex.set(-1);
  }

  async selectItem(item: InventoryItem) {
    const whId = this.warehouseId();
    
    // Industrial Guard: If we have a warehouse, fetch REAL stock before emitting
    if (whId) {
      try {
        const stockRes = await this.inventoryService.getStock(whId, item.id);
        if (stockRes) {
          item.available = Number(stockRes.quantity || 0);
          // If price is available in stock (WAC), we could also update it here
          if (stockRes.wac && stockRes.wac.amount) {
             item.lastPrice = Number(stockRes.wac.amount);
          }
        }
      } catch (err) {
        console.error('[ItemSearch] Could not fetch stock for item:', item.sku, err);
        item.available = 0; // Safe fallback
      }
    }

    if (item.lastPrice === null) {
      this.toast.info(`El producto ${item.sku} no tiene precio registrado. Se usará 0.00 por el momento.`, 'Maestro de Datos');
    }
    
    this.query.set(item.sku);
    this.itemSelected.emit(item);
    this.isOpen.set(false);
  }
}
