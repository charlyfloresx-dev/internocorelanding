import { Component, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { OnboardingService } from '@services/onboarding.service';
import { AuthService } from '@services/auth.service';

@Component({
  selector: 'app-onboarding-wizard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen bg-slate-950 flex items-center justify-center p-6 relative overflow-hidden">
      <!-- Background Effects -->
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black"></div>
      <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-sky-500 via-purple-500 to-sky-500 opacity-30"></div>

      <div class="w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl relative z-10 flex flex-col md:flex-row overflow-hidden animate-fade-in-up">
        
        <!-- Sidebar / Progress -->
        <div class="w-full md:w-1/3 bg-slate-950 p-8 border-r border-slate-800 flex flex-col justify-between">
          <div>
            <div class="flex items-center gap-3 mb-8">
              <div class="w-10 h-10 rounded-lg bg-sky-600 flex items-center justify-center text-white shadow-lg shadow-sky-900/50">
                <i class="fa-solid fa-wand-magic-sparkles"></i>
              </div>
              <h1 class="font-bold text-white text-xl tracking-tight">Setup Wizard</h1>
            </div>

            <div class="space-y-6 relative">
              <!-- Step Line -->
              <div class="absolute left-3.5 top-2 bottom-2 w-0.5 bg-slate-800 -z-10"></div>

              @for (step of steps; track step.id) {
                <div class="flex items-center gap-4 group" [class.opacity-50]="service.state().step < step.id">
                  <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all duration-300 z-10"
                       [ngClass]="{
                         'bg-sky-600 border-sky-600 text-white': service.state().step >= step.id,
                         'bg-slate-900 border-slate-700 text-slate-500': service.state().step < step.id,
                         'ring-4 ring-sky-500/20': service.state().step === step.id
                       }">
                    {{ step.id }}
                  </div>
                  <div>
                    <div class="text-sm font-bold text-slate-200">{{ step.title }}</div>
                    <div class="text-xs text-slate-500">{{ step.desc }}</div>
                  </div>
                </div>
              }
            </div>
          </div>

          <div class="mt-8 pt-6 border-t border-slate-800">
            <div class="flex items-center gap-3">
              <img [src]="auth.currentUser()?.avatar" class="w-8 h-8 rounded-full border border-slate-700">
              <div class="text-xs">
                <div class="text-slate-400">Configurando como</div>
                <div class="text-white font-bold">{{ auth.currentUser()?.email }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content -->
        <div class="flex-1 p-8 md:p-12 flex flex-col">
          
          <!-- Step 1: Company Info -->
          @if (service.state().step === 1) {
            <div class="flex-1 animate-fade-in">
              <h2 class="text-2xl font-bold text-white mb-2">Perfil de la Empresa</h2>
              <p class="text-slate-400 mb-8">Comencemos con los datos básicos de tu organización.</p>

              <div class="space-y-4">
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Nombre Comercial</label>
                  <input type="text" [ngModel]="service.state().companyName" (ngModelChange)="service.updateState({companyName: $event})"
                         class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-sky-500 focus:ring-1 focus:ring-sky-500 outline-none transition-all"
                         placeholder="Ej. Acme Manufacturing">
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-500 uppercase mb-2">Industria</label>
                  <select [ngModel]="service.state().industry" (ngModelChange)="service.updateState({industry: $event})"
                          class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:border-sky-500 outline-none">
                    <option value="" disabled selected>Selecciona una industria</option>
                    <option value="automotive">Automotriz</option>
                    <option value="aerospace">Aeroespacial</option>
                    <option value="electronics">Electrónica</option>
                    <option value="food">Alimentos y Bebidas</option>
                    <option value="other">Otra Manufactura</option>
                  </select>
                </div>
              </div>
            </div>
          }

          <!-- Step 2: Modules (Placeholder for brevity) -->
          @if (service.state().step === 2) {
            <div class="flex-1 animate-fade-in">
              <h2 class="text-2xl font-bold text-white mb-2">Módulos Operativos</h2>
              <p class="text-slate-400 mb-8">Selecciona las áreas que deseas gestionar.</p>
              <div class="p-4 bg-slate-800/50 rounded-lg border border-slate-700 text-center text-slate-400">
                <i class="fa-solid fa-cubes-stacked text-3xl mb-2"></i>
                <p>Configuración de módulos simplificada para esta demo.</p>
              </div>
            </div>
          }

          <!-- Footer Actions -->
          <div class="mt-8 flex justify-between items-center pt-6 border-t border-slate-800">
            <button (click)="service.prevStep()" [disabled]="service.state().step === 1"
                    class="px-6 py-2 rounded-lg text-slate-400 hover:text-white font-medium disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              Atrás
            </button>

            @if (service.state().step < 2) {
              <button (click)="service.nextStep()" 
                      class="px-6 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-lg shadow-lg shadow-sky-900/20 transition-all">
                Siguiente <i class="fa-solid fa-arrow-right ml-2"></i>
              </button>
            } @else {
              <button (click)="service.submitOnboarding()" 
                      class="px-8 py-2 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg shadow-lg shadow-green-900/20 transition-all flex items-center gap-2">
                @if (service.loading()) { <i class="fa-solid fa-circle-notch fa-spin"></i> }
                Finalizar Setup
              </button>
            }
          </div>
        </div>
      </div>
    </div>
  `
})
export class OnboardingWizardComponent {
  public service = inject(OnboardingService);
  public auth = inject(AuthService);

  steps = [
    { id: 1, title: 'Perfil', desc: 'Datos de la empresa' },
    { id: 2, title: 'Módulos', desc: 'Selección de features' }
  ];
}