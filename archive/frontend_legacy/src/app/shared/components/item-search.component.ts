import { Component, ElementRef, HostListener, Output, EventEmitter, signal, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { QrScannerComponent } from './qr-scanner.component';
import { InventoryService } from '../../core/services/inventory.service';
import { Subject, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap, catchError, takeUntil } from 'rxjs/operators';

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
  conversions?: { unit: string; factor: number }[];
  kardex?: { type: 'IN' | 'OUT'; qty: number; date: string }[];
}

@Component({
  selector: 'app-item-search',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, QrScannerComponent],
  template: `
    <div class="relative w-full group">
      <div class="relative flex items-center">
        <mat-icon class="absolute left-2.5 text-surface-text-muted text-[14px] group-focus-within:text-primary transition-colors h-4 w-4">search</mat-icon>
        <input 
          #searchInput
          type="text" 
          [ngModel]="query()"
          (ngModelChange)="query.set($event); onFocus()"
          (focus)="onFocus()"
          (keydown.arrowdown)="onArrowDown($event)"
          (keydown.arrowup)="onArrowUp($event)"
          (keydown.enter)="onEnter($event)"
          (keydown.escape)="onEscape()"
          placeholder="SKU / Material"
          class="w-full bg-surface-bg/50 border border-surface-border rounded-lg pl-8 pr-12 py-1.5 text-xs font-mono font-bold text-surface-text outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all placeholder:text-surface-text-muted/50 uppercase tracking-widest"
        >
        <!-- QR SCAN BUTTON -->
        <button (click)="isScannerOpen.set(true)" 
                class="absolute right-2 p-1.5 text-surface-text-muted hover:text-primary hover:bg-primary/10 rounded transition-all group/qr"
                title="Escanear Código QR">
          <mat-icon class="text-[16px] h-4 w-4">qr_code_scanner</mat-icon>
        </button>
      </div>

      <!-- QR SCANNER MODAL -->
      @if (isScannerOpen()) {
        <app-qr-scanner 
          (scanSuccess)="onQrScanned($event)" 
          (close)="isScannerOpen.set(false)">
        </app-qr-scanner>
      }

      <!-- Glassmorphism Results Dropdown -->
      @if (isOpen() && filteredItems().length > 0) {
        <div class="absolute z-50 mt-2 w-[500px] left-0 bg-slate-900/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          <div class="max-h-80 overflow-y-auto divide-y divide-white/5 custom-scrollbar">
            @for (item of filteredItems(); track item.id; let i = $index) {
              <button 
                (click)="selectItem(item)"
                [ngClass]="{'bg-primary/20': selectedIndex() === i}"
                class="w-full px-5 py-4 text-left hover:bg-white/5 transition-colors flex items-center gap-4 group/item"
              >
                <!-- Item Icon/Thumbnail Placeholder -->
                <div class="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex-shrink-0 overflow-hidden">
                  <img [src]="item.imageUrl || 'https://picsum.photos/seed/' + item.sku + '/100/100'" [alt]="item.name" class="w-full h-full object-cover opacity-60 group-hover/item:opacity-100 transition-opacity" referrerpolicy="no-referrer">
                </div>

                <div class="flex-grow min-w-0">
                  <div class="flex items-center justify-between mb-0.5">
                    <span class="text-[10px] font-black text-primary tracking-widest uppercase">{{ item.sku }}</span>
                    <div class="flex items-center gap-1.5">
                      <span class="text-[8px] text-surface-text-muted uppercase font-bold">Stock</span>
                      <span class="text-[11px] font-black" [class.text-emerald-400]="item.available > 10" [class.text-amber-400]="item.available <= 10">
                        {{ item.available }}
                      </span>
                    </div>
                  </div>
                  <h4 class="text-xs font-bold text-white truncate">{{ item.name }}</h4>
                  <div class="flex items-center gap-2 mt-1.5">
                    @if (item.variant) {
                      <span class="text-[9px] text-surface-text-muted uppercase tracking-tighter italic">{{ item.variant }}</span>
                    }
                    @if (item.brand) {
                      <div class="h-3 w-[1px] bg-white/10"></div>
                      <span class="px-1.5 py-0.5 bg-white/10 rounded text-[7px] font-black text-surface-text-muted uppercase tracking-tighter">
                        {{ item.brand }} | {{ item.mfg_part_number }}
                      </span>
                    }
                  </div>
                </div>
              </button>
            }
          </div>
          <div class="p-2.5 bg-white/5 text-center border-t border-white/5">
            <p class="text-[8px] text-surface-text-muted font-bold uppercase tracking-[0.2em]">
              Usa ↑ ↓ para navegar • Enter para seleccionar
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
export class ItemSearchComponent {
  @Output() itemSelected = new EventEmitter<InventoryItem>();
  @Output() arrowDownPressed = new EventEmitter<void>();
  @Output() arrowUpPressed = new EventEmitter<void>();

  private elementRef = inject(ElementRef);
  private inventoryService = inject(InventoryService);

  inputRef = signal<HTMLInputElement | null>(null);
  query = signal('');
  isOpen = signal(false);
  isScannerOpen = signal(false);
  selectedIndex = signal(-1);
  loading = signal(false);
  results = signal<InventoryItem[]>([]);

  private searchSubject = new Subject<string>();

  filteredItems = computed(() => this.results());

  constructor() {
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => {
        if (q.length < 2) {
          this.results.set([]);
          this.loading.set(false);
          return of({ data: [] });
        }
        this.loading.set(true);
        return this.inventoryService.searchItems(q).pipe(
          catchError(() => {
            this.loading.set(false);
            return of({ data: [] });
          })
        );
      })
    ).subscribe((res: any) => {
      const items = (res.data || []).map((item: any) => ({
        id: item.variant_id || item.id,
        sku: item.sku_maestro || item.sku,
        name: item.display_name || item.name,
        variant: item.variant_name || item.warehouse_name,
        brand: item.brand,
        mfg_part_number: item.mfg_part_number,
        available: item.quantity || item.current_stock || 0,
        unitWeight: item.weight || 0,
        unitVolume: item.volume || 0,
        imageUrl: `https://picsum.photos/seed/${item.sku_maestro || item.sku}/100/100`
      }));
      this.results.set(items);
      this.loading.set(false);
    });

    effect(() => {
      // Trigger RxJS stream
      this.searchSubject.next(this.query().toLowerCase().trim());

      // Reset selection when results change
      if (this.filteredItems()) {
        this.selectedIndex.set(-1);
      }
    }, { allowSignalWrites: true });
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

  onFocus() {
    if (this.query().length >= 2) {
      this.isOpen.set(true);
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

  selectItem(item: InventoryItem) {
    this.query.set(item.sku);
    this.itemSelected.emit(item);
    this.isOpen.set(false);
  }

  onQrScanned(data: string) {
    this.isScannerOpen.set(false);
    // Some scanners might include prefix or full URL, we extract potential SKU
    let sku = data.trim();
    if (sku.includes('=')) {
      sku = sku.split('=').pop() || sku;
    }

    this.query.set(sku);

    // After setting the query, the RxJS observable will trigger the search.
    // If the exact match comes back, the user can select it from the dropdown.
      // If not found, at least we leave the SKU in the search box
      this.isOpen.set(true);
    }
  }
}
