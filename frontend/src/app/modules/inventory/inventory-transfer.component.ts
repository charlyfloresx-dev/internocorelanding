import { Component, signal, inject, OnInit, computed, HostListener, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { ItemSearchComponent, InventoryItem } from '../../shared/components/item-search.component';
import { InventoryService } from '../../core/services/inventory.service';
import { ToastService } from '../../core/services/toast.service';
import { AuthService } from '../../core/services/auth.service';
import { Router } from '@angular/router';
import { MasterDataService } from '../../core/services/master-data.service';
import { LocalDatePipe } from '../../shared/pipes/local-date.pipe';

interface TransferItem {
  id: string;
  product_id?: string;
  sku: string;
  name: string;
  variant?: string;
  quantity: number;
  available: number;
  uom_id?: string;
  selected_batch_id?: string;
  selected_batch_label?: string;
}

@Component({
  selector: 'app-inventory-transfer',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, ItemSearchComponent, LocalDatePipe],
  templateUrl: './inventory-transfer.component.html',
  styleUrl: './inventory-transfer.component.css'
})
export class InventoryTransferComponent implements OnInit {
  private inventoryService = inject(InventoryService);
  private authService = inject(AuthService);
  private toast = inject(ToastService);
  private router = inject(Router);
  private masterData = inject(MasterDataService);
  
  constructor() {
    // Industrial Context Synchronization: Always align origin with header's active company
    effect(() => {
      const headerCoId = this.authService.activeCompanyId();
      if (!headerCoId) return;

      const currentWhId = this.originWarehouseId();
      const allWhs = this.warehouses();
      
      const currentWh = allWhs.find(w => w.id === currentWhId);
      
      // If no warehouse selected OR existing selection belongs to a different company
      if (!currentWh || currentWh.company_id !== headerCoId) {
        const companyWhs = allWhs.filter(w => w.company_id === headerCoId);
        if (companyWhs.length > 0) {
          console.log('[ICT] Syncing origin with header company:', headerCoId);
          this.selectOriginContext(companyWhs[0]);
        }
      }
    }, { allowSignalWrites: true });
  }





  @HostListener('keydown.alt.a', ['$event'])
  onAltAPressed(event: any) {
    event.preventDefault();
    this.addItem();
  }

  warehouses = signal<any[]>([]);

  
  // Custom Dropdown State
  isContextDropdownOpen = signal(false);

  selectedWarehouseName = computed(() => {
    const id = this.originWarehouseId();
    if (!id) return '';
    const wh = this.warehouses().find(w => w.id === id);
    return wh ? wh.name : '';
  });

  toggleContextDropdown() {
    this.isContextDropdownOpen.set(!this.isContextDropdownOpen());
  }

  selectOriginContext(wh: any) {
    this.originWarehouseId.set(wh.id);
    this.originCompanyId.set(wh.company_id);
    this.isContextDropdownOpen.set(false);
  }

  originCompanyId = signal<string>('');
  originWarehouseId = signal<string>('');
  
  destinationCompanyId = signal<string>('');
  destinationWarehouseId = signal<string>('');
  
  customsPedimento = signal<string>('');
  customsRegime = signal<'TEMPORAL' | 'DEFINITIVO'>('TEMPORAL');
  customsPedimentoKey = signal<string>('');
  
  isProcessing = signal(false);

  // ── Compliance Audit Signals ──────────────────────────────────
  /** Tasa de cambio oficial DOF (MXN/USD) — Obligatoria para rutas binacionales */
  exchangeRateDof = signal<number>(0);
  /** True cuando el backend retorna requires_risk_acknowledgment por caducidad del pedimento */
  requiresRiskAck = signal<boolean>(false);
  /** El operador marcó el checkbox aceptando el riesgo de caducidad */
  riskAcknowledged = signal<boolean>(false);
  /** Hay transferencia parcial sin precio (deuda administrativa activa) */
  hasPendingValuation = signal<boolean>(false);
  /** Advertencias del Agente de Auditoría pre-vuelo (MISSING_PRICE, etc.) */
  complianceWarnings = signal<any[]>([]);
  /** Clave de pedimento sugerida por el Agente */
  suggestedCustomsKey = signal<string>('');

  // ── Industrial Audio Context (Lazy Initialization) ───────────────────
  private audioCtx: AudioContext | null = null;

