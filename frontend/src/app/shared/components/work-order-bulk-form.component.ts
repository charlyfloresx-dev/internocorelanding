import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { environment } from '../../../environments/environment';

const CSV_HEADER = 'order_number,item_code,order_qty,due_date,alias,wo_type';
const CSV_EXAMPLE = [
  'OT-2026-001,TURBO-SKU-A,100,2026-06-30T00:00:00Z,Lote Verano,STANDARD',
  'OT-2026-002,BRAKE-SKU-B,50,2026-07-15T00:00:00Z,,STANDARD',
  'OT-2026-003,INJECT-001,200,2026-07-20T00:00:00Z,Prioridad Alta,',
].join('\n');

interface WORow {
  order_number: string;
  item_code: string;
  order_qty: number;
  due_date: string;
  alias: string | null;
  wo_type: string | null;
}

interface BulkResult {
  created: number;
  skipped: number;
  errors: { row: number; order_number: string; error: string }[];
}

@Component({
  selector: 'app-work-order-bulk-form',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-amber-500/10 rounded-2xl flex items-center justify-center text-amber-400 border border-amber-500/20">
            <mat-icon class="text-2xl">upload_file</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              Importar Órdenes de Trabajo
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              CARGA MASIVA DESDE CSV
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-5">

        <!-- Step 1 -->
        <div class="p-5 bg-surface-card rounded-2xl border border-surface-border space-y-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-primary/10 rounded-xl flex items-center justify-center text-primary text-sm font-black">1</div>
            <h3 class="text-xs font-black text-surface-text uppercase tracking-widest">Descargar Plantilla</h3>
          </div>
          <div class="bg-surface-bg rounded-xl p-3 font-mono text-[10px] text-amber-400 border border-surface-border overflow-x-auto">
            <pre>{{ templatePreview }}</pre>
          </div>
          <p class="text-[10px] text-surface-text-muted">
            Campos: <code class="text-primary">due_date</code> en ISO 8601. <code class="text-primary">wo_type</code>: STANDARD, REPAIR, REWORK, TEST, TOOLING (vacío = STANDARD). Duplicados (mismo order_number) se omiten.
          </p>
          <button
            (click)="downloadTemplate()"
            class="w-full py-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2"
          >
            <mat-icon class="text-sm">download</mat-icon>
            Descargar plantilla_ordenes.csv
          </button>
        </div>

        <!-- Step 2 -->
        <div class="p-5 bg-surface-card rounded-2xl border border-surface-border space-y-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-primary/10 rounded-xl flex items-center justify-center text-primary text-sm font-black">2</div>
            <h3 class="text-xs font-black text-surface-text uppercase tracking-widest">Seleccionar Archivo</h3>
          </div>
          <label
            class="flex flex-col items-center justify-center w-full h-28 border-2 border-dashed border-surface-border rounded-2xl cursor-pointer hover:border-primary/40 transition-all group"
            [class.border-primary]="selectedFile()"
          >
            <mat-icon class="text-2xl text-surface-text-muted group-hover:text-primary transition-colors mb-2">
              {{ selectedFile() ? 'check_circle' : 'cloud_upload' }}
            </mat-icon>
            <span class="text-[10px] font-bold text-surface-text-muted group-hover:text-primary transition-colors">
              {{ selectedFile() ? selectedFile()!.name : 'Haz clic o arrastra el archivo CSV aquí' }}
            </span>
            <input type="file" accept=".csv,text/csv" class="hidden" (change)="onFileSelected($event)" />
          </label>
        </div>

        @if (parseError()) {
          <div class="p-4 bg-rose-500/10 rounded-xl border border-rose-500/20">
            <div class="flex items-center gap-2 text-rose-400 mb-1">
              <mat-icon class="text-sm">error</mat-icon>
              <span class="text-[10px] font-black uppercase">Error de formato</span>
            </div>
            <p class="text-[11px] text-rose-300">{{ parseError() }}</p>
          </div>
        }

        @if (parsedRows().length > 0 && !parseError()) {
          <div class="p-4 bg-amber-500/10 rounded-xl border border-amber-500/20">
            <div class="flex items-center gap-2 text-amber-400 mb-3">
              <mat-icon class="text-sm">table_view</mat-icon>
              <span class="text-[10px] font-black uppercase">{{ parsedRows().length }} OTs listas para importar</span>
            </div>
            <div class="max-h-40 overflow-y-auto space-y-1">
              @for (row of parsedRows(); track row.order_number) {
                <div class="flex items-center gap-3 py-1">
                  <span class="text-[10px] font-mono text-primary font-bold w-28 truncate">{{ row.order_number }}</span>
                  <span class="text-[10px] font-mono text-surface-text-muted w-24 truncate">{{ row.item_code }}</span>
                  <span class="text-[10px] text-surface-text">× {{ row.order_qty }}</span>
                </div>
              }
            </div>
          </div>
        }

        @if (result()) {
          <div class="p-5 bg-surface-card rounded-2xl border border-surface-border space-y-3">
            <h3 class="text-[10px] font-black text-surface-text uppercase tracking-widest">Resultado de Importación</h3>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                <div class="text-2xl font-black text-emerald-400">{{ result()!.created }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Creadas</div>
              </div>
              <div class="text-center p-3 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <div class="text-2xl font-black text-amber-400">{{ result()!.skipped }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Omitidas</div>
              </div>
              <div class="text-center p-3 bg-rose-500/10 rounded-xl border border-rose-500/20">
                <div class="text-2xl font-black text-rose-400">{{ result()!.errors.length }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Errores</div>
              </div>
            </div>
            @if (result()!.errors.length > 0) {
              <div class="max-h-32 overflow-y-auto space-y-1">
                @for (e of result()!.errors; track e.row) {
                  <p class="text-[10px] text-rose-400 font-mono">Fila {{ e.row }} ({{ e.order_number }}): {{ e.error }}</p>
                }
              </div>
            }
          </div>
        }

      </div>

      <!-- Footer -->
      <div class="pt-6 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button
            (click)="upload()"
            [disabled]="!selectedFile() || parsedRows().length === 0 || uploading() || !!parseError()"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic disabled:opacity-50 disabled:pointer-events-none"
          >
            <mat-icon>{{ uploading() ? 'sync' : 'cloud_upload' }}</mat-icon>
            <span>{{ uploading() ? 'Importando...' : 'Importar ' + parsedRows().length + ' órdenes' }}</span>
          </button>
          <button
            type="button"
            (click)="drawer.close()"
            class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all"
          >
            {{ result() ? 'Cerrar' : 'Cancelar' }}
          </button>
        </div>
      </div>

    </div>
  `,
  styles: [`:host { display: block; }`]
})
export class WorkOrderBulkFormComponent {
  private http  = inject(HttpClient);
  private notif = inject(NotificationService);
  drawer        = inject(SideDrawerService);

  private base = `${environment.productionUrl}/mes/orders`;
  templatePreview = `${CSV_HEADER}\n${CSV_EXAMPLE}`;

  selectedFile = signal<File | null>(null);
  parsedRows   = signal<WORow[]>([]);
  parseError   = signal<string | null>(null);
  uploading    = signal(false);
  result       = signal<BulkResult | null>(null);

  downloadTemplate(): void {
    const content = `${CSV_HEADER}\n${CSV_EXAMPLE}`;
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'plantilla_ordenes.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  onFileSelected(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0] ?? null;
    this.selectedFile.set(file);
    this.parseError.set(null);
    this.parsedRows.set([]);
    this.result.set(null);
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const rows = this.parseCsv((e.target as FileReader).result as string);
        this.parsedRows.set(rows);
      } catch (err: any) {
        this.parseError.set(err.message ?? 'Formato CSV inválido');
      }
    };
    reader.readAsText(file, 'UTF-8');
  }

  private parseCsv(text: string): WORow[] {
    const lines = text.trim().split(/\r?\n/).filter(l => l.trim());
    if (lines.length < 2) throw new Error('El archivo debe tener encabezado y al menos una fila');

    const header = lines[0].split(',').map(h => h.trim().toLowerCase());
    const col = (name: string) => header.indexOf(name);

    const orderIdx = col('order_number');
    const itemIdx  = col('item_code');
    const qtyIdx   = col('order_qty');
    const dateIdx  = col('due_date');

    if (orderIdx < 0 || itemIdx < 0 || qtyIdx < 0 || dateIdx < 0) {
      throw new Error('El CSV debe tener columnas: order_number, item_code, order_qty, due_date');
    }

    return lines.slice(1).map((line, i) => {
      const c = line.split(',').map(s => s.trim());
      const order_number = c[orderIdx];
      const item_code    = c[itemIdx];
      const qty          = parseInt(c[qtyIdx], 10);
      const due_date     = c[dateIdx];

      if (!order_number) throw new Error(`Fila ${i + 2}: order_number es obligatorio`);
      if (!item_code)    throw new Error(`Fila ${i + 2}: item_code es obligatorio`);
      if (isNaN(qty) || qty < 1) throw new Error(`Fila ${i + 2}: order_qty debe ser un entero ≥ 1`);
      if (!due_date)     throw new Error(`Fila ${i + 2}: due_date es obligatorio (ISO 8601)`);

      const aliasIdx  = col('alias');
      const typeIdx   = col('wo_type');
      return {
        order_number,
        item_code,
        order_qty: qty,
        due_date,
        alias:   aliasIdx >= 0 && c[aliasIdx] ? c[aliasIdx] : null,
        wo_type: typeIdx  >= 0 && c[typeIdx]  ? c[typeIdx]  : null,
      };
    });
  }

  async upload(): Promise<void> {
    if (this.parsedRows().length === 0) return;
    this.uploading.set(true);
    try {
      const res = await firstValueFrom(
        this.http.post<BulkResult>(`${this.base}/bulk`, this.parsedRows())
      );
      this.result.set(res);
      if (res.created > 0) {
        this.notif.success('Importación completa', `${res.created} OTs creadas`);
        this.drawer.notifyRefresh();
      }
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'Error en la importación');
    } finally {
      this.uploading.set(false);
    }
  }
}
