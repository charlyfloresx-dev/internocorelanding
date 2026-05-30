import { Component, inject, signal, computed, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { Subscription } from 'rxjs';
import { MesConfigService, AddScanPatternCommand } from '../../../core/services/mes-config.service';
import { StandardTimeService, StandardTime } from '../../../core/services/standard-time.service';
import { SideDrawerService } from '../../../core/services/side-drawer.service';
import { StandardTimeFormComponent } from '../../../shared/components/standard-time-form.component';

@Component({
  selector: 'app-mes-item-config',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in">

      <!-- Header -->
      <div class="flex justify-between items-center mb-8">
        <div>
          <h1 class="text-3xl font-bold text-white tracking-tight">Configuración de Ítem — MES</h1>
          <p class="text-slate-400">Patrones de escaneo y tiempos estándar por código de ítem</p>
        </div>
        <span class="px-3 py-1 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20 text-xs font-bold uppercase tracking-wider">
          <i class="fa-solid fa-barcode mr-1"></i> Item Config
        </span>
      </div>

      <!-- ─── TAB NAV ────────────────────────────────────────────────────────── -->
      <div class="flex gap-1 bg-slate-900 border border-slate-800 rounded-xl p-1 w-fit">
        <button
          (click)="activeTab.set('patterns')"
          [class]="activeTab() === 'patterns'
            ? 'px-4 py-2 rounded-lg bg-violet-600 text-white text-xs font-bold'
            : 'px-4 py-2 rounded-lg text-slate-400 hover:text-white text-xs font-bold transition-colors'"
        >
          <i class="fa-solid fa-barcode mr-1.5"></i> Patrones de Escaneo
        </button>
        <button
          (click)="onOpenStandardTimes()"
          [class]="activeTab() === 'standard-times'
            ? 'px-4 py-2 rounded-lg bg-teal-600 text-white text-xs font-bold'
            : 'px-4 py-2 rounded-lg text-slate-400 hover:text-white text-xs font-bold transition-colors'"
        >
          <i class="fa-solid fa-clock mr-1.5"></i> Tiempos Estándar
        </button>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════════════
           TAB: SCAN PATTERNS
      ═══════════════════════════════════════════════════════════════════════ -->
      @if (activeTab() === 'patterns') {

        <!-- QUERY PANEL -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-sky-500 to-violet-500"></div>

          <h3 class="text-white font-bold mb-4 flex items-center gap-2">
            <i class="fa-solid fa-magnifying-glass text-sky-400"></i>
            Consultar Patrones por Ítem
          </h3>

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

          @if (svc.queryError()) {
            <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm mb-4">
              <i class="fa-solid fa-triangle-exclamation mr-2"></i>{{ svc.queryError() }}
            </div>
          }

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

        <!-- COMMAND PANEL -->
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
            <div class="md:col-span-2">
              <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Código de Ítem</label>
              <input
                [(ngModel)]="form.item_code"
                placeholder="SKU del producto"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors font-mono"
              />
            </div>

            <div>
              <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Nombre del Patrón</label>
              <input
                [(ngModel)]="form.pattern_name"
                placeholder="LOT_REQUIRED, NOMENCLATURE…"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors"
              />
            </div>

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

            <div class="md:col-span-2">
              <label class="block text-slate-400 text-xs font-bold mb-1 uppercase tracking-wider">Expresión Regular (regex)</label>
              <input
                [(ngModel)]="form.regex"
                placeholder="^[A-Z]+-\\d{3}:LOT\\d{6}$"
                class="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 transition-colors font-mono"
              />
            </div>

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

      } <!-- end patterns tab -->

      <!-- ═══════════════════════════════════════════════════════════════════════
           TAB: STANDARD TIMES
      ═══════════════════════════════════════════════════════════════════════ -->
      @if (activeTab() === 'standard-times') {

        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
          <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-teal-500 to-cyan-500"></div>

          <!-- Toolbar -->
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-white font-bold flex items-center gap-2">
              <i class="fa-solid fa-clock text-teal-400"></i>
              Tiempos Estándar por Ítem
            </h3>
            <div class="flex gap-2">
              <button
                (click)="openNewStandardTime()"
                class="px-4 py-2 bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-1.5"
              >
                <i class="fa-solid fa-plus"></i> Nuevo Tiempo
              </button>
            </div>
          </div>

          <!-- Filter by item_code -->
          <div class="flex gap-3 mb-5">
            <input
              [(ngModel)]="stSearchInput"
              (keydown.enter)="loadStandardTimes()"
              placeholder="Filtrar por código de ítem (vacío = todos)"
              class="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 transition-colors font-mono text-sm"
            />
            <button
              (click)="loadStandardTimes()"
              [disabled]="stSvc.loading()"
              class="px-5 py-2.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white text-xs font-bold rounded-xl transition-colors flex items-center gap-1.5"
            >
              @if (stSvc.loading()) {
                <i class="fa-solid fa-spinner fa-spin"></i>
              } @else {
                <i class="fa-solid fa-filter"></i>
              }
              Filtrar
            </button>
          </div>

          <!-- Table -->
          @if (stSvc.loading()) {
            <div class="py-12 text-center text-slate-600">
              <i class="fa-solid fa-spinner fa-spin text-2xl mb-3"></i>
              <p class="text-sm">Cargando tiempos…</p>
            </div>
          } @else if (stSvc.items().length === 0) {
            <div class="py-12 text-center text-slate-600">
              <i class="fa-solid fa-clock text-3xl mb-3"></i>
              <p class="text-sm font-medium">Sin tiempos estándar registrados</p>
              <p class="text-xs mt-1">Haz clic en "Nuevo Tiempo" para agregar una operación.</p>
            </div>
          } @else {
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-800">
                    <th class="text-left text-xs font-bold text-slate-500 uppercase tracking-wider pb-3 pr-4">Ítem</th>
                    <th class="text-left text-xs font-bold text-slate-500 uppercase tracking-wider pb-3 pr-4">Operación</th>
                    <th class="text-right text-xs font-bold text-slate-500 uppercase tracking-wider pb-3 pr-4">Setup (h)</th>
                    <th class="text-right text-xs font-bold text-slate-500 uppercase tracking-wider pb-3 pr-4">Ciclo (s)</th>
                    <th class="pb-3 w-16"></th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/50">
                  @for (st of stSvc.items(); track st.id) {
                    <tr class="group hover:bg-slate-800/30 transition-colors">
                      <td class="py-3 pr-4 font-mono text-xs text-teal-400 font-bold">{{ st.item_code }}</td>
                      <td class="py-3 pr-4 text-white text-sm">{{ st.operation_name }}</td>
                      <td class="py-3 pr-4 text-right font-mono text-white">{{ st.set_time_hours | number:'1.2-4' }}</td>
                      <td class="py-3 pr-4 text-right font-mono">
                        @if (st.cycle_time_seconds) {
                          <span class="text-white">{{ st.cycle_time_seconds }}</span>
                        } @else {
                          <span class="text-slate-600 text-xs">—</span>
                        }
                      </td>
                      <td class="py-3 text-right">
                        <div class="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            (click)="editStandardTime(st)"
                            class="p-1.5 text-slate-500 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition-colors"
                            title="Editar"
                          >
                            <i class="fa-solid fa-pen text-xs"></i>
                          </button>
                          <button
                            (click)="deleteStandardTime(st)"
                            class="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                            title="Eliminar"
                          >
                            <i class="fa-solid fa-trash-can text-xs"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
            <p class="text-xs text-slate-600 mt-4">{{ stSvc.items().length }} tiempo(s) estándar</p>
          }

        </div>

      } <!-- end standard-times tab -->

    </div>
  `
})
export class MesItemConfigComponent implements OnInit, OnDestroy {
  readonly svc = inject(MesConfigService);
  readonly stSvc = inject(StandardTimeService);
  readonly drawer = inject(SideDrawerService);

  activeTab = signal<'patterns' | 'standard-times'>('patterns');
  searchInput = '';
  stSearchInput = '';
  testInput = '';

  private refreshSub?: Subscription;

  form: AddScanPatternCommand = {
    item_code: '',
    pattern_name: '',
    regex: '',
    error_message: '',
    priority: 0,
    is_active: true,
  };

  ngOnInit(): void {
    this.refreshSub = this.drawer.refresh$.subscribe(() => {
      if (this.activeTab() === 'standard-times') {
        this.loadStandardTimes();
      }
    });
  }

  ngOnDestroy(): void {
    this.refreshSub?.unsubscribe();
  }

  onOpenStandardTimes(): void {
    this.activeTab.set('standard-times');
    this.loadStandardTimes();
  }

  loadStandardTimes(): void {
    this.stSvc.load(this.stSearchInput.trim() || undefined);
  }

  openNewStandardTime(): void {
    this.drawer.open(StandardTimeFormComponent, {
      title: 'Nuevo Tiempo Estándar',
      icon: 'timer',
      width: 'w-[480px]',
    });
  }

  editStandardTime(st: StandardTime): void {
    this.drawer.open(
      StandardTimeFormComponent,
      { title: 'Editar Tiempo Estándar', icon: 'timer', width: 'w-[480px]' },
      st
    );
  }

  async deleteStandardTime(st: StandardTime): Promise<void> {
    if (!confirm(`¿Eliminar "${st.operation_name}" de ${st.item_code}?`)) return;
    await this.stSvc.remove(st.id);
    await this.loadStandardTimes();
  }

  // ── Scan patterns ──────────────────────────────────────────────────────────

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
