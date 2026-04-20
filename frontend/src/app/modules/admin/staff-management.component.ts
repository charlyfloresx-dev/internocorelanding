import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { StaffService } from '../../core/services/staff.service';
import { ToastService } from '../../core/services/toast.service';
import { TranslationService } from '../../core/services/translation.service';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-staff-management',
  standalone: true,
  imports: [CommonModule, MatIconModule, TranslatePipe],
  template: `
    <div class="p-12 space-y-12 animate-fade-in bg-[#fdfdfd] min-h-screen">
      <!-- Header -->
      <div class="flex justify-between items-end">
        <div>
          <h2 class="text-5xl font-black text-slate-900 uppercase tracking-tighter italic leading-tight">
            {{ 'staff.title' | translate:'Gestión de Planta' }}
          </h2>
          <p class="text-slate-500 text-[11px] font-mono uppercase tracking-[0.3em] mt-2 flex items-center gap-2">
            <span class="w-8 h-[1px] bg-primary"></span>
            {{ 'staff.subtitle' | translate:'Control de Identidad Física y Colaboradores' }}
          </p>
        </div>
        
        <button 
          (click)="downloadTemplate()"
          class="group px-6 py-3 rounded-2xl border-2 border-slate-900 text-slate-900 font-black text-[10px] uppercase tracking-widest hover:bg-slate-900 hover:text-white transition-all flex items-center gap-3 active:scale-95"
        >
          <mat-icon class="text-lg" style="width: 20px; height: 20px; font-size: 20px;">download</mat-icon>
          {{ 'staff.download_template' | translate:'Descargar Plantilla CSV' }}
        </button>
      </div>

      <!-- Bulk Action Area -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        <!-- Upload Card -->
        <div class="bg-white rounded-[3rem] p-10 border border-slate-200 shadow-[0_20px_50px_rgba(0,0,0,0.03)] relative overflow-hidden group">
          <!-- Background Decorative -->
          <div class="absolute -top-20 -right-20 w-64 h-64 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-colors"></div>
          
          <div class="relative z-10 space-y-8">
            <div class="w-16 h-16 bg-slate-50 rounded-3xl flex items-center justify-center text-primary border border-slate-100 group-hover:scale-110 transition-transform duration-500">
              <mat-icon class="!text-3xl" style="width: 30px; height: 30px; font-size: 30px;">upload_file</mat-icon>
            </div>
            
            <div>
              <h3 class="text-2xl font-black text-slate-900 uppercase tracking-tighter">{{ 'staff.bulk_upload' | translate:'Carga Masiva' }}</h3>
              <p class="text-slate-500 text-xs mt-2 leading-relaxed">
                {{ 'staff.bulk_description' | translate:'Sincroniza la base de datos de colaboradores. El sistema procesará identificadores internos, tags RFID y roles de supervisión automáticamente.' }}
              </p>
            </div>

            <!-- Custom File Input -->
            <label class="block cursor-pointer">
              <div class="border-2 border-dashed border-slate-200 rounded-[2rem] p-12 text-center hover:border-primary hover:bg-primary/[0.02] transition-all group/drop">
                <input type="file" (change)="onFileSelected($event)" class="hidden" accept=".csv">
                <mat-icon class="text-slate-300 group-hover/drop:text-primary transition-colors !text-5xl !w-12 !h-12 mb-4" style="width: 48px; height: 48px; font-size: 48px;">cloud_upload</mat-icon>
                <p class="text-[10px] font-black text-slate-400 group-hover/drop:text-slate-600 uppercase tracking-widest">
                  {{ selectedFile ? selectedFile.name : ('staff.drop_instruction' | translate:'Arrastra tu archivo CSV o haz clic aquí') }}
                </p>
              </div>
            </label>

            <button 
              (click)="upload()"
              [disabled]="!selectedFile || uploading()"
              class="w-full py-5 bg-primary text-white rounded-2xl font-black text-[11px] uppercase tracking-[0.2em] shadow-[0_15px_30px_rgba(0,229,255,0.3)] hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-20 disabled:grayscale disabled:scale-100"
            >
              {{ uploading() ? ('staff.processing' | translate:'Procesando...') : ('staff.execute_sync' | translate:'Ejecutar Sincronización') }}
            </button>
          </div>
        </div>

        <!-- Instructions / Help -->
        <div class="bg-slate-900 rounded-[3rem] p-10 text-white shadow-2xl space-y-8 relative overflow-hidden">
          <div class="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-primary via-transparent to-transparent"></div>
          
          <div class="relative z-10 flex flex-col h-full justify-between">
            <div class="space-y-6">
              <div class="inline-flex items-center gap-3 px-4 py-2 bg-white/10 rounded-full border border-white/10">
                <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                <span class="text-[9px] font-black uppercase tracking-widest text-primary">{{ 'staff.docs' | translate:'Guía de Carga' }}</span>
              </div>
              
              <h3 class="text-3xl font-black uppercase tracking-tight italic">{{ 'staff.check_list' | translate:'Estructura de Datos' }}</h3>
              
              <div class="space-y-4">
                <div class="flex gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <span class="font-mono text-primary font-black">01</span>
                  <div>
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-300">internal_id</p>
                    <p class="text-[10px] text-slate-500 mt-1 uppercase">{{ 'staff.help_id' | translate:'ID del empleado en su sistema externo.' }}</p>
                  </div>
                </div>
                <div class="flex gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <span class="font-mono text-primary font-black">02</span>
                  <div>
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-300">rfid_tag / pin_code</p>
                    <p class="text-[10px] text-slate-500 mt-1 uppercase">{{ 'staff.help_creds' | translate:'Identidad física. No se requieren ambos.' }}</p>
                  </div>
                </div>
                <div class="flex gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 transition-colors">
                  <span class="font-mono text-primary font-black">03</span>
                  <div>
                    <p class="text-[10px] font-black uppercase tracking-widest text-slate-300">home_warehouse_id</p>
                    <p class="text-[10px] text-slate-500 mt-1 uppercase">{{ 'staff.help_warehouse' | translate:'UUID del almacén (Consultar en Configuración).' }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="p-6 bg-primary/10 rounded-2xl border border-primary/20 mt-8">
              <p class="text-[9px] font-black text-primary uppercase tracking-[0.2em] leading-relaxed italic">
                {{ 'staff.security_notice' | translate:'Aviso: Los datos de identidad (RFID/PIN) son hasheados irreversiblemente antes de su almacenamiento para garantizar el cumplimiento de normativas de seguridad física.' }}
              </p>
            </div>
          </div>
        </div>

      </div>

      <!-- Results Display (Optional if something was uploaded) -->
      @if (lastResults()) {
        <div class="bg-white rounded-[2rem] border border-slate-200 p-8 flex items-center justify-around animate-fade-in divide-x divide-slate-100">
           <div class="text-center px-8">
             <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">{{ 'staff.results.created' | translate:'Nuevos Registros' }}</p>
             <p class="text-4xl font-black text-emerald-500">{{ lastResults().created }}</p>
           </div>
           <div class="text-center px-8">
             <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">{{ 'staff.results.updated' | translate:'Actualizados' }}</p>
             <p class="text-4xl font-black text-primary">{{ lastResults().updates }}</p>
           </div>
           <div class="text-center px-8">
             <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">{{ 'staff.results.errors' | translate:'Incidentes' }}</p>
             <p class="text-4xl font-black" [class.text-rose-500]="lastResults()?.errors?.length > 0" [class.text-slate-200]="lastResults()?.errors?.length === 0">
               {{ lastResults()?.errors?.length }}
             </p>
           </div>
        </div>

        @if (lastResults()?.errors?.length > 0) {
          <div class="bg-rose-50 border border-rose-100 rounded-[2rem] p-6 space-y-3">
             <h4 class="text-[10px] font-black text-rose-600 uppercase tracking-widest flex items-center gap-2">
               <mat-icon class="text-sm" style="width: 14px; height: 14px; font-size: 14px;">warning</mat-icon>
               {{ 'staff.log_errors' | translate:'Log de Errores en Carga' }}
             </h4>
             <ul class="space-y-1">
               @for (err of lastResults().errors; track err) {
                 <li class="text-[10px] font-mono text-rose-400 uppercase tracking-tight">• {{ err }}</li>
               }
             </ul>
          </div>
        }
      }
    </div>
  `,
  styles: [`
    :host { display: block; }
    .animate-fade-in { animation: fadeIn 0.5s ease-out; }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }
  `]
})
export class StaffManagementComponent {
  private staffService = inject(StaffService);
  private toastService = inject(ToastService);
  
  selectedFile: File | null = null;
  uploading = signal(false);
  lastResults = signal<any>(null);

  downloadTemplate() {
    this.staffService.downloadTemplate();
    this.toastService.info('Descargando plantilla...', 'Sistema de Planta');
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
    }
  }

  upload() {
    if (!this.selectedFile) return;
    
    this.uploading.set(true);
    this.staffService.bulkUpload(this.selectedFile).subscribe({
      next: (res) => {
        this.uploading.set(false);
        this.lastResults.set(res.data);
        this.selectedFile = null;
        this.toastService.success('Sincronización completada exitosamente', 'Staff Management');
      },
      error: (err) => {
        this.uploading.set(false);
        this.toastService.error('Error durante la sincronización: ' + (err.error?.detail || 'Error desconocido'), 'Sistema');
      }
    });
  }
}
