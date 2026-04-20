import { Component, ChangeDetectionStrategy, signal, inject, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MasterDataService, Partner } from '../../core/services/master-data.service';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-price-import-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatFormFieldModule,
    FormsModule
  ],
  template: `
    <div class="p-8 bg-surface-bg text-surface-text rounded-3xl border border-surface-border shadow-2xl relative overflow-hidden">
      <!-- Glow Accent -->
      <div class="absolute -top-24 -right-24 w-48 h-48 bg-primary/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div class="flex justify-between items-center mb-8 relative z-10">
        <h2 class="text-2xl font-black text-primary flex items-center gap-3 tracking-tighter uppercase italic">
          <mat-icon class="text-3xl">terminal</mat-icon> 
          Control Tower B2B
        </h2>
        <button (click)="dialogRef.close()" class="p-2 hover:bg-surface-border rounded-xl transition-colors text-surface-text-muted">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <div class="mb-8 bg-surface-card/50 p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-end justify-between border border-surface-border gap-6 relative z-10">
        <div class="flex flex-col md:flex-row gap-6 w-full flex-1">
          <div class="flex flex-col gap-2 flex-1">
            <span class="text-[10px] uppercase tracking-[0.2em] text-surface-text-muted font-black">Contexto de Carga</span>
            <select class="bg-surface-bg border border-surface-border text-surface-text text-xs font-bold rounded-xl focus:ring-amber-500 focus:border-amber-500 block w-full px-4 py-3 outline-none appearance-none cursor-pointer hover:bg-surface-card transition-colors"
                    [(ngModel)]="importMode" (change)="onModeChange()">
              <option value="GENERAL">Precios Generales</option>
              <option value="AGREEMENT">Contratos por Entidad</option>
            </select>
          </div>

          <div class="flex flex-col gap-2 flex-1" *ngIf="importMode === 'AGREEMENT'">
            <span class="text-[10px] uppercase tracking-[0.2em] text-surface-text-muted font-black">Entidad Legal</span>
            <select class="bg-surface-bg border border-surface-border text-surface-text text-xs font-bold rounded-xl focus:ring-amber-500 focus:border-amber-500 block w-full px-4 py-3 outline-none appearance-none cursor-pointer hover:bg-surface-card transition-colors"
                    [(ngModel)]="selectedEntity">
              <option [value]="null" disabled selected>Seleccione Cliente/Proveedor...</option>
              <option *ngFor="let p of partners()" [value]="p.id">{{p.code}} - {{p.name}}</option>
            </select>
          </div>
        </div>

        <button class="flex items-center gap-3 px-8 py-3.5 rounded-xl border-2 border-primary/50 text-primary hover:bg-primary hover:text-surface-bg transition-all duration-300 disabled:opacity-30 disabled:grayscale font-black uppercase text-[10px] tracking-widest shadow-lg shadow-primary/10 min-w-[180px] justify-center"
                [disabled]="importMode === 'AGREEMENT' && !selectedEntity"
                (click)="downloadTemplate()">
          <mat-icon class="scale-110">cloud_download</mat-icon> 
          <span>Bajar Plantilla</span>
        </button>
      </div>

      <!-- Drag & Drop Zone -->
      <div 
        class="border-2 border-dashed border-surface-border rounded-3xl p-12 flex flex-col items-center justify-center transition-all duration-500 cursor-pointer bg-surface-card/30 hover:bg-primary/5 hover:border-primary/50 relative z-10 group"
        [class.!border-primary]="isDragging()"
        [class.!bg-primary/10]="isDragging()"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        (drop)="onDrop($event)"
        (click)="fileInput.click()"
      >
        <div class="w-16 h-16 bg-surface-bg rounded-2xl flex items-center justify-center mb-6 shadow-sm group-hover:scale-110 transition-transform duration-500">
           <mat-icon class="text-4xl text-surface-text-muted group-hover:text-primary transition-colors">upload_file</mat-icon>
        </div>
        <p class="text-sm text-surface-text font-black uppercase tracking-widest italic">Arrastra la matriz de precios aquí</p>
        <p class="text-[10px] text-surface-text-muted mt-2 font-mono">UTF-8 / LATIN1 (.CSV)</p>
        <input type="file" #fileInput (change)="onFileSelected($event)" accept=".csv" class="hidden">
      </div>

      <!-- File Details & Upload Action -->
      <div *ngIf="selectedFile()" class="mt-6 flex flex-col md:flex-row items-center justify-between bg-primary/5 p-5 rounded-2xl border border-primary/20 relative z-10 animate-fade-in gap-4">
        <div class="flex items-center gap-4">
          <div class="h-12 w-12 rounded-xl bg-primary/20 flex items-center justify-center text-primary">
            <mat-icon>description</mat-icon>
          </div>
          <div class="flex flex-col">
            <span class="font-black text-[11px] text-surface-text truncate max-w-[200px] uppercase tracking-tighter">{{selectedFile()?.name}}</span>
            <span class="text-[9px] text-surface-text-muted font-bold">{{(selectedFile()!.size / 1024).toFixed(2)}} KB</span>
          </div>
        </div>
        
        <button class="w-full md:w-auto flex items-center justify-center gap-3 px-8 py-3.5 rounded-xl bg-primary text-surface-bg font-black uppercase text-[10px] tracking-[0.2em] transition-all shadow-xl shadow-primary/30 hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:grayscale"
                [disabled]="isUploading()" 
                (click)="uploadFile()">
          <ng-container *ngIf="!isUploading()">
            <mat-icon class="scale-110">rocket_launch</mat-icon>
            Procesar Transacción
          </ng-container>
          <ng-container *ngIf="isUploading()">
            <mat-spinner diameter="18" strokeWidth="3" class="mr-2"></mat-spinner>
            Sincronizando...
          </ng-container>
        </button>
      </div>

      <!-- Results Matrix -->
      <div *ngIf="results()" class="mt-8 border-t border-surface-border pt-8 animate-fade-in relative z-10">
        <div class="flex items-center gap-2 mb-6">
          <mat-icon class="text-primary scale-75">analytics</mat-icon>
          <h3 class="text-[10px] font-black uppercase tracking-[0.3em] text-surface-text-muted">Matriz de Resultados</h3>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div class="bg-surface-card border-l-4 border-emerald-500 p-6 rounded-2xl shadow-sm">
            <span class="text-[9px] text-surface-text-muted uppercase font-black tracking-widest mb-1 block">Inmutabilidad Creada</span>
            <span class="text-4xl font-black text-emerald-500 tracking-tighter font-mono">{{results()?.procesados || 0}}</span>
          </div>
          <div class="bg-surface-card border-l-4 border-red-500 p-6 rounded-2xl shadow-sm">
            <span class="text-[9px] text-surface-text-muted uppercase font-black tracking-widest mb-1 block">Integridad Fallida</span>
            <span class="text-4xl font-black text-red-500 tracking-tighter font-mono">{{results()?.errores?.length || 0}}</span>
          </div>
        </div>

        <div *ngIf="results()?.errores?.length" class="mt-4 bg-red-500/5 border border-red-500/20 rounded-2xl overflow-hidden shadow-inner">
          <div class="bg-red-500/10 px-6 py-3 border-b border-red-500/20 flex justify-between items-center">
            <span class="text-[9px] font-black uppercase tracking-widest text-red-600">Detalle Forense</span>
            <mat-icon class="text-red-500 scale-75">bug_report</mat-icon>
          </div>
          <div class="max-h-48 overflow-y-auto custom-scrollbar">
            <table class="w-full text-left">
              <tbody class="divide-y divide-red-500/10">
                <tr *ngFor="let err of results()?.errores" class="hover:bg-red-500/5 transition-colors">
                  <td class="px-6 py-3 w-32 text-red-700/60 font-mono text-[10px] font-bold">LÍNEA {{err.fila}}</td>
                  <td class="px-6 py-3 font-bold text-xs text-red-700">{{err.error}}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
    ::ng-deep .mat-mdc-dialog-container .mdc-dialog__surface {
        background: transparent !important;
        box-shadow: none !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class PriceImportDashboardComponent {
  public dialogRef = inject(MatDialogRef<PriceImportDashboardComponent>);
  private msData = inject(MasterDataService);

  public importMode: 'GENERAL' | 'AGREEMENT' = 'GENERAL';
  public partners = signal<Partner[]>([]);
  public selectedEntity: string | null = null;

  public isDragging = signal(false);
  public selectedFile = signal<File | null>(null);
  public isUploading = signal(false);
  public results = signal<{procesados?: number, errores?: any[]} | null>(null);

  @ViewChild('fileInput') fileInput!: ElementRef;

  constructor() {
    this.loadPartners();
  }

  async loadPartners() {
    try {
      const res = await firstValueFrom(this.msData.getPartners());
      this.partners.set(res.data);
    } catch(e) {}
  }

  onModeChange() {
    this.selectedEntity = null;
  }

  downloadTemplate() {
    if (this.importMode === 'GENERAL') {
      this.msData.downloadPriceTemplate();
    } else {
      if (this.selectedEntity) {
        this.msData.downloadPriceTemplate(this.selectedEntity);
      }
    }
  }

  onDragOver(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent) {
    event.preventDefault();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    this.handleFiles(files);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    this.handleFiles(input.files);
  }

  private handleFiles(files: FileList | null | undefined) {
    if (files && files.length > 0) {
      if (files[0].name.toLowerCase().endsWith('.csv')) {
        this.selectedFile.set(files[0]);
        this.results.set(null);
      } else {
        alert('Formato de seguridad invalido. Solo archivos .csv permitidos.');
      }
    }
  }

  async uploadFile() {
    const file = this.selectedFile();
    if (!file) return;

    this.isUploading.set(true);
    this.results.set(null);
    
    try {
      const res = await firstValueFrom(this.msData.importPrices(file));
      this.results.set(res.data);
      
      // If success reset the file selection context
      if (res.data.errores?.length === 0) {
          setTimeout(() => {
              this.selectedFile.set(null);
          }, 3000); // give them 3s to read the success
      }
      
    } catch (e: any) {
      this.results.set({
        procesados: 0,
        errores: [{fila: 'SYS', error: e.message || 'Error de conexión / Timeout'}]
      });
    } finally {
      this.isUploading.set(false);
    }
  }
}
