import { Component, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MesConfigService, AddScanPatternCommand } from '../../../core/services/mes-config.service';

@Component({
  selector: 'app-mes-item-config',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in">

      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-white tracking-tight">Configuración de Ítem — MES</h1>
          <p class="text-slate-400">Patrones de validación de escaneo por código de ítem</p>
        </div>
        <span class="px-3 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20 text-xs font-bold uppercase tracking-wider">
          <i class="fa-solid fa-barcode mr-1"></i> Scan Config
        </span>
      </div>

      <!-- ─── QUERY PANEL ─────────────────────────────────────────────────── -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-sky-500 to-violet-500"></div>

        <h3 class="text-white font-bold mb-4 flex items-center gap-2">
          <i class="fa-solid fa-magnifying-glass text-sky-400"></i>
          Consultar Patrones por Ítem
        </h3>

        <!-- SKU input -->
        <div class="flex gap-3 mb-6">
          <input
            [(ngModel)]="searchInput"
            (keydown.enter)="runQuery()"
            placeholder="Código de ítem (SKU)"
            class="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-colors font-mono"
          />
          <button
            (click)="runQuery()"
            [disabled]="svc.queryLoading() || !searchInput.trim()"
            class="px-6 py-3 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white font-bold rounded-xl transition-colors flex items-center gap-2"
          >
            @if (svc.queryLoading()) {
              <i class="fa-solid fa-spinner fa-spin"></i>
            } @else {
              <i class="fa-solid fa-search"></i>
            }
            Consultar
          </button>
        </div>

        <!-- Error state -->
        @if (svc.queryError()) {
          <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm mb-4">
            <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ svc.queryError() }}
          </div>
        }

        <!-- Pattern list -->
        @if (svc.queriedItemCode()) {
          <div class="space-y-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-slate-400 text-sm">
                Ítem: <span class="text-white font-mono font-bold">{{ svc.queriedItemCode() }}</span>
              </span>
              <span class="text-xs text-slate-500">{{ svc.patterns().length }} patrón(es) activo(s)</span>
            </div>

            @if (svc.patterns().length === 0 && !svc.queryLoading()) {
              <div class="text-center py-8 text-slate-600">
                <i class="fa-solid fa-check-circle text-2xl mb-2"></i>
                <p class="text-sm">Sin patrones de validación. El escaneo acepta cualquier código.</p>
              </div>
            }

            @for (p of svc.patterns(); track p.id) {
              <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-start justify-between gap-4 group hover:border-slate-600 transition-colors">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-xs font-bold text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded">
                      #{{ p.priority }} {{ p.pattern_name }}
                    </span>
                  </div>
                  <code class="block text-sky-300 text-sm font-mono truncate mb-1">{{ p.regex }}</code>
                  <p class="text-slate-400 text-xs">{{ p.error_message }}</p>
                </div>
                <button
                  (click)="remove(p.id)"
                  [disabled]="svc.commandBusy()"
                  title="Desactivar patrón"
                  class="shrink-0 p-2 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-40"
                >
                  <i class="fa-solid fa-trash-can text-sm"></i>
                </button>
              </div>
            }
          </div>
        }
      </div>

      <!-- ─── COMMAND PANEL ────────────────────────────────────────────────── -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-violet-500 to-pink-500"></div>

        <h3 class="text-white font-bold mb-4 flex items-center gap-2">
          <i class="fa-solid fa-plus text-violet-400"></i>
          Agregar Patrón de Validación
        </h3>

        @if (svc.commandError()) {
          <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm mb-4 flex items-center justify-between">
            <span><i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ svc.commandError() }}</span>
            <button (click)="svc.clearCommandError()" class="text-slate-500 hover:text-white ml-4">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
        }

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Item code (auto-fill from query) -->
          <div class="md:col-span-2">
            <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Código de Ítem</label>
            <input
              [(ngModel)]="form.item_code"
              placeholder="SKU del producto"
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors font-mono"
            />
          </div>

          <!-- Pattern name -->
          <div>
            <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Nombre del Patrón</label>
            <input
              [(ngModel)]="form.pattern_name"
              placeholder="LOT_REQUIRED, NOMENCLATURE…"
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <!-- Priority -->
          <div>
            <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Prioridad</label>
            <input
              type="number"
              [(ngModel)]="form.priority"
              min="0"
              placeholder="0"
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <!-- Regex -->
          <div class="md:col-span-2">
            <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Expresión Regular (regex)</label>
            <input
              [(ngModel)]="form.regex"
              placeholder="^[A-Z]+-\\d{3}:LOT\\d{6}$"
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors font-mono"
            />
          </div>

          <!-- Error message -->
          <div class="md:col-span-2">
            <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Mensaje de Error para el Operador</label>
            <input
              [(ngModel)]="form.error_message"
              placeholder="Este ítem requiere número de lote (ej: ITEM-001:LOT202601)"
              class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors"
            />
          </div>

          <!-- Live regex tester -->
          <div class="md:col-span-2 bg-slate-800/60 border border-slate-700 rounded-xl p-4">
            <label class="block text-slate-400 text-xs font-bold mb-2 uppercase tracking-wider flex items-center gap-2">
              <i class="fa-solid fa-flask text-yellow-400"></i> Probar Regex (live)
            </label>
            <div class="flex gap-3 items-center">
              <input
                [(ngModel)]="testInput"
                placeholder="Escribe un código de ejemplo para probar"
                class="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-white placeholder-slate-600 focus:outline-none focus:border-yellow-500 transition-colors font-mono text-sm"
              />
              @if (testInput && form.regex) {
                <span [class]="regexTestPasses() ? 'text-green-400' : 'text-red-400'" class="shrink-0 font-bold text-sm flex items-center gap-1">
                  <i [class]="regexTestPasses() ? 'fa-solid fa-check' : 'fa-solid fa-xmark'"></i>
                  {{ regexTestPasses() ? 'Válido' : 'Inválido' }}
                </span>
              }
            </div>
          </div>
        </div>

        <!-- Submit command -->
        <div class="flex justify-end mt-6">
          <button
            (click)="submitAdd()"
            [disabled]="svc.commandBusy() || !formValid()"
            class="px-8 py-3 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 text-white font-bold rounded-xl transition-colors flex items-center gap-2"
          >
            @if (svc.commandBusy()) {
              <i class="fa-solid fa-spinner fa-spin"></i> Guardando…
            } @else {
              <i class="fa-solid fa-plus"></i> Agregar Patrón
            }
          </button>
        </div>
      </div>

    </div>
  `
})
export class MesItemConfigComponent {
  readonly svc = inject(MesConfigService);

  searchInput = '';
  testInput = '';

  form: AddScanPatternCommand = {
    item_code: '',
    pattern_name: '',
    regex: '',
    error_message: '',
    priority: 0,
    is_active: true,
  };

  formValid(): boolean {
    return (
      this.form.item_code.trim().length > 0 &&
      this.form.pattern_name.trim().length > 0 &&
      this.form.regex.trim().length > 0 &&
      this.form.error_message.trim().length > 0
    );
  }

  regexTestPasses(): boolean {
    if (!this.form.regex || !this.testInput) return false;
    try {
      return new RegExp(this.form.regex).test(this.testInput);
    } catch {
      return false;
    }
  }

  runQuery(): void {
    const code = this.searchInput.trim();
    if (!code) return;
    // Auto-fill item_code in command form
    this.form.item_code = code;
    this.svc.queryPatterns(code);
  }

  async remove(patternId: string): Promise<void> {
    const itemCode = this.svc.queriedItemCode();
    if (!itemCode) return;
    await this.svc.removePattern(itemCode, patternId);
  }

  async submitAdd(): Promise<void> {
    const ok = await this.svc.addPattern({ ...this.form });
    if (ok) {
      this.form = {
        item_code: this.form.item_code,
        pattern_name: '',
        regex: '',
        error_message: '',
        priority: 0,
        is_active: true,
      };
      this.testInput = '';
    }
  }
}
