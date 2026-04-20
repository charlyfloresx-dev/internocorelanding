// temp_future/src/app/modules/inventory/components/document-header/document-header.component.ts
import { Component, Input, Output, EventEmitter, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConceptType } from '../../../../core/models/domain.types';
import { InventoryService } from '../../../../core/services/inventory.service';

@Component({
  selector: 'app-document-header',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="industrial-card p-8 border-l-4" [ngClass]="headerBorder()">
      <div class="flex flex-col md:flex-row justify-between items-start gap-8">
        <!-- Type Selection -->
        <div class="space-y-4 min-w-[250px]">
          <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">Tipo de Transacción</label>
          <div class="flex gap-2">
            <button *ngFor="let type of types" 
                    (click)="selectType(type)"
                    [class.active-type]="activeType === type"
                    class="type-btn">
              {{ typeLabels[type] || type }}
            </button>
          </div>
        </div>

        <!-- Concept & Warehouse -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full">
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Concepto</label>
            <select [(ngModel)]="conceptId" (change)="onConceptChange()"
                    class="w-full bg-slate-800/50 border border-white/10 rounded-xl p-3 text-white focus:border-cyan-500 outline-none appearance-none cursor-pointer">
              <option value="" disabled>Seleccionar Concepto...</option>
              <option *ngFor="let c of filteredConcepts()" [value]="c.id">{{ c.name }}</option>
            </select>
          </div>

          <div class="space-y-2">
            <label class="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Almacén Origen</label>
            <select [(ngModel)]="warehouseId" (change)="emitHeader()"
                    class="w-full bg-slate-800/50 border border-white/10 rounded-xl p-3 text-white focus:border-cyan-500 outline-none">
              <option value="" disabled>Seleccionar Almacén...</option>
              <option *ngFor="let w of service.warehouses()" [value]="w.id">{{ w.name }}</option>
            </select>
          </div>

          <div *ngIf="requiresTarget()" class="space-y-2 animate-in fade-in duration-500">
            <label class="text-[10px] font-bold text-amber-500 uppercase tracking-widest">Almacén Destino</label>
            <select [(ngModel)]="targetWarehouseId" (change)="emitHeader()"
                    class="w-full bg-slate-800/20 border border-amber-500/30 rounded-xl p-3 text-white focus:border-amber-500 outline-none">
              <option value="" disabled>Seleccionar Destino...</option>
              <option *ngFor="let w of filteredTargetWarehouses()" [value]="w.id">{{ w.name }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="mt-8">
        <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2">Notas / Referencia de Documento</label>
        <textarea [(ngModel)]="notes" (input)="emitHeader()"
                  class="w-full bg-slate-900/50 border border-white/5 rounded-xl p-4 text-xs text-slate-300 h-20 outline-none focus:border-cyan-500/30 transition-all"
                  placeholder="Detalle de la operación o referencia interna..."></textarea>
      </div>
    </div>
  `
})
export class DocumentHeaderComponent {
  public service = inject(InventoryService);

  @Output() headerChanged = new EventEmitter<any>();

  activeType: ConceptType = ConceptType.ENTRY;
  conceptId = '';
  warehouseId = '';
  targetWarehouseId = '';
  notes = '';

  types = [ConceptType.ENTRY, ConceptType.OUTPUT, ConceptType.TRANSFER, ConceptType.ADJUSTMENT];

  typeLabels: Record<string, string> = {
    [ConceptType.ENTRY]: 'Entrada',
    [ConceptType.OUTPUT]: 'Salida',
    [ConceptType.TRANSFER]: 'Traspaso',
    [ConceptType.ADJUSTMENT]: 'Ajuste'
  };

  headerBorder = computed(() => {
    switch (this.activeType) {
      case ConceptType.ENTRY: return 'border-emerald-500';
      case ConceptType.OUTPUT: return 'border-red-500';
      case ConceptType.TRANSFER: return 'border-amber-500';
      default: return 'border-cyan-500';
    }
  });

  filteredConcepts = computed(() => {
    const raw = (this.service.concepts() || []) as any[];
    return raw.filter(c => {
      const cType = String(c.type || '').toUpperCase();
      const aType = String(this.activeType || '').toUpperCase();
      return cType === aType;
    });
  });

  requiresTarget = computed(() => {
    const rawConcepts = (this.service.concepts() || []) as any[];
    const concept = rawConcepts.find(c => c.id === this.conceptId);
    return concept?.requires_target_warehouse || this.activeType === ConceptType.TRANSFER;
  });

  filteredTargetWarehouses = computed(() => {
    const rawWarehouses = (this.service.warehouses() || []) as any[];
    return rawWarehouses.filter(w => w.id !== this.warehouseId);
  });

  selectType(type: ConceptType) {
    this.activeType = type;
    this.conceptId = '';
    this.emitHeader();
  }

  onConceptChange() {
    this.emitHeader();
  }

  emitHeader() {
    this.headerChanged.emit({
      concept_type: this.activeType,
      concept_id: this.conceptId,
      warehouse_id: this.warehouseId,
      destination_warehouse_id: this.targetWarehouseId,
      notes: this.notes
    });
  }
}
