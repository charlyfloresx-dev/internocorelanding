import { Component, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { NotificationService } from '../../core/services/notification.service';
import { SideDrawerService } from '../../core/services/side-drawer.service';
import { FacilityRead, ProductionAreaRead } from '../../core/models/mes.types';

@Component({
  selector: 'app-production-area-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full bg-surface-bg animate-fade-in">

      <!-- Header -->
      <div class="mb-8 p-1">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-sky-500/10 rounded-2xl flex items-center justify-center text-sky-400 border border-sky-500/20">
            <mat-icon class="text-2xl">account_tree</mat-icon>
          </div>
          <div>
            <h2 class="text-xl font-black text-surface-text tracking-tighter uppercase italic leading-none">
              Estructura de Planta
            </h2>
            <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest mt-1">
              FACILIDADES · ÁREAS DE PRODUCCIÓN
            </p>
          </div>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-8">

        <!-- ─── FACILITIES ──────────────────────────────────────────────── -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black text-surface-text uppercase tracking-widest flex items-center gap-2">
              <mat-icon class="text-sm text-sky-400">factory</mat-icon>
              Facilidades (Plantas)
            </h3>
            <button (click)="showFacilityForm.set(!showFacilityForm())"
              class="text-[9px] text-primary font-black uppercase tracking-widest flex items-center gap-1 hover:opacity-70 transition-opacity">
              <mat-icon class="text-xs">{{ showFacilityForm() ? 'remove' : 'add' }}</mat-icon>
              Nueva Facilidad
            </button>
          </div>

          @if (showFacilityForm()) {
            <div class="p-4 bg-surface-card rounded-2xl border border-primary/20 space-y-3 mb-4">
              <div class="grid grid-cols-2 gap-3">
                <div class="space-y-1">
                  <label class="text-[8px] text-surface-text-muted uppercase font-bold">Código *</label>
                  <input [(ngModel)]="newFacility.code" type="text" maxlength="25" placeholder="PLT-TIJ"
                    class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs font-mono outline-none focus:border-primary transition-all uppercase" />
                </div>
                <div class="space-y-1">
                  <label class="text-[8px] text-surface-text-muted uppercase font-bold">Nombre *</label>
                  <input [(ngModel)]="newFacility.name" type="text" placeholder="Planta Tijuana"
                    class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs outline-none focus:border-primary transition-all" />
                </div>
                <div class="col-span-2 space-y-1">
                  <label class="text-[8px] text-surface-text-muted uppercase font-bold">Ubicación</label>
                  <input [(ngModel)]="newFacility.location" type="text" placeholder="Tijuana, BC, México"
                    class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs outline-none focus:border-primary transition-all" />
                </div>
              </div>
              <button (click)="createFacility()" [disabled]="!newFacility.code || !newFacility.name || creatingFacility()"
                class="w-full py-2.5 bg-sky-500/20 hover:bg-sky-500/30 text-sky-400 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                <mat-icon class="text-xs">{{ creatingFacility() ? 'sync' : 'add' }}</mat-icon>
                Registrar Facilidad
              </button>
            </div>
          }

          <div class="space-y-2">
            @if (facilitiesLoading()) {
              <div class="h-16 bg-surface-card rounded-xl animate-pulse"></div>
            } @else {
              @for (f of facilities(); track f.id) {
                <div class="flex items-center gap-3 px-4 py-3 bg-surface-card border border-surface-border rounded-xl">
                  <mat-icon class="text-sm text-sky-400">factory</mat-icon>
                  <div class="flex-1">
                    <span class="text-xs font-bold text-primary font-mono">{{ f.code }}</span>
                    <span class="text-xs text-surface-text ml-3">{{ f.name }}</span>
                    @if (f.location_description) {
                      <div class="text-[9px] text-surface-text-muted">{{ f.location_description }}</div>
                    }
                  </div>
                </div>
              } @empty {
                <p class="text-[10px] text-surface-text-muted italic text-center py-4">Sin facilidades configuradas</p>
              }
            }
          </div>
        </section>

        <!-- ─── PRODUCTION AREAS ────────────────────────────────────────── -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black text-surface-text uppercase tracking-widest flex items-center gap-2">
              <mat-icon class="text-sm text-emerald-400">hub</mat-icon>
              Áreas de Producción
            </h3>
            <button (click)="showAreaForm.set(!showAreaForm())"
              class="text-[9px] text-primary font-black uppercase tracking-widest flex items-center gap-1 hover:opacity-70 transition-opacity">
              <mat-icon class="text-xs">{{ showAreaForm() ? 'remove' : 'add' }}</mat-icon>
              Nueva Área
            </button>
          </div>

          @if (showAreaForm()) {
            <div class="p-4 bg-surface-card rounded-2xl border border-primary/20 space-y-3 mb-4">
              <div class="space-y-1">
                <label class="text-[8px] text-surface-text-muted uppercase font-bold">Nombre del Área *</label>
                <input [(ngModel)]="newArea.name" type="text" placeholder="Líneas de Ensamble"
                  class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs outline-none focus:border-primary transition-all" />
              </div>
              <div class="space-y-1">
                <label class="text-[8px] text-surface-text-muted uppercase font-bold">Descripción</label>
                <input [(ngModel)]="newArea.description" type="text" placeholder="Descripción opcional..."
                  class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs outline-none focus:border-primary transition-all" />
              </div>
              <div class="space-y-1">
                <label class="text-[8px] text-surface-text-muted uppercase font-bold">Facilidad</label>
                <select [(ngModel)]="newArea.facility_id"
                  class="w-full bg-surface-bg border border-surface-border rounded-lg p-2.5 text-xs cursor-pointer outline-none focus:border-primary transition-all">
                  <option value="">— Sin facilidad —</option>
                  @for (f of facilities(); track f.id) {
                    <option [value]="f.id">{{ f.code }} — {{ f.name }}</option>
                  }
                </select>
              </div>
              <button (click)="createArea()" [disabled]="!newArea.name || creatingArea()"
                class="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                <mat-icon class="text-xs">{{ creatingArea() ? 'sync' : 'add' }}</mat-icon>
                Registrar Área
              </button>
            </div>
          }

          <div class="space-y-2">
            @if (areasLoading()) {
              <div class="h-16 bg-surface-card rounded-xl animate-pulse"></div>
            } @else {
              @for (a of areas(); track a.id) {
                <div class="flex items-center gap-3 px-4 py-3 bg-surface-card border border-surface-border rounded-xl">
                  <mat-icon class="text-sm text-emerald-400">hub</mat-icon>
                  <div class="flex-1">
                    <div class="text-xs font-bold text-surface-text">{{ a.name }}</div>
                    @if (a.description) {
                      <div class="text-[9px] text-surface-text-muted">{{ a.description }}</div>
                    }
                    @if (facilityName(a.facility_id)) {
                      <div class="text-[9px] text-sky-400 font-mono">{{ facilityName(a.facility_id) }}</div>
                    }
                  </div>
                </div>
              } @empty {
                <p class="text-[10px] text-surface-text-muted italic text-center py-4">Sin áreas configuradas</p>
              }
            }
          </div>
        </section>

      </div>

      <!-- Footer -->
      <div class="pt-6 mt-auto border-t border-surface-border">
        <button type="button" (click)="drawer.close()"
          class="w-full py-4 border border-surface-border rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-surface-border transition-all">
          Cerrar
        </button>
      </div>

    </div>
  `,
  styles: [`:host { display: block; }`]
})
export class ProductionAreaFormComponent implements OnInit {
  private http  = inject(HttpClient);
  private notif = inject(NotificationService);
  drawer        = inject(SideDrawerService);

  private base = `${environment.productionUrl}/mes/resources`;

  facilities = signal<FacilityRead[]>([]);
  areas      = signal<ProductionAreaRead[]>([]);
  facilitiesLoading = signal(false);
  areasLoading      = signal(false);
  creatingFacility  = signal(false);
  creatingArea      = signal(false);
  showFacilityForm  = signal(false);
  showAreaForm      = signal(false);

  newFacility = { code: '', name: '', location: '' };
  newArea     = { name: '', description: '', facility_id: '' };

  async ngOnInit() {
    await Promise.all([this.loadFacilities(), this.loadAreas()]);
  }

  async loadFacilities() {
    this.facilitiesLoading.set(true);
    try {
      const resp: any = await lastValueFrom(this.http.get(`${this.base}/facilities`));
      this.facilities.set(resp?.data ?? resp ?? []);
    } finally { this.facilitiesLoading.set(false); }
  }

  async loadAreas() {
    this.areasLoading.set(true);
    try {
      const resp: any = await lastValueFrom(this.http.get(`${this.base}/production-areas`));
      this.areas.set(resp?.data ?? resp ?? []);
    } finally { this.areasLoading.set(false); }
  }

  facilityName(facilityId?: string | null): string {
    if (!facilityId) return '';
    const f = this.facilities().find(f => f.id === facilityId);
    return f ? `${f.code} — ${f.name}` : '';
  }

  async createFacility() {
    if (!this.newFacility.code || !this.newFacility.name) return;
    this.creatingFacility.set(true);
    try {
      await lastValueFrom(this.http.post(`${this.base}/facilities`, {
        code: this.newFacility.code.toUpperCase(),
        name: this.newFacility.name,
        location_description: this.newFacility.location || null,
      }));
      this.notif.success('Facilidad creada', this.newFacility.name);
      this.newFacility = { code: '', name: '', location: '' };
      this.showFacilityForm.set(false);
      this.drawer.notifyRefresh();
      await this.loadFacilities();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo crear la facilidad');
    } finally { this.creatingFacility.set(false); }
  }

  async createArea() {
    if (!this.newArea.name) return;
    this.creatingArea.set(true);
    try {
      await lastValueFrom(this.http.post(`${this.base}/production-areas`, {
        name: this.newArea.name,
        description: this.newArea.description || null,
        facility_id: this.newArea.facility_id || null,
      }));
      this.notif.success('Área creada', this.newArea.name);
      this.newArea = { name: '', description: '', facility_id: '' };
      this.showAreaForm.set(false);
      this.drawer.notifyRefresh();
      await this.loadAreas();
    } catch (err: any) {
      this.notif.error('Error', err?.error?.detail ?? 'No se pudo crear el área');
    } finally { this.creatingArea.set(false); }
  }
}
