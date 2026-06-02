import {
  Component, inject, signal, computed, ChangeDetectionStrategy, ViewChild, ElementRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { OnboardingService } from '../../core/services/onboarding.service';

// ─── Inline CSV templates ─────────────────────────────────────────────────────
const CSV_TEMPLATES = {
  products: `sku,name,description,category,uom_code,unit_price,currency
PROD-001,Cojinete SKF 6205,Cojinete radial estándar,Rodamientos,PZ,145.00,MXN
PROD-002,Tornillo M8x25 DIN 933,Tornillo cabeza hexagonal,Ferretería,PZ,2.50,MXN
PROD-003,Aceite hidráulico ISO 46,Aceite para sistemas hidráulicos,Lubricantes,GL,320.00,MXN`,

  partners: `code,name,type,rfc,email,phone,city
PROV-001,Distribuidora SKF México,SUPPLIER,DSK123456ABC,ventas@skf.com.mx,800-123-4567,Monterrey
PROV-002,Ferretera Industrial TIJ,SUPPLIER,FIT890123DEF,pedidos@ferretera.com,664-555-0123,Tijuana
CLI-001,Maquiladora ACME SA,CUSTOMER,MAC456789GHI,compras@acme.com,664-555-0456,Tijuana`,

  collaborators: `internal_id,name,last_name,department,job_title,rfid_code,pin,email
EMP001,Juan,García López,Producción,Operador,,1234,jgarcia@empresa.com
EMP002,María,Rodríguez Soto,Calidad,Inspector de Calidad,,5678,mrodriguez@empresa.com
EMP003,Carlos,Martínez Cruz,Mantenimiento,Técnico de Mantenimiento,A1B2C3D4,,cmartinez@empresa.com`,
};

const STEP_META = [
  { icon: 'business',         label: 'Empresa'      },
  { icon: 'workspace_premium',label: 'Plan'         },
  { icon: 'inventory_2',      label: 'Catálogo'     },
  { icon: 'handshake',        label: 'Partners'     },
  { icon: 'warehouse',        label: 'Almacén'      },
  { icon: 'badge',            label: 'Personal'     },
  { icon: 'precision_manufacturing', label: 'MES'   },
  { icon: 'notifications',    label: 'Alertas'      },
];

@Component({
  selector: 'app-onboarding',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
<div class="min-h-screen bg-surface-bg flex flex-col overflow-x-hidden">

  <!-- ── Ambient glow ─────────────────────────────────────────── -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden">
    <div class="absolute top-1/4 -left-32 w-96 h-96 bg-primary/10 blur-[140px] rounded-full"></div>
    <div class="absolute bottom-1/4 -right-32 w-96 h-96 bg-primary/6 blur-[140px] rounded-full"></div>
  </div>

  <!-- ── Header ───────────────────────────────────────────────── -->
  <header class="relative z-10 flex items-center justify-between px-8 py-5 border-b border-surface-border/60">
    <div class="flex items-center gap-3">
      <svg viewBox="0 0 100 100" class="w-8 h-8 text-primary" fill="none" stroke="currentColor" stroke-width="8">
        <path d="M20 20 L80 20 L80 80 L20 80 Z"/>
        <path d="M40 40 L60 40 L60 60 L40 60 Z" fill="currentColor" stroke="none"/>
      </svg>
      <span class="font-black text-surface-text tracking-tighter text-lg uppercase italic">
        Interno<span class="text-primary">Core</span>
      </span>
    </div>
    <span class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest hidden sm:block">
      Configuración Inicial · Paso {{ step() }}/{{ totalSteps }}
    </span>
  </header>

  <!-- ── Body ─────────────────────────────────────────────────── -->
  <main class="flex-1 flex items-start justify-center px-4 py-8 relative z-10">
    <div class="w-full max-w-3xl space-y-6">

      <!-- Step progress bar -->
      <div class="space-y-3">
        <div class="flex gap-1.5">
          @for (s of stepMeta; track s.label; let i = $index) {
            <div class="flex-1 h-1.5 rounded-full transition-all duration-500"
                 [class.bg-primary]="step() > i + 1"
                 [class.bg-primary/40]="step() === i + 1"
                 [class.bg-surface-border]="step() < i + 1"></div>
          }
        </div>
        <div class="flex justify-between">
          @for (s of stepMeta; track s.label; let i = $index) {
            <div class="flex flex-col items-center gap-1 transition-all duration-300"
                 [class.opacity-100]="step() >= i + 1"
                 [class.opacity-30]="step() < i + 1">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center text-[10px] transition-all duration-300"
                   [class.bg-primary]="step() > i + 1"
                   [class.text-ic-dark]="step() > i + 1"
                   [class.ring-2]="step() === i + 1"
                   [class.ring-primary]="step() === i + 1"
                   [class.bg-surface-card]="step() <= i + 1"
                   [class.text-primary]="step() === i + 1"
                   [class.text-surface-text-muted]="step() < i + 1">
                @if (step() > i + 1) {
                  <mat-icon class="!text-sm !w-4 !h-4">check</mat-icon>
                } @else {
                  <span class="font-black text-[9px]">{{ i + 1 }}</span>
                }
              </div>
              <span class="text-[8px] font-bold tracking-widest uppercase hidden sm:block"
                    [class.text-primary]="step() === i + 1"
                    [class.text-surface-text-muted]="step() !== i + 1">
                {{ s.label }}
              </span>
            </div>
          }
        </div>
      </div>

      <!-- ── Card shell ──────────────────────────────────────── -->
      <div class="glass-card rounded-3xl border border-surface-border p-8 shadow-2xl">

        <!-- ═══════ STEP 1 — Empresa ═══════ -->
        @if (step() === 1) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 1 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Identidad de la Empresa</h2>
              <p class="text-xs text-surface-text-muted mt-1">Datos fiscales y operativos de tu organización</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div class="space-y-1.5">
                <label class="field-label">Nombre de la Empresa *</label>
                <input class="input-industrial w-full" placeholder="Ej. Global Logistics SA de CV" [(ngModel)]="company.name"/>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">RFC / Tax ID</label>
                <input class="input-industrial w-full" placeholder="GLO123456ABC" [(ngModel)]="company.tax_id"/>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Sector Industrial *</label>
                <select class="input-industrial w-full" [(ngModel)]="company.industry">
                  <option value="Aerospace">Aeroespacial / Defensa</option>
                  <option value="Medical">Dispositivos Médicos (FDA)</option>
                  <option value="Automotive">Automotriz / Tier 1</option>
                  <option value="Electronics">Electrónica</option>
                  <option value="Logistics">Logística / Distribución</option>
                  <option value="Food">Alimentos y Bebidas</option>
                  <option value="Manufacturing">Manufactura General</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">País</label>
                <select class="input-industrial w-full" [(ngModel)]="company.country_code">
                  <option value="MX">🇲🇽 México</option>
                  <option value="US">🇺🇸 Estados Unidos</option>
                  <option value="CA">🇨🇦 Canadá</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Moneda Base</label>
                <select class="input-industrial w-full" [(ngModel)]="company.base_currency">
                  <option value="MXN">MXN — Peso Mexicano</option>
                  <option value="USD">USD — Dólar Americano</option>
                  <option value="EUR">EUR — Euro</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Zona Horaria</label>
                <select class="input-industrial w-full" [(ngModel)]="company.timezone">
                  <option value="America/Tijuana">America/Tijuana (PST/PDT)</option>
                  <option value="America/Mexico_City">America/Mexico_City (CST)</option>
                  <option value="America/Monterrey">America/Monterrey (CST)</option>
                  <option value="America/New_York">America/New_York (EST)</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Tasa IVA / Tax Rate</label>
                <select class="input-industrial w-full" [(ngModel)]="company.tax_rate">
                  <option value="0.16">16% (IVA México estándar)</option>
                  <option value="0.08">8% (Zona fronteriza)</option>
                  <option value="0.00">0% (Exportación / US)</option>
                  <option value="0.10">10% (Custom)</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Norma de Calidad</label>
                <select class="input-industrial w-full" [(ngModel)]="company.quality_standard">
                  <option value="AS9100">AS9100 (Aeroespacial)</option>
                  <option value="FDA_21CFR">FDA 21 CFR Part 820 (Médico)</option>
                  <option value="IATF16949">IATF 16949 (Automotriz)</option>
                  <option value="ISO9001">ISO 9001 (General)</option>
                  <option value="NONE">Sin norma específica</option>
                </select>
              </div>
            </div>
            @if (stepError()) {
              <p class="text-red-400 text-xs font-bold flex items-center gap-2">
                <mat-icon class="!text-sm !w-4 !h-4">error</mat-icon> {{ stepError() }}
              </p>
            }
          </div>
        }

        <!-- ═══════ STEP 2 — Plan ═══════ -->
        @else if (step() === 2) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 2 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Selecciona tu Plan</h2>
              <p class="text-xs text-surface-text-muted mt-1">Los módulos activos dependen del plan seleccionado</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              @for (plan of plans; track plan.id) {
                <button
                  (click)="selectedPlan.set(plan.id)"
                  class="text-left p-5 rounded-2xl border-2 transition-all duration-300 space-y-3"
                  [class.border-primary]="selectedPlan() === plan.id"
                  [class.bg-primary/5]="selectedPlan() === plan.id"
                  [class.border-surface-border]="selectedPlan() !== plan.id"
                  [class.bg-surface-card/40]="selectedPlan() !== plan.id"
                >
                  @if (plan.recommended) {
                    <span class="text-[8px] font-black uppercase tracking-widest bg-primary text-ic-dark px-2 py-0.5 rounded-full">Recomendado</span>
                  }
                  <div>
                    <p class="font-black text-surface-text text-sm uppercase tracking-tight">{{ plan.name }}</p>
                    <p class="text-2xl font-black text-primary mt-1">&#36;{{ plan.price }}<span class="text-xs text-surface-text-muted font-normal"> USD/mes</span></p>
                  </div>
                  <ul class="space-y-1.5">
                    @for (f of plan.features; track f) {
                      <li class="flex items-start gap-2 text-[10px] text-surface-text-muted">
                        <mat-icon class="!text-[10px] !w-3 !h-3 text-primary mt-0.5 flex-shrink-0">check_circle</mat-icon>
                        {{ f }}
                      </li>
                    }
                  </ul>
                </button>
              }
            </div>
            <p class="text-[9px] text-surface-text-muted text-center">Puedes cambiar de plan en cualquier momento desde <strong>Configuración → Suscripción</strong></p>
          </div>
        }

        <!-- ═══════ STEP 3 — Catálogo ═══════ -->
        @else if (step() === 3) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 3 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Catálogo de Productos</h2>
              <p class="text-xs text-surface-text-muted mt-1">Define las categorías base y carga tus productos vía CSV</p>
            </div>

            <!-- Categorías -->
            <div class="space-y-3">
              <label class="field-label">Categorías de Producto</label>
              <div class="flex gap-2">
                <input class="input-industrial flex-1" placeholder="Ej. Rodamientos, Lubricantes, Consumibles…" [(ngModel)]="newCategoryName"/>
                <button (click)="addCategory()" class="btn-secondary-sm whitespace-nowrap">
                  <mat-icon class="!text-sm">add</mat-icon> Agregar
                </button>
              </div>
              @if (categories().length) {
                <div class="flex flex-wrap gap-2">
                  @for (cat of categories(); track cat; let i = $index) {
                    <span class="flex items-center gap-1.5 text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 px-3 py-1.5 rounded-lg">
                      {{ cat }}
                      <button (click)="removeCategory(i)" class="hover:text-red-400 transition-colors">
                        <mat-icon class="!text-[10px] !w-3 !h-3">close</mat-icon>
                      </button>
                    </span>
                  }
                </div>
              } @else {
                <p class="text-[10px] text-surface-text-muted italic">Sin categorías — puedes agregarlas ahora o desde Catálogo después.</p>
              }
            </div>

            <!-- CSV Bulk Import Productos -->
            <ng-container *ngTemplateOutlet="csvSection; context: {
              $implicit: 'products',
              title: 'Carga Masiva de Productos',
              hint: 'sku, name, description, category, uom_code, unit_price, currency',
              rows: productsCsvRows(),
              cols: ['sku','name','category','uom_code','unit_price','currency'],
              dragging: isDraggingProducts()
            }"></ng-container>
          </div>
        }

        <!-- ═══════ STEP 4 — Partners ═══════ -->
        @else if (step() === 4) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 4 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Clientes y Proveedores</h2>
              <p class="text-xs text-surface-text-muted mt-1">Carga tu directorio de partners B2B vía CSV</p>
            </div>
            <div class="bg-surface-card/40 rounded-2xl border border-surface-border p-5 space-y-2">
              <p class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Columnas del template</p>
              <div class="flex flex-wrap gap-2">
                @for (col of ['code','name','type','rfc','email','phone','city']; track col) {
                  <span class="font-mono text-[9px] bg-surface-bg text-primary px-2 py-1 rounded-md border border-primary/20">{{ col }}</span>
                }
              </div>
              <p class="text-[9px] text-surface-text-muted mt-2">
                <strong>type</strong> acepta: <code class="text-primary">SUPPLIER</code> · <code class="text-primary">CUSTOMER</code> · <code class="text-primary">BOTH</code>
              </p>
            </div>
            <ng-container *ngTemplateOutlet="csvSection; context: {
              $implicit: 'partners',
              title: 'Carga Masiva de Partners',
              hint: 'code, name, type (SUPPLIER/CUSTOMER/BOTH), rfc, email, phone, city',
              rows: partnersCsvRows(),
              cols: ['code','name','type','rfc','email','city'],
              dragging: isDraggingPartners()
            }"></ng-container>
          </div>
        }

        <!-- ═══════ STEP 5 — Almacén ═══════ -->
        @else if (step() === 5) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 5 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Almacén Principal</h2>
              <p class="text-xs text-surface-text-muted mt-1">Define tu primera ubicación física de inventario</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div class="space-y-1.5">
                <label class="field-label">Nombre del Almacén *</label>
                <input class="input-industrial w-full" placeholder="Ej. Almacén Principal Tijuana" [(ngModel)]="warehouse.name"/>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Código *</label>
                <input class="input-industrial w-full" placeholder="Ej. WH-TIJ-01" [(ngModel)]="warehouse.code"/>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Tipo</label>
                <select class="input-industrial w-full" [(ngModel)]="warehouse.type">
                  <option value="PHYSICAL">Físico (inventario real)</option>
                  <option value="VIRTUAL">Virtual (tránsito / consigna)</option>
                  <option value="TRANSIT">Tránsito aduanero</option>
                </select>
              </div>
              <div class="space-y-1.5">
                <label class="field-label">Ciudad / Ubicación</label>
                <input class="input-industrial w-full" placeholder="Ej. Tijuana, Baja California" [(ngModel)]="warehouse.address"/>
              </div>
            </div>
            <div class="bg-surface-card/40 rounded-2xl border border-primary/10 p-4">
              <p class="text-[9px] text-surface-text-muted">
                <mat-icon class="!text-[10px] !w-3 !h-3 text-primary inline">info</mat-icon>
                Puedes agregar más almacenes y ubicaciones (bins/racks) desde <strong>Catálogo → Almacenes</strong> una vez dentro del sistema.
              </p>
            </div>
            @if (stepError()) {
              <p class="text-red-400 text-xs font-bold flex items-center gap-2">
                <mat-icon class="!text-sm !w-4 !h-4">error</mat-icon> {{ stepError() }}
              </p>
            }
          </div>
        }

        <!-- ═══════ STEP 6 — Colaboradores ═══════ -->
        @else if (step() === 6) {
          <div class="space-y-6 animate-fade-in">
            <div>
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 6 de 8</p>
              <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Personal de Planta</h2>
              <p class="text-xs text-surface-text-muted mt-1">Carga tu equipo con RFID/PIN vía CSV</p>
            </div>
            <div class="bg-surface-card/40 rounded-2xl border border-surface-border p-5 space-y-2">
              <p class="text-[10px] font-bold text-surface-text-muted uppercase tracking-widest">Columnas del template</p>
              <div class="flex flex-wrap gap-2">
                @for (col of ['internal_id','name','last_name','department','job_title','rfid_code','pin','email']; track col) {
                  <span class="font-mono text-[9px] bg-surface-bg text-primary px-2 py-1 rounded-md border border-primary/20">{{ col }}</span>
                }
              </div>
              <p class="text-[9px] text-surface-text-muted mt-2">
                <strong>rfid_code</strong> y <strong>pin</strong> son opcionales pero al menos uno es requerido para login industrial.
                <strong>department</strong> debe coincidir con uno de los 6 departamentos default (Producción, Calidad, Mantenimiento, Almacén, Administración, Ingeniería).
              </p>
            </div>
            <ng-container *ngTemplateOutlet="csvSection; context: {
              $implicit: 'collaborators',
              title: 'Carga Masiva de Colaboradores',
              hint: 'internal_id, name, last_name, department, job_title, rfid_code, pin, email',
              rows: collaboratorsCsvRows(),
              cols: ['internal_id','name','last_name','department','job_title'],
              dragging: isDraggingCollaborators()
            }"></ng-container>
          </div>
        }

        <!-- ═══════ STEP 7 — MES / Planta ═══════ -->
        @else if (step() === 7) {
          <div class="space-y-6 animate-fade-in">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 7 de 8</p>
                <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Planta de Producción</h2>
                <p class="text-xs text-surface-text-muted mt-1">Configura tu planta para el módulo MES (opcional)</p>
              </div>
              <label class="flex items-center gap-2 cursor-pointer shrink-0">
                <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Omitir</span>
                <div class="relative w-10 h-5">
                  <input type="checkbox" class="sr-only peer" [(ngModel)]="skipMes" />
                  <div class="w-full h-full bg-surface-border rounded-full peer-checked:bg-primary transition-colors duration-300"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-300 peer-checked:translate-x-5"></div>
                </div>
              </label>
            </div>

            @if (!skipMes) {
              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div class="space-y-1.5">
                  <label class="field-label">Nombre de la Planta *</label>
                  <input class="input-industrial w-full" placeholder="Ej. Planta Tijuana Norte" [(ngModel)]="facility.name"/>
                </div>
                <div class="space-y-1.5">
                  <label class="field-label">Código *</label>
                  <input class="input-industrial w-full" placeholder="Ej. PLT-TIJ" [(ngModel)]="facility.code"/>
                </div>
                <div class="space-y-1.5 md:col-span-2">
                  <label class="field-label">Dirección</label>
                  <input class="input-industrial w-full" placeholder="Ej. Blvd. Industrial 1234, Tijuana BC" [(ngModel)]="facility.address"/>
                </div>
              </div>
              <div class="bg-surface-card/40 rounded-2xl border border-primary/10 p-4 space-y-2">
                <p class="text-[9px] font-black text-primary uppercase tracking-widest">Creado automáticamente al guardar:</p>
                <ul class="space-y-1">
                  @for (item of mesAutoItems; track item) {
                    <li class="flex items-center gap-2 text-[10px] text-surface-text-muted">
                      <mat-icon class="!text-[10px] !w-3 !h-3 text-primary">auto_fix_high</mat-icon>
                      {{ item }}
                    </li>
                  }
                </ul>
              </div>
            } @else {
              <div class="rounded-2xl border border-surface-border bg-surface-card/30 p-8 text-center">
                <mat-icon class="text-surface-text-muted text-4xl !w-10 !h-10 mb-3">precision_manufacturing</mat-icon>
                <p class="text-sm text-surface-text-muted">El módulo MES se puede configurar después desde <strong>Producción → Configuración</strong></p>
              </div>
            }
          </div>
        }

        <!-- ═══════ STEP 8 — Notificaciones ═══════ -->
        @else if (step() === 8) {
          <div class="space-y-6 animate-fade-in">
            <div class="flex items-start justify-between gap-4">
              <div>
                <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] mb-1">Paso 8 de 8</p>
                <h2 class="text-2xl font-black text-surface-text tracking-tighter uppercase italic">Alertas y Notificaciones</h2>
                <p class="text-xs text-surface-text-muted mt-1">Configura canales de alerta para ANDON, tickets y eventos críticos</p>
              </div>
              <label class="flex items-center gap-2 cursor-pointer shrink-0">
                <span class="text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Omitir</span>
                <div class="relative w-10 h-5">
                  <input type="checkbox" class="sr-only peer" [(ngModel)]="skipNotifications" />
                  <div class="w-full h-full bg-surface-border rounded-full peer-checked:bg-primary transition-colors duration-300"></div>
                  <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-300 peer-checked:translate-x-5"></div>
                </div>
              </label>
            </div>

            @if (!skipNotifications) {
              <div class="space-y-4">
                <div class="space-y-1.5">
                  <label class="field-label">Email de notificaciones (Admin)</label>
                  <input type="email" class="input-industrial w-full" placeholder="admin@tuempresa.com" [(ngModel)]="notifEmail"/>
                </div>

                <div class="border border-surface-border rounded-2xl divide-y divide-surface-border overflow-hidden">
                  @for (ch of notifChannels; track ch.id) {
                    <div class="flex items-center justify-between px-5 py-3.5 bg-surface-card/30">
                      <div class="flex items-center gap-3">
                        <mat-icon class="text-primary !text-lg !w-5 !h-5">{{ ch.icon }}</mat-icon>
                        <div>
                          <p class="text-xs font-bold text-surface-text">{{ ch.label }}</p>
                          <p class="text-[9px] text-surface-text-muted">{{ ch.desc }}</p>
                        </div>
                      </div>
                      <label class="relative w-10 h-5 cursor-pointer">
                        <input type="checkbox" class="sr-only peer" [(ngModel)]="ch.enabled" />
                        <div class="w-full h-full bg-surface-border rounded-full peer-checked:bg-primary transition-colors duration-300"></div>
                        <div class="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform duration-300 peer-checked:translate-x-5"></div>
                      </label>
                    </div>
                  }
                </div>

                @if (notifChannels[1].enabled) {
                  <div class="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-5 space-y-3">
                    <p class="text-[9px] font-black text-amber-400 uppercase tracking-widest">Credenciales WhatsApp (Twilio Sandbox)</p>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div class="space-y-1.5">
                        <label class="field-label">Twilio Account SID</label>
                        <input class="input-industrial w-full font-mono text-xs" placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" [(ngModel)]="twilioSid"/>
                      </div>
                      <div class="space-y-1.5">
                        <label class="field-label">Twilio Auth Token</label>
                        <input type="password" class="input-industrial w-full font-mono text-xs" placeholder="••••••••••••••••••••••••••••••••" [(ngModel)]="twilioToken"/>
                      </div>
                    </div>
                  </div>
                }
              </div>
            } @else {
              <div class="rounded-2xl border border-surface-border bg-surface-card/30 p-8 text-center">
                <mat-icon class="text-surface-text-muted text-4xl !w-10 !h-10 mb-3">notifications_off</mat-icon>
                <p class="text-sm text-surface-text-muted">Las notificaciones se configuran después desde <strong>Admin → Alertas</strong></p>
              </div>
            }
          </div>
        }

        <!-- ── Navigation footer ─────────────────────────────── -->
        <div class="mt-8 pt-6 border-t border-surface-border/50 flex items-center justify-between gap-4">
          <button
            (click)="prevStep()"
            [disabled]="step() === 1"
            class="flex items-center gap-2 px-5 py-3 text-[10px] font-black uppercase tracking-widest text-surface-text-muted hover:text-primary disabled:opacity-0 transition-all">
            <mat-icon class="!text-sm !w-4 !h-4">arrow_back</mat-icon> Anterior
          </button>

          <div class="flex items-center gap-3">
            @if (isLoading()) {
              <div class="w-4 h-4 border-2 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            }
            <button
              (click)="nextStep()"
              [disabled]="isLoading()"
              class="flex items-center gap-2 px-8 py-3.5 bg-primary text-ic-dark rounded-xl font-black text-xs uppercase tracking-[0.15em] hover:shadow-[0_0_20px_rgba(0,229,255,0.35)] transition-all disabled:opacity-60 active:scale-95">
              {{ step() === totalSteps ? 'Finalizar Setup' : 'Siguiente' }}
              <mat-icon class="!text-sm !w-4 !h-4">{{ step() === totalSteps ? 'rocket_launch' : 'arrow_forward' }}</mat-icon>
            </button>
          </div>
        </div>

      </div><!-- /card -->
    </div>
  </main>

  <!-- ── CSV Import reusable section (ng-template) ────────────── -->
  <ng-template #csvSection let-type let-title="title" let-hint="hint" let-rows="rows" let-cols="cols" let-dragging="dragging">
    <div class="border-t border-surface-border/50 pt-5 space-y-4">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <p class="text-[10px] font-black uppercase tracking-widest text-surface-text-muted">{{ title }}</p>
          <p class="text-[9px] text-surface-text-muted mt-0.5 font-mono">{{ hint }}</p>
        </div>
        <button (click)="downloadTemplate(type)"
                class="flex items-center gap-2 px-4 py-2 rounded-xl border border-primary/30 text-primary hover:bg-primary/10 transition-all text-[10px] font-black uppercase tracking-widest">
          <mat-icon class="!text-sm !w-4 !h-4">download</mat-icon>
          Descargar Plantilla
        </button>
      </div>

      <!-- Drop zone -->
      <div class="relative border-2 border-dashed rounded-2xl transition-all duration-300 cursor-pointer"
           [class.border-primary]="dragging"
           [class.bg-primary/5]="dragging"
           [class.border-surface-border]="!dragging"
           [class.hover:border-primary/50]="!rows?.length"
           (dragover)="onDragOver($event, type)"
           (dragleave)="onDragLeave(type)"
           (drop)="onDrop($event, type)"
           (click)="triggerFileInput(type)">

        @if (!rows?.length) {
          <!-- Empty state -->
          <div class="flex flex-col items-center justify-center py-10 gap-3">
            <mat-icon class="text-surface-text-muted !text-4xl !w-10 !h-10">upload_file</mat-icon>
            <div class="text-center">
              <p class="text-xs font-bold text-surface-text-muted">Arrastra tu CSV aquí o haz clic para seleccionar</p>
              <p class="text-[9px] text-surface-text-muted/60 mt-1">Solo archivos .csv · UTF-8</p>
            </div>
          </div>
        } @else {
          <!-- Preview table -->
          <div class="p-4" (click)="$event.stopPropagation()">
            <div class="flex items-center justify-between mb-3">
              <p class="text-[10px] font-black text-primary uppercase tracking-widest">
                <mat-icon class="!text-[10px] !w-3 !h-3">check_circle</mat-icon>
                {{ rows.length }} registros cargados
              </p>
              <button (click)="clearFile(type)" class="text-[9px] text-red-400 hover:text-red-300 font-bold flex items-center gap-1">
                <mat-icon class="!text-[10px] !w-3 !h-3">delete</mat-icon> Limpiar
              </button>
            </div>
            <div class="overflow-x-auto rounded-xl border border-surface-border">
              <table class="w-full text-[9px] font-mono">
                <thead>
                  <tr class="bg-surface-bg border-b border-surface-border">
                    @for (col of cols; track col) {
                      <th class="px-3 py-2 text-left text-primary font-black uppercase tracking-widest whitespace-nowrap">{{ col }}</th>
                    }
                  </tr>
                </thead>
                <tbody>
                  @for (row of rows | slice:0:5; track $index) {
                    <tr class="border-b border-surface-border/40 hover:bg-surface-card/30">
                      @for (col of cols; track col) {
                        <td class="px-3 py-1.5 text-surface-text-muted whitespace-nowrap max-w-[120px] truncate">{{ $any(row)[col] || '—' }}</td>
                      }
                    </tr>
                  }
                  @if (rows.length > 5) {
                    <tr>
                      <td [attr.colspan]="cols.length" class="px-3 py-2 text-[9px] text-surface-text-muted text-center italic">
                        + {{ rows.length - 5 }} registros más…
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          </div>
        }
      </div>

      <!-- Hidden file inputs (one per type) -->
      @if (type === 'products') {
        <input #productsFileInput type="file" accept=".csv" (change)="onFileSelected($event, 'products')" class="hidden">
      } @else if (type === 'partners') {
        <input #partnersFileInput type="file" accept=".csv" (change)="onFileSelected($event, 'partners')" class="hidden">
      } @else if (type === 'collaborators') {
        <input #collaboratorsFileInput type="file" accept=".csv" (change)="onFileSelected($event, 'collaborators')" class="hidden">
      }
    </div>
  </ng-template>

</div>
  `,
})
export class OnboardingComponent {
  private router  = inject(Router);
  private svc     = inject(OnboardingService);

  // ── Wizard state ──────────────────────────────────────────────
  readonly totalSteps = 8;
  readonly stepMeta   = STEP_META;
  step        = signal(1);
  isLoading   = signal(false);
  stepError   = signal('');

  // ── Step 1 ─────────────────────────────────────────────────
  company = { name: '', tax_id: '', industry: 'Aerospace', country_code: 'MX',
               base_currency: 'USD', timezone: 'America/Tijuana',
               tax_rate: '0.08', quality_standard: 'AS9100' };

  // ── Step 2 ─────────────────────────────────────────────────
  selectedPlan = signal<'OPERATIVE' | 'INDUSTRIAL' | 'ENTERPRISE'>('INDUSTRIAL');
  readonly plans = [
    { id: 'OPERATIVE' as const, name: 'Operativo', price: 45, recommended: false,
      features: ['SSOT Master Data', 'Inventario básico', 'Tickets de soporte', 'Hasta 3 usuarios'] },
    { id: 'INDUSTRIAL' as const, name: 'Industrial', price: 350, recommended: true,
      features: ['Todo el plan Operativo', 'MES + OEE', 'WMS avanzado', 'RFID/PIN', 'Usuarios ilimitados'] },
    { id: 'ENTERPRISE' as const, name: 'Enterprise', price: 550, recommended: false,
      features: ['Ecosistema completo', 'HCM + CMMS', 'Rutas AS9100/FDA', 'Soporte VIP', 'SAP/Oracle'] },
  ];

  // ── Step 3 ─────────────────────────────────────────────────
  categories      = signal<string[]>([]);
  newCategoryName = '';
  productsCsvRows = signal<Record<string, string>[]>([]);
  isDraggingProducts    = signal(false);

  // ── Step 4 ─────────────────────────────────────────────────
  partnersCsvRows       = signal<Record<string, string>[]>([]);
  isDraggingPartners    = signal(false);

  // ── Step 5 ─────────────────────────────────────────────────
  warehouse = { name: '', code: '', type: 'PHYSICAL', address: '' };

  // ── Step 6 ─────────────────────────────────────────────────
  collaboratorsCsvRows    = signal<Record<string, string>[]>([]);
  isDraggingCollaborators = signal(false);

  // ── Step 7 ─────────────────────────────────────────────────
  skipMes  = false;
  facility = { name: '', code: '', address: '' };
  readonly mesAutoItems = [
    '3 áreas de producción default (Ensamble, Calidad, WIP)',
    '3 turnos (Matutino 06-14h · Vespertino 14-22h · Nocturno 22-06h)',
    '2 descansos por turno (30 min c/u)',
  ];

  // ── Step 8 ─────────────────────────────────────────────────
  skipNotifications = false;
  notifEmail        = '';
  twilioSid         = '';
  twilioToken       = '';
  notifChannels = [
    { id: 'email',    icon: 'email',     label: 'Email',         desc: 'Alertas críticas y resúmenes diarios',     enabled: true  },
    { id: 'whatsapp', icon: 'whatsapp',  label: 'WhatsApp',      desc: 'ANDON y tiempos muertos en tiempo real',   enabled: false },
    { id: 'inapp',    icon: 'circle_notifications', label: 'In-App', desc: 'Notificaciones en el panel web',       enabled: true  },
  ];

  // ── File input ViewChild refs ──────────────────────────────
  @ViewChild('productsFileInput')      private productsInput!:      ElementRef<HTMLInputElement>;
  @ViewChild('partnersFileInput')      private partnersInput!:      ElementRef<HTMLInputElement>;
  @ViewChild('collaboratorsFileInput') private collaboratorsInput!: ElementRef<HTMLInputElement>;

  // ── Categorías ─────────────────────────────────────────────
  addCategory() {
    const name = this.newCategoryName.trim();
    if (!name || this.categories().includes(name)) return;
    this.categories.update(c => [...c, name]);
    this.newCategoryName = '';
  }

  removeCategory(i: number) {
    this.categories.update(c => c.filter((_, idx) => idx !== i));
  }

  // ── CSV download ───────────────────────────────────────────
  downloadTemplate(type: 'products' | 'partners' | 'collaborators') {
    this.svc.downloadCsv(CSV_TEMPLATES[type], `internocore_${type}_template.csv`);
  }

  // ── CSV drag-drop ──────────────────────────────────────────
  triggerFileInput(type: string) {
    if (type === 'products')       this.productsInput?.nativeElement.click();
    else if (type === 'partners')  this.partnersInput?.nativeElement.click();
    else                           this.collaboratorsInput?.nativeElement.click();
  }

  onDragOver(event: DragEvent, type: string) {
    event.preventDefault();
    event.stopPropagation();
    if (type === 'products')       this.isDraggingProducts.set(true);
    else if (type === 'partners')  this.isDraggingPartners.set(true);
    else                           this.isDraggingCollaborators.set(true);
  }

  onDragLeave(type: string) {
    if (type === 'products')       this.isDraggingProducts.set(false);
    else if (type === 'partners')  this.isDraggingPartners.set(false);
    else                           this.isDraggingCollaborators.set(false);
  }

  onDrop(event: DragEvent, type: string) {
    event.preventDefault();
    event.stopPropagation();
    this.onDragLeave(type);
    const file = event.dataTransfer?.files[0];
    if (file) this.readCsvFile(file, type);
  }

  onFileSelected(event: Event, type: string) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.readCsvFile(file, type);
  }

  private readCsvFile(file: File, type: string) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const rows = this.svc.parseCsv(text);
      if (type === 'products')       this.productsCsvRows.set(rows);
      else if (type === 'partners')  this.partnersCsvRows.set(rows);
      else                           this.collaboratorsCsvRows.set(rows);
    };
    reader.readAsText(file, 'utf-8');
  }

  clearFile(type: string) {
    if (type === 'products')       this.productsCsvRows.set([]);
    else if (type === 'partners')  this.partnersCsvRows.set([]);
    else                           this.collaboratorsCsvRows.set([]);
  }

  // ── Navigation ─────────────────────────────────────────────
  prevStep() {
    if (this.step() > 1) {
      this.step.update(s => s - 1);
      this.stepError.set('');
    }
  }

  async nextStep() {
    this.stepError.set('');
    if (!this.validate()) return;
    this.isLoading.set(true);
    try {
      await this.saveCurrentStep();
      if (this.step() < this.totalSteps) {
        this.step.update(s => s + 1);
      } else {
        this.router.navigate(['/dashboard']);
      }
    } catch (err: any) {
      const msg = err?.error?.detail || err?.message || 'Error al guardar. Intenta de nuevo.';
      this.stepError.set(msg);
    } finally {
      this.isLoading.set(false);
    }
  }

  private validate(): boolean {
    switch (this.step()) {
      case 1:
        if (!this.company.name.trim()) { this.stepError.set('El nombre de la empresa es requerido.'); return false; }
        break;
      case 5:
        if (!this.warehouse.name.trim()) { this.stepError.set('El nombre del almacén es requerido.'); return false; }
        if (!this.warehouse.code.trim()) { this.stepError.set('El código del almacén es requerido.'); return false; }
        break;
      case 7:
        if (!this.skipMes && !this.facility.name.trim()) { this.stepError.set('El nombre de la planta es requerido o activa "Omitir".'); return false; }
        break;
    }
    return true;
  }

  private async saveCurrentStep(): Promise<void> {
    switch (this.step()) {
      case 1:
        await this.svc.patchCompany({
          default_tax_rate: parseFloat(this.company.tax_rate),
          timezone:         this.company.timezone,
          base_currency:    this.company.base_currency,
          country_code:     this.company.country_code,
          industry_sector:  this.company.industry,
        }).catch(() => {}); // non-blocking — company update is best-effort
        break;

      case 3:
        for (const name of this.categories()) {
          await this.svc.createCategory({ name }).catch(() => {});
        }
        if (this.productsCsvRows().length) {
          await this.svc.bulkImportProducts(this.productsCsvRows() as any).catch(() => {});
        }
        break;

      case 4:
        if (this.partnersCsvRows().length) {
          await this.svc.bulkImportPartners(this.partnersCsvRows() as any).catch(() => {});
        }
        break;

      case 5:
        await this.svc.createWarehouse({
          name:           this.warehouse.name,
          code:           this.warehouse.code,
          warehouse_type: this.warehouse.type as any,
          address:        this.warehouse.address,
        }).catch(() => {});
        break;

      case 6:
        if (this.collaboratorsCsvRows().length) {
          await this.svc.bulkImportCollaborators(this.collaboratorsCsvRows() as any).catch(() => {});
        }
        break;

      case 7:
        if (!this.skipMes && this.facility.name) {
          await this.svc.createFacility({ ...this.facility }).catch(() => {});
        }
        break;
    }
  }
}