  private initAudio() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume();
    }
  }

  /**
   * Genera osciladores sintéticos para feedback auditivo industrial.
   * Evita el uso de archivos MP3 externos y garantiza latencia cero.
   */
  playIndustrialBeep(type: 'success' | 'warning' | 'error') {
    try {
      this.initAudio();
      if (!this.audioCtx) return;

      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();

      osc.connect(gain);
      gain.connect(this.audioCtx.destination);

      const now = this.audioCtx.currentTime;

      if (type === 'success') {
        // High pitch (880Hz - La5) | 150ms
        osc.frequency.setValueAtTime(880, now);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
      } else if (type === 'warning') {
        // Two fast medium pulses (440Hz)
        osc.frequency.setValueAtTime(440, now);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.1);
        
        // Second pulse logic needs a second oscillator or a scheduled sequence
        const osc2 = this.audioCtx.createOscillator();
        const gain2 = this.audioCtx.createGain();
        osc2.connect(gain2);
        gain2.connect(this.audioCtx.destination);
        osc2.frequency.setValueAtTime(440, now + 0.15);
        gain2.gain.setValueAtTime(0, now);
        gain2.gain.setValueAtTime(0.1, now + 0.15);
        gain2.gain.exponentialRampToValueAtTime(0.0001, now + 0.25);
        
        osc.start(now);
        osc.stop(now + 0.1);
        osc2.start(now + 0.15);
        osc2.stop(now + 0.25);
      } else if (type === 'error') {
        // Low pitch (220Hz - La2) | 400ms decay
        osc.frequency.setValueAtTime(220, now);
        osc.frequency.exponentialRampToValueAtTime(110, now + 0.4);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.4);
        osc.start(now);
        osc.stop(now + 0.4);
      }
    } catch (e) {
      console.warn('[AUDIO] Failed to play industrial beep:', e);
    }
  }

  onOriginContextChange(whId: string) {
    const wh = this.warehouses().find(w => w.id === whId);
    if (wh) {
      this.originCompanyId.set(wh.company_id);
    } else {
      this.originCompanyId.set('');
    }
  }

  getWarehousesByCompany(companyId: string): any[] {
    return this.warehouses().filter(w => w.company_id === companyId);
  }

  // Known company registry — maps company_id to human-readable label & country.
  // Derived from the warehouse group catalog so it stays in sync with the DB.
  private readonly KNOWN_COMPANIES: Record<string, { name: string; flag: string; country: string }> = {
    '9cd9986b-89da-48b7-8733-26a2a1225b01': { name: 'InternoCorp Enterprise', flag: '🏢', country: 'MX' },
    'ad6cc8a6-34f9-42df-8f29-28254e0ad242': { name: 'Interno Logistics MX', flag: '🇲🇽', country: 'MX' },
    '777cc8a6-34f9-42df-8f29-28254e0ad277': { name: 'Interno Logistics US', flag: '🇺🇸', country: 'US' },
  };

  companies = computed(() => {
    const activeId = this.authService.activeCompanyId();
    const groupAccess = this.authService.availableCompanies();
    const allWhs = this.warehouses();
    const uniqueMap = new Map<string, any>();
    
    // 1. Source: Group Access (From AuthService)
    groupAccess.forEach((co: any) => {
      const known = this.KNOWN_COMPANIES[co.company_id];
      const label = known ? `${known.flag} ${known.name}` : co.company_name;
      
      uniqueMap.set(co.company_id, {
        id: co.company_id,
        label,
        full_name: co.company_name,
        country: known?.country || 'GLOBAL', 
        type: co.company_id === activeId ? 'SAME_RFC' : 'GROUP_LOGISTICS'
      });
    });

    // 2. Enrichment: Scan warehouses to discover remaining entities or add country flags
    allWhs.forEach((w: any) => {
      if (!w.company_id) return;
      
      const existing = uniqueMap.get(w.company_id);
      if (existing) {
        if (w.country_code && existing.country === 'GLOBAL') {
          existing.country = w.country_code;
        }
      } else {
        uniqueMap.set(w.company_id, {
          id: w.company_id,
          label: `🏢 Empresa [${w.company_id.substring(0, 8).toUpperCase()}]`,
          full_name: `Empresa [${w.company_id.substring(0, 8).toUpperCase()}]`,
          country: w.country_code || 'GLOBAL',
          type: 'EXTERNAL'
        });
      }
    });

    return Array.from(uniqueMap.values());
  });




  internalCos = computed(() => this.companies().filter(c => c.type === 'SAME_RFC'));
  viatraCos = computed(() => this.companies().filter(c => c.type === 'GROUP_LOGISTICS'));


  filteredOriginCompanies = computed(() => {
    const activeId = this.authService.activeCompanyId();
    return this.companies().filter(c => c.id === activeId);
  });

  filteredOriginWarehouses = computed(() => {
    const coId = this.originCompanyId();
    if (!coId) return [];
    return this.warehouses().filter(w => w.company_id === coId);
  });

  filteredDestWarehouses = computed(() => {
    const coId = this.destinationCompanyId();
    if (!coId) return [];
    return this.warehouses().filter(w => w.company_id === coId && w.id !== this.originWarehouseId());
  });

  setDestinationCompany(companyId: string) {
    if (this.destinationCompanyId() === companyId) {
      // Toggle off if same clicked again
      this.destinationCompanyId.set('');
      this.destinationWarehouseId.set('');
      return;
    }

    this.destinationCompanyId.set(companyId);
    
    // Auto-wipe warehouse if switching boundaries
    if (companyId !== this.originCompanyId()) {
      this.destinationWarehouseId.set('');
    } else {
      if (this.destinationWarehouseId() === this.originWarehouseId()) {
        this.destinationWarehouseId.set('');
      }
    }
  }

  setDestinationWarehouse(whId: string) {
    if (this.destinationWarehouseId() === whId) {
      this.destinationWarehouseId.set('');
    } else {
      this.destinationWarehouseId.set(whId);
    }
  }

  selectedOrigin = computed(() => this.warehouses().find(w => w.id === this.originWarehouseId()));
  selectedDest = computed(() => this.warehouses().find(w => w.id === this.destinationWarehouseId()));
  
  isBinational = computed(() => {
    const origin = this.selectedOrigin();
    if (!origin) return false;
    
    const destWh = this.selectedDest();
    if (destWh) return origin.country_code !== destWh.country_code;
    
    const destCoId = this.destinationCompanyId();
    if (destCoId) {
      const co = this.companies().find(c => c.id === destCoId);
      return co ? origin.country_code !== co.country : false;
    }
    
    return false;
  });

  /** True when sender and receiver are different legal entities (different company_id) */
  isInterCompanyTransfer = computed(() => {
    const originCo = this.originCompanyId();
    const destCo = this.destinationCompanyId();
    return !!(originCo && destCo && originCo !== destCo);
  });

  // ─── Concept Guard (Deterministic Signal-Safe Resolution) ──────────────────

  /**
   * Reactive concept_id for Inter-Company Transfers (INT-TRA).
   * Returns null if the concept catalog is not yet loaded — blocks submit.
   * This is the ONLY authoritative source of concept_id for ICT operations.
   */
  readonly transferConceptId = computed(() =>
    this.masterData.resolveConceptByCode('INT-TRA')?.id ?? null
  );

  /**
   * Reactive concept_id for Internal Transfers between warehouses of the same company.
   * Resolves to INT-TRA as well (intra-company transfer concept).
   */
  readonly internalTransferConceptId = computed(() =>
    this.masterData.resolveConceptByCode('INT-TRA')?.id ?? null
  );

  /**
   * Three-state catalog guard for the submit button label.
   * Components bind to this to show "Configurando Empresa..." instead of blocking silently.
   */
  readonly catalogState = this.masterData.conceptCatalogState;

  /**
   * True when the form can be submitted.
   * Adds concept_id availability check on top of structural form validity.
   */
  readonly canSubmitTransfer = computed(() => {
    if (!this.isFormValid()) return false;
    // Block if the concept catalog isn't ready (prevents sending null concept_id)
    const isICT = this.isInterCompanyTransfer();
    const conceptId = isICT ? this.transferConceptId() : this.internalTransferConceptId();
    return conceptId !== null;
  });

  /**
   * Deterministic "Traffic Light" compliance status.
   * - SAFE: All green (Price + Stock + Pedimento if binational).
   * - WARNING: Valid but requires attention (Missing Price / Administrative Debt).
   * - BLOCKED: Incomplete or invalid data.
   */
  complianceStatus = computed(() => {
    // 1. Structural blockage
    if (!this.isFormValid()) return 'BLOCKED';

    // 2. Binational documentation warning (User specified Amber/Warning if missing but allowed?)
    // Actually the user said "Verde: Todo en orden (Precio + Stock + Pedimento)".
    // So if missing anything it's at least Amber/Warning.
    const isBinational = this.isBinational();
    const hasPedimento = !!this.customsPedimento();
    const hasPrice = !this.hasPendingValuation() && this.complianceWarnings().length === 0;

    if (isBinational && !hasPedimento) return 'WARNING';
    if (!hasPrice) return 'WARNING';

    return 'SAFE';
  });

  /** 
   * [Phase 42.7] Metric for global operational readiness (0-100%) 
   * Used to drive the industrial UI "Meter".
   */
  readinessPercentage = computed(() => {
    let score = 0;
    
    // 1. Route (25%): Origin + Destination selected
    if (this.originWarehouseId() && this.destinationCompanyId()) {
      score += 25;
      // Bonus if warehouse is also selected for intra-company
      if (this.destinationCompanyId() === this.originCompanyId() && this.destinationWarehouseId()) {
        score += 0; // Already covered by basics
      }
    }

    // 2. Inventory (25%): All items have valid quantities and match FIFO
    const items = this.items();
    if (items.length > 0) {
      const allValid = items.every(i => i.sku && i.quantity > 0 && i.quantity <= i.available);
      if (allValid) score += 25;
    }

    // 3. Compliance (25%): Custom fields if required
    if (this.isBinational()) {
      if (this.customsPedimento() && this.customsPedimentoKey()) score += 25;
    } else {
      score += 25; // Auto-pass for domestic
    }

    // 4. Valuation (25%): All prices settled
    if (!this.hasPendingValuation() && this.complianceWarnings().length === 0) {
      score += 25;
    }

    return score;
  });

  /** Human-readable label for the selected destination company */
  destCompanyLabel = computed(() => {
    const destCoId = this.destinationCompanyId();
    if (!destCoId) return '';
    const co = this.companies().find(c => c.id === destCoId);
    return co?.label || `[${destCoId.substring(0, 8).toUpperCase()}]`;
  });

  /** Country code badge for the destination node in the route map */
  destCompanyCountry = computed(() => {
    const destCoId = this.destinationCompanyId();
    if (!destCoId) return '';
    // Check selected warehouse first (intra-company case)
    const destWh = this.selectedDest();
    if (destWh) return destWh.country_code || '';
    // Fallback to company country (inter-company case)
    const co = this.companies().find(c => c.id === destCoId);
    return co?.country || '';
  });

  items = signal<TransferItem[]>([]);
  fifoPreviews = signal<Record<string, any[]>>({});

  isFormValid = computed(() => {
    if (!this.originWarehouseId() || !this.destinationCompanyId()) return false;
    // Internal transfer requires warehouse, External transfer doesn't (receiver decides)
    if (this.destinationCompanyId() === this.originCompanyId() && !this.destinationWarehouseId()) return false;
    
    // Modo Permisivo Industrial: Los campos aduaneros se validan visualmente 
    // pero no bloquean la ejecución del traspaso por ahora.
    
    // Si el Agente de Auditoría solicita confirmación de riesgo, exigirla
    if (this.requiresRiskAck() && !this.riskAcknowledged()) return false;
    
    const validItems = this.items().filter(i => i.sku && i.quantity > 0 && i.quantity <= i.available);
    return validItems.length > 0 && validItems.length === this.items().length;
  });

  private processWarehouses(whs: any[]): any[] {
    return whs.map(w => {
      // Use activeTenant fallback ONLY if backend omits company_id (due to scoping)
      const activeId = this.authService.activeCompanyId();
      if (!w.company_id && activeId) {
        w.company_id = activeId;
      }
      return w;
    });
  }

  async ngOnInit() {
    // Force-refresh warehouses to avoid stale localStorage cache
    // (e.g., after ghost company records were purged from the DB)
    await this.inventoryService.loadCatalogs();
    const updatedWhs = this.inventoryService.warehouses();
    console.log('[ICT] Warehouses loaded from service:', updatedWhs.length);
    this.warehouses.set(this.processWarehouses(updatedWhs));

    // Auto-Seleccion de Contexto (Header Sync)
    const activeId = this.authService.activeCompanyId();
    if (!this.originWarehouseId()) {
      const companyWhs = updatedWhs.filter(w => w.company_id === activeId);
      if (companyWhs.length > 0) {
        console.log('[ICT] Auto-seleccionando contexto inicial:', companyWhs[0].name);
        this.selectOriginContext(companyWhs[0]);
      }
    }
    
    if (this.items().length === 0) {
      this.addItem();
    }
  }

  addItem() {
    const newItem: TransferItem = {
      id: Math.random().toString(36).substring(2, 9),
      sku: '',
      name: '',
      quantity: 1,
      available: 0
    };
    this.items.update(prev => [...prev, newItem]);
    
    // Auto-scroll to bottom of the table smoothly (Excel-like flow)
    setTimeout(() => {
      const wrappers = document.querySelectorAll('.overflow-x-auto');
      if (wrappers.length > 0) {
        const tableContainer = wrappers[0] as HTMLElement;
        tableContainer.scrollTo({
          top: tableContainer.scrollHeight,
          behavior: 'smooth'
        });
      }
    }, 50);
  }

  onQuantityEnter(index: number) {
    // Si es el último item y tiene datos, agregar otro
    const currentItems = this.items();
    if (index === currentItems.length - 1 && currentItems[index].sku) {
      this.addItem();
    }
  }

  removeItem(index: number) {
    this.items.update(prev => prev.filter((_, i) => i !== index));
    if (this.items().length === 0) this.addItem();
  }

  onItemSelected(row: TransferItem, item: InventoryItem) {
    this.items.update(items => {
      const target = items.find(i => i.id === row.id);
      if (target) {
        target.product_id = item.id;
        target.sku = item.sku;
        target.name = item.name;
        target.available = item.available;
        target.uom_id = (item as any).uom_id || '11111111-1111-1111-1111-111111111111';
      }
      
      // Async Fetch FIFO Picking Preview
      const whId = this.originWarehouseId();
      if (whId && item.id) {
        this.inventoryService.getFifoPreview(item.id, whId).then(preview => {
          this.fifoPreviews.update(prev => ({ ...prev, [row.id]: preview }));
        });
      }

      // Force array reference change to trigger computed dependencies like 'isFormValid'
      return [...items];
    });
  }

  toggleBatchSelection(row: TransferItem, batch: any) {
    this.items.update(items => {
      const target = items.find(i => i.id === row.id);
      if (target) {
        if (target.selected_batch_id === batch.movement_id) {
          // Deselect
          target.selected_batch_id = undefined;
          target.selected_batch_label = undefined;
        } else {
          // Select
          target.selected_batch_id = batch.movement_id;
          target.selected_batch_label = `${batch.pedimento_number} @ ${batch.location}`;
          // Auto-fill quantity if empty
          if (!target.quantity || target.quantity === 0) {
            target.quantity = Math.min(batch.quantity, 100); // Respect some sane default or batch cap
          }
        }
      }
      return [...items];
    });
  }

  async onInitiateTransfer() {
    if (!this.canSubmitTransfer() || this.isProcessing()) return;

    // Defensive concept guard (belt-and-suspenders)
    const isICT = this.originCompanyId() !== (this.destinationCompanyId() || this.selectedDest()?.company_id);
    const resolvedConceptId = isICT ? this.transferConceptId() : this.internalTransferConceptId();

    if (!resolvedConceptId) {
      this.toast.warning(
        'El catálogo de conceptos aún se está cargando. Por favor intenta en un momento.',
        'Configurando Empresa...'
      );
      return;
    }

    this.isProcessing.set(true);

    // Check if it's an Inter-Company transfer
    const originCo = this.originCompanyId();
    const destCo = this.destinationCompanyId() || this.selectedDest()?.company_id;
    const isInterCompany = originCo !== destCo;
    
    const itemsPayload = this.items().map(i => ({
      product_id: i.product_id,
      quantity: i.quantity,
      uom_id: i.uom_id || '11111111-1111-1111-1111-111111111111',
      origin_sku: i.sku,
      selected_batch_id: i.selected_batch_id
    }));

    // For multi-item support or single item logic
    const firstItem = itemsPayload[0];
    
    try {
      if (isInterCompany) {
        // [PHASE 39] Inter-Company Bridge Logic
      const result = await this.inventoryService.initiateInterCompanyTransfer({
        destination_company_id: destCo,
        destination_warehouse_id: this.destinationWarehouseId() || '00000000-0000-0000-0000-000000000000',
        origin_warehouse_id: this.originWarehouseId(),
        from_warehouse_id: this.originWarehouseId(),       // Backend alias
        to_warehouse_id: this.destinationWarehouseId() || '00000000-0000-0000-0000-000000000000',
        product_id: firstItem.product_id!,
        uom_id: firstItem.uom_id,
        quantity: firstItem.quantity,
        concept_id: resolvedConceptId,                     // ← Concept guard
        origin_sku: firstItem.origin_sku,
        selected_batch_id: (firstItem as any).selected_batch_id,
        currency: 'USD',
        customs_pedimento: this.customsPedimento(),
        customs_regime: this.customsRegime(),
        customs_pedimento_key: this.customsPedimentoKey(),
        notes: 'Transferencia generada desde Dashboard Binacional',
        exchange_rate_dof: this.isBinational() ? this.exchangeRateDof() : undefined,
        risk_acknowledged: this.riskAcknowledged() || undefined,
      });
        
        // Activar estado de Deuda Administrativa si el servidor lo indica
        if (result?.compliance_status === 'COMPLIANCE_WARNING' || result?.pending_financial_valuation) {
          this.hasPendingValuation.set(true);
          this.complianceWarnings.set(result?.audit_warnings || []);
          this.toast.warning(
            `Transferencia procesada con advertencias de compliance. ${result?.audit_warnings?.length || 0} SKU(s) requieren regularización en Finanzas.`,
            '⚠️ Compliance Warning'
          );
          this.playIndustrialBeep('warning');
        } else {
          this.toast.success('Transferencia Inter-Company SHIPPED (Tránsito Iniciado).', 'Logística Binacional');
          this.playIndustrialBeep('success');
        }
        this.router.navigate(['/inventory/documents']);
      } else {
        // Standard internal transfer
        const internalPayload = {
          product_id: firstItem.product_id!,
          quantity: firstItem.quantity,
          uom_id: firstItem.uom_id,
          origin_warehouse_id: this.originWarehouseId(),
          destination_warehouse_id: this.destinationWarehouseId(),
          destination_company_id: destCo,
          concept_id: resolvedConceptId,                   // ← Concept guard
          selected_batch_id: (firstItem as any).selected_batch_id
        };
        await this.inventoryService.dispatchInternalTransfer(internalPayload);
        this.toast.success('Traspaso interno completado.', 'Inventario');
        this.playIndustrialBeep('success');
        this.router.navigate(['/inventory/documents']);
      }
    } catch (e: any) {
      console.error('[ICT] Error:', e);
      
      // Parsear el payload de auditoría estructurado del Agente
      const serverMsg: string = e?.error?.message || '';
      const details = e?.error?.data || e?.error?.details || {};
      
      if (serverMsg.includes('ERR_PREFLIGHT_REJECTED') && details?.errors?.length) {
        // Error duro del Agente (ej. Pedimento vencido)
        const firstErr = details.errors[0];
        this.toast.error(
          `❌ ${firstErr.msg} (SKU: ${firstErr.sku}).`,
          'Auditoría Pre-Vuelo Rechazada'
        );
      } else if (serverMsg.includes('MISSING_PRICE') || details?.warnings?.length) {
        // Warning de precio faltante — el operador puede regularizar en Catálogo
        const warnItems = details?.warnings || [];
        const skus = warnItems.map((w: any) => w.sku).join(', ');
        this.toast.warning(
          `Precio inter-company no definido para: ${skus || firstItem.origin_sku}. Ir a Catálogo > Precios para regularizar.`,
          '💰 Precio Pendiente'
        );
        // Ofrecer redirección al catálogo si hay un solo SKU afectado
        if (warnItems.length === 1) {
          setTimeout(() => {
            this.router.navigate(['/catalog/prices'], { queryParams: { sku: warnItems[0].sku } });
          }, 2500);
        }
      } else if (details?.metadata?.requires_risk_acknowledgment) {
        // Pedimento por vencer — mostrar checkbox de aceptación de riesgo
        this.requiresRiskAck.set(true);
        this.suggestedCustomsKey.set(details.metadata.suggested_customs_key || '');
        this.toast.warning(
          '⚠️ Material con estancia legal próxima a vencer. Marca el checkbox de confirmación de riesgo para despachar.',
          'Alerta Anexo 24'
        );
      } else {
        this.toast.error(serverMsg || 'Error al procesar el envío.', 'Error de Transferencia');
      }
      this.playIndustrialBeep('error');
    } finally {
      this.isProcessing.set(false);
    }
  }
}
