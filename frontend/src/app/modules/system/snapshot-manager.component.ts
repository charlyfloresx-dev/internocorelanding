
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiSimulationService } from '@services/api-simulation.service';
import { ToastService } from '@services/toast.service';

@Component({
  selector: 'app-snapshot-manager',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      <div class="max-w-4xl mx-auto">
        
        <header class="mb-8">
           <h1 class="text-3xl font-bold text-white tracking-tight">Puntos de Restauración</h1>
           <p class="text-slate-400">Gestiona copias de seguridad de los datos del proyecto</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          <!-- EXPORT CARD -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl group hover:border-sky-500/50 transition-all">
             <div class="w-16 h-16 bg-sky-500/10 rounded-2xl flex items-center justify-center text-sky-500 mb-6 group-hover:scale-110 transition-transform">
               <i class="fa-solid fa-cloud-arrow-down text-3xl"></i>
             </div>
             <h3 class="text-xl font-bold text-white mb-2">Crear Backup</h3>
             <p class="text-slate-400 text-sm mb-6 leading-relaxed">Genera un archivo JSON con el estado actual de documentos, inventarios, almacenes y socios comerciales.</p>
             
             <button (click)="exportData()" class="w-full py-3 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-xl shadow-lg shadow-sky-900/20 transition-all flex items-center justify-center gap-2">
               <i class="fa-solid fa-download"></i> Descargar Snapshot
             </button>
          </div>

          <!-- IMPORT CARD -->
          <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl group hover:border-emerald-500/50 transition-all">
             <div class="w-16 h-16 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-500 mb-6 group-hover:scale-110 transition-transform">
               <i class="fa-solid fa-cloud-arrow-up text-3xl"></i>
             </div>
             <h3 class="text-xl font-bold text-white mb-2">Restaurar Datos</h3>
             <p class="text-slate-400 text-sm mb-6 leading-relaxed">Carga un archivo de snapshot previamente descargado para sobrescribir los datos actuales del sistema.</p>
             
             <label class="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-900/20 transition-all flex items-center justify-center gap-2 cursor-pointer">
               <i class="fa-solid fa-upload"></i> Cargar Archivo
               <input type="file" (change)="importData($event)" class="hidden" accept=".json">
             </label>
          </div>

        </div>

        <!-- INFO BOX -->
        <div class="mt-8 p-6 bg-slate-800/50 border border-slate-700 rounded-xl flex gap-4">
           <i class="fa-solid fa-circle-info text-sky-500 text-xl"></i>
           <div class="text-sm text-slate-300">
             <p class="font-bold text-white mb-1">¿Para qué sirve esto?</p>
             <p>Este sistema es ideal para guardar estados de prueba o para mover tus datos de un entorno a otro sin perder la trazabilidad de los documentos que has creado.</p>
           </div>
        </div>

      </div>
    </div>
  `
})
export class SnapshotManagerComponent {
  api = inject(ApiSimulationService);
  toast = inject(ToastService);

  exportData() {
    const state = this.api.getFullState();
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `InternoCore_Snapshot_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    this.toast.success("Snapshot generado y descargado.");
  }

  importData(event: any) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e: any) => {
      try {
        const json = JSON.parse(e.target.result);
        const success = this.api.loadFullState(json);
        if (success) {
          this.toast.success("Sistema restaurado con éxito.");
          setTimeout(() => window.location.reload(), 1500);
        } else {
          this.toast.error("Formato de archivo inválido.");
        }
      } catch (err) {
        this.toast.error("Error al procesar el archivo.");
      }
    };
    reader.readAsText(file);
  }
}
