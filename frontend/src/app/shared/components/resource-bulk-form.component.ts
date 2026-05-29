import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { ResourceService } from '../../core/services/resource.service';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { ResourceCreate } from '../../core/models/mes.types';

const CSV_TEMPLATE_HEADER = 'code,name,resource_type,capacity,description';
const CSV_TEMPLATE_EXAMPLE = [
  'CELDA-01,Celda de Ensamble 01,CELL,240,Línea de ensamble principal',
  'TURRET-02,Torno CNC TURRET-02,MACHINE,180,',
  'PRESS-03,Prensa Hidráulica 03,MACHINE,120,',
  'LINEA-A,Línea de Producción A,LINE,300,',
].join('\n');

@Component({
  selector: 'app-resource-bulk-form',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-400 border border-emerald-500/20">
            <mat-icon class="text-2xl">upload_file</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              Carga Masiva
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              IMPORTAR RECURSOS DESDE CSV
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-6">

        <!-- Step 1: Download template -->
        <div class="p-5 bg-surface-card rounded-2xl border border-surface-border space-y-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-primary/10 rounded-xl flex items-center justify-center text-primary text-sm font-black">1</div>
            <h3 class="text-xs font-black text-surface-text uppercase tracking-widest">Descargar Plantilla</h3>
          </div>
          <p class="text-[11px] text-surface-text-muted leading-relaxed">
            Descarga el template CSV, llena los recursos y súbelo en el paso 2.
          </p>
          <div class="bg-surface-bg rounded-xl p-3 font-mono text-[10px] text-emerald-400 border border-surface-border overflow-x-auto">
            <pre>{{ csvTemplatePreview }}</pre>
          </div>
          <button
            (click)="downloadTemplate()"
            class="w-full py-3 bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2"
          >
            <mat-icon class="text-sm">download</mat-icon>
            Descargar plantilla_recursos.csv
          </button>
        </div>

        <!-- Step 2: Upload CSV -->
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

        <!-- Preview / parse errors -->
        @if (parseError()) {
          <div class="p-4 bg-rose-500/10 rounded-xl border border-rose-500/20">
            <div class="flex items-center gap-2 text-rose-400 mb-2">
              <mat-icon class="text-sm">error</mat-icon>
              <span class="text-[10px] font-black uppercase tracking-widest">Error de formato</span>
            </div>
            <p class="text-[11px] text-rose-300">{{ parseError() }}</p>
          </div>
        }

        @if (parsedRows().length > 0 && !parseError()) {
          <div class="p-4 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
            <div class="flex items-center gap-2 text-emerald-400 mb-3">
              <mat-icon class="text-sm">table_view</mat-icon>
              <span class="text-[10px] font-black uppercase tracking-widest">{{ parsedRows().length }} filas listas para importar</span>
            </div>
            <div class="max-h-40 overflow-y-auto space-y-1">
              @for (row of parsedRows(); track row.code) {
                <div class="flex items-center gap-3 py-1">
                  <span class="text-[10px] font-mono text-primary font-bold w-24 truncate">{{ row.code }}</span>
                  <span class="text-[10px] text-surface-text truncate">{{ row.name }}</span>
                  <span class="text-[9px] text-surface-text-muted font-mono">{{ row.resource_type }}</span>
                </div>
              }
            </div>
          </div>
        }

        <!-- Upload results -->
        @if (result()) {
          <div class="p-5 bg-surface-card rounded-2xl border border-surface-border space-y-3">
            <h3 class="text-[10px] font-black text-surface-text uppercase tracking-widest">Resultado de Importación</h3>
            <div class="grid grid-cols-3 gap-3">
              <div class="text-center p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20">
                <div class="text-2xl font-black text-emerald-400">{{ result()!.created }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Creados</div>
              </div>
              <div class="text-center p-3 bg-amber-500/10 rounded-xl border border-amber-500/20">
                <div class="text-2xl font-black text-amber-400">{{ result()!.skipped }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Omitidos</div>
              </div>
              <div class="text-center p-3 bg-rose-500/10 rounded-xl border border-rose-500/20">
                <div class="text-2xl font-black text-rose-400">{{ result()!.errors.length }}</div>
                <div class="text-[9px] text-surface-text-muted uppercase">Errores</div>
              </div>
            </div>
            @if (result()!.errors.length > 0) {
              <div class="max-h-32 overflow-y-auto space-y-1">
                @for (e of result()!.errors; track e.row) {
                  <p class="text-[10px] text-rose-400 font-mono">Fila {{ e.row }} ({{ e.code }}): {{ e.message }}</p>
                }
              </div>
            }
          </div>
        }

      </div>

      <!-- Footer -->
      <div class="pt-8 mt-auto border-t border-surface-border">
        <div class="flex flex-col gap-3">
          <button
            (click)="upload()"
            [disabled]="!selectedFile() || parsedRows().length === 0 || uploading() || !!parseError()"
            class="w-full py-5 bg-primary text-slate-950 rounded-2xl text-[11px] font-black uppercase tracking-[0.3em] shadow-xl shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-4 italic disabled:opacity-50 disabled:pointer-events-none"
          >
            <mat-icon>{{ uploading() ? 'sync' : 'cloud_upload' }}</mat-icon>
            <span>{{ uploading() ? 'Importando...' : 'Importar ' + parsedRows().length + ' recursos' }}</span>
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
export class ResourceBulkFormComponent {
  private svc   = inject(ResourceService);
  private notif = inject(NotificationService);
  drawer        = inject(SideDrawerService);

  csvTemplatePreview = `${CSV_TEMPLATE_HEADER}\n${CSV_TEMPLATE_EXAMPLE}`;

  selectedFile = signal<File | null>(null);
  parsedRows   = signal<ResourceCreate[]>([]);
  parseError   = signal<string | null>(null);
  uploading    = signal(false);
  result       = signal<{ created: number; skipped: number; errors: any[] } | null>(null);

  downloadTemplate() {
    const content = `${CSV_TEMPLATE_HEADER}\n${CSV_TEMPLATE_EXAMPLE}`;
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'plantilla_recursos.csv';
    link.click();
    URL.revokeObjectURL(url);
  }

  onFileSelected(event: Event) {
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

  private parseCsv(text: string): ResourceCreate[] {
    const lines = text.trim().split(/\r?\n/).filter(l => l.trim());
    if (lines.length < 2) throw new Error('El archivo debe tener encabezado y al menos una fila de datos');

    const header = lines[0].split(',').map(h => h.trim().toLowerCase());
    const codeIdx = header.indexOf('code');
    const nameIdx = header.indexOf('name');
    const typeIdx = header.indexOf('resource_type');
    const capIdx  = header.indexOf('capacity');
    const descIdx = header.indexOf('description');

    if (codeIdx < 0 || nameIdx < 0) {
      throw new Error('El CSV debe tener columnas "code" y "name"');
    }

    return lines.slice(1).map((line, i) => {
      const cols = line.split(',').map(c => c.trim());
      const code = cols[codeIdx];
      const name = cols[nameIdx];
      if (!code || !name) throw new Error(`Fila ${i + 2}: code y name son obligatorios`);

      const resource_type = typeIdx >= 0 ? (cols[typeIdx] || null) as any : null;
      const capacity = capIdx >= 0 && cols[capIdx] ? Number(cols[capIdx]) : null;
      const description = descIdx >= 0 ? (cols[descIdx] || null) : null;

      return { code, name, resource_type, capacity, description } as ResourceCreate;
    });
  }

  async upload() {
    if (this.parsedRows().length === 0) return;
    this.uploading.set(true);
    try {
      const res = await this.svc.bulkCreateResources(this.parsedRows());
      this.result.set(res);
      if (res.created > 0) {
        this.notif.success('Importación completa', `${res.created} recursos creados`);
        this.drawer.notifyRefresh();
      }
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'Error en la importación');
    } finally {
      this.uploading.set(false);
    }
  }
}
