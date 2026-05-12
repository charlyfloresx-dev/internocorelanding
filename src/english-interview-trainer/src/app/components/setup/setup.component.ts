import { Component, inject, signal, CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { JobService } from '../../core/job.service';
import { InterviewService } from '../../core/interview.service';
import { GoogleAuthService } from '../../core/google-auth.service';
import { GeminiService } from '../../core/gemini.service';
import { ProfileService } from '../../core/profile.service';

@Component({
  selector: 'app-setup',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="max-w-4xl mx-auto p-6 md:p-10 min-h-[90vh] flex flex-col justify-center animate-in fade-in duration-1000">
      
      <!-- STEP INDICATOR -->
      <div class="flex items-center justify-center gap-3 sm:gap-4 mb-6 sm:mb-12 transition-all">
        @for (s of [1,2,3,4]; track s) {
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-[10px] sm:text-xs font-black transition-all duration-500"
                 [ngClass]="currentStep === s ? 'bg-primary text-white scale-125 shadow-lg shadow-primary/40' : (currentStep > s ? 'bg-emerald-500 text-white' : 'bg-white/5 text-white/20 border border-white/10')">
              {{ currentStep > s ? '✓' : s }}
            </div>
            @if (s < 4) {
              <div class="w-4 sm:w-8 h-px bg-white/10" [class.bg-emerald-500]="currentStep > s"></div>
            }
          </div>
        }
      </div>

      <!-- STEP 1: GOOGLE AUTH -->
      @if (currentStep === 1) {
        <div class="text-center animate-in slide-in-from-bottom-4 duration-500">
          <h2 class="text-4xl font-black text-white mb-4 tracking-tight">Acceso Identitario</h2>
          <p class="text-surface-muted text-sm uppercase font-bold tracking-[0.3em] mb-10">Paso 1: Conecta tu cuenta para personalizar la experiencia</p>
          
          @if (!auth.isAuthenticated()) {
            <div id="google-setup-login" class="flex justify-center mb-8"></div>
            <p class="text-xs text-white/40 italic">Utilizamos tu nombre y foto para que el entrevistador te reconozca.</p>
          } @else {
            <div class="flex flex-col items-center gap-4 p-8 bg-white/5 border border-white/10 rounded-3xl animate-in zoom-in duration-300">
               <img [src]="auth.user()?.picture" class="w-20 h-20 rounded-2xl border-2 border-primary/50 shadow-2xl" alt="User">
               <div>
                 <p class="text-white font-black text-xl">{{ auth.user()?.name }}</p>
                 <p class="text-white/40 text-xs">{{ auth.user()?.email }}</p>
               </div>
               <button (click)="nextStep()" class="mt-4 px-10 py-3 bg-primary text-white font-black rounded-full hover:scale-105 transition-all">Continuar</button>
            </div>
          }
        </div>
      }

      <!-- STEP 2: API KEY -->
      @if (currentStep === 2) {
        <div class="animate-in slide-in-from-bottom-4 duration-500">
          <div class="text-center mb-8">
            <h2 class="text-4xl font-black text-white mb-2 tracking-tight italic">Motor de Inteligencia</h2>
            <p class="text-surface-muted text-sm uppercase font-bold tracking-[0.3em]">Paso 2: Conecta tu Gemini API Key</p>
          </div>

          <div class="bg-surface-card border border-surface-border rounded-3xl p-8 shadow-2xl relative">
            <p class="text-sm text-white/70 mb-6 leading-relaxed">
              Para que Gemini sea 100% tuyo y privado, necesitamos que pegues tu <strong>API Key</strong> de Google AI Studio. 
              Es gratuita y se queda guardada localmente en tu navegador.
            </p>
            
            <div class="flex gap-2 mb-6">
              <input [(ngModel)]="apiKeyStr" type="password" placeholder="AIzaSy..." class="flex-1 bg-black/40 border border-white/10 rounded-xl px-6 py-4 text-white font-mono focus:border-primary outline-none transition-all">
              <button (click)="saveApiKey()" [disabled]="!apiKeyStr.startsWith('AIza')" class="px-8 bg-primary text-white font-black rounded-xl disabled:opacity-20 transition-all">Conectar</button>
            </div>

            <div class="flex justify-between items-center">
              <a href="https://aistudio.google.com/app/apikey" target="_blank" class="flex items-center gap-2 text-primary hover:underline text-sm font-bold">
                <span class="material-icons text-base">open_in_new</span>
                Obtén tu API Key gratuita aquí
              </a>
              <button (click)="prevStep()" class="text-white/40 hover:text-white text-xs font-bold uppercase tracking-widest">Atrás</button>
            </div>
          </div>
        </div>
      }

      <!-- STEP 3: LINKEDIN / PROFILE -->
      @if (currentStep === 3) {
        <div class="animate-in slide-in-from-bottom-4 duration-500">
          <div class="text-center mb-8">
            <h2 class="text-4xl font-black text-white mb-2 tracking-tight italic">Tu Identidad Profesional</h2>
            <p class="text-surface-muted text-sm uppercase font-bold tracking-[0.3em]">Paso 3: Sincroniza tu perfil de LinkedIn</p>
          </div>

          <div class="bg-surface-card border border-surface-border rounded-3xl p-8 shadow-2xl">
            <div class="flex flex-col gap-6">
              <div>
                <label class="text-[10px] font-black text-primary uppercase tracking-widest mb-2 block">LinkedIn Profile URL</label>
                <div class="flex gap-2">
                  <input [(ngModel)]="linkedinUrlStr" type="url" placeholder="https://linkedin.com/in/username" class="flex-1 bg-black/40 border border-white/10 rounded-xl px-6 py-4 text-white focus:border-primary outline-none transition-all">
                  <button (click)="analyzeLinkedIn()" [disabled]="!linkedinUrlStr || isAnalyzing" class="px-8 bg-indigo-600 text-white font-black rounded-xl disabled:opacity-50">
                    {{ isAnalyzing ? 'Analizando...' : 'Analizar' }}
                  </button>
                </div>
              </div>

              <div class="relative">
                <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-white/5"></div></div>
                <div class="relative flex justify-center text-[10px] font-black uppercase text-white/20 tracking-widest"><span class="bg-surface-card px-4">O pega tu CV en texto</span></div>
              </div>

              <textarea [(ngModel)]="profileTextStr" placeholder="Pega aquí el texto de tu CV o perfil..." class="w-full h-40 bg-black/40 border border-white/10 rounded-xl p-6 text-white focus:border-primary outline-none resize-none transition-all"></textarea>
              
              <div class="flex justify-between items-center">
                <button (click)="prevStep()" class="text-white/40 hover:text-white text-xs font-bold uppercase tracking-widest">Cambié de opinión / Atrás</button>
                <button (click)="saveProfileAndNext()" class="px-12 py-4 bg-white text-black font-black uppercase tracking-[0.2em] rounded-full hover:bg-primary hover:text-white transition-all">Guardar Perfil</button>
              </div>
            </div>
          </div>
        </div>
      }

      <!-- STEP 4: FINAL PREP -->
      @if (currentStep === 4) {
        <div class="text-center animate-in zoom-in duration-700 max-w-sm mx-auto">
           <div class="w-20 h-20 sm:w-32 sm:h-32 bg-emerald-500/20 border-2 border-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6 sm:mb-10 shadow-[0_0_60px_rgba(16,185,129,0.3)]">
             <span class="material-icons text-4xl sm:text-6xl text-emerald-500">rocket_launch</span>
           </div>
           <h2 class="text-3xl sm:text-5xl font-black text-white mb-2 sm:mb-4 tracking-tighter">Everything Ready!</h2>
           <p class="text-surface-muted text-[10px] sm:text-sm uppercase font-bold tracking-[0.2em] sm:tracking-[0.4em] mb-6 sm:mb-12">Nivel de Entrenamiento: Inglés Intermedio-Básico</p>
           
           <div class="grid grid-cols-2 gap-3 sm:gap-4 mb-8 sm:mb-12">
              <div class="p-3 sm:p-4 bg-white/5 rounded-2xl border border-white/5">
                <p class="text-[7px] sm:text-[8px] font-black text-primary uppercase mb-1">Candidatus</p>
                <p class="text-[10px] sm:text-xs text-white truncate">{{ auth.user()?.name }}</p>
              </div>
              <div class="p-3 sm:p-4 bg-white/5 rounded-2xl border border-white/5">
                <p class="text-[7px] sm:text-[8px] font-black text-primary uppercase mb-1">Audit Mode</p>
                <p class="text-[10px] sm:text-xs text-white">V3 (Conversational)</p>
              </div>
           </div>

           <button (click)="finalizeSetup()" class="w-full sm:w-auto px-8 sm:px-16 py-4 sm:py-6 bg-primary text-white font-black text-sm sm:text-lg uppercase tracking-[0.2em] sm:tracking-[0.3em] rounded-full hover:shadow-[0_0_80px_rgba(129,140,248,0.6)] transition-all hover:scale-110 active:scale-95">
             Start Interview
           </button>
        </div>
      }

    </div>
  `,
  styles: [`
    :host { display: block; background: radial-gradient(circle at 50% 50%, rgba(129, 140, 248, 0.05) 0%, transparent 100%); }
    textarea { field-sizing: content; }
  `]
})
export class SetupComponent {
  protected auth = inject(GoogleAuthService);
  protected gemini = inject(GeminiService);
  protected profileSvc = inject(ProfileService);
  private interview = inject(InterviewService);

  currentStep = 1;
  apiKeyStr = '';
  linkedinUrlStr = '';
  profileTextStr = '';
  isAnalyzing = false;

  constructor() {
    this.currentStep = this.interview.setupStep();
    
    // Restore saved data
    this.apiKeyStr = this.gemini.userApiKey() || '';
    
    const p = this.profileSvc.profile();
    if (p.profileText) {
      this.profileTextStr = p.profileText;
      if (p.linkedinUrl) this.linkedinUrlStr = p.linkedinUrl;
    }

    // New logic: Jump to final step if profile exists
    // We remove the strict auth check here because GSI is async and might take
    // a second to initialize on hard refresh.
    if (this.currentStep === 1 && this.apiKeyStr && this.profileTextStr) {
      this.currentStep = 4;
    }

    // Initialize Google Login button if not authenticated
    if (!this.auth.isAuthenticated() && this.currentStep === 1) {
      setTimeout(() => this.auth.renderButton('google-setup-login'), 500);
    }
  }

  nextStep() { 
    this.currentStep++;
    this.interview.setupStep.set(this.currentStep);
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.interview.setupStep.set(this.currentStep);
    }
  }

  saveApiKey() {
    if (this.gemini.setApiKey(this.apiKeyStr)) {
      this.nextStep();
    }
  }

  async analyzeLinkedIn() {
    this.isAnalyzing = true;
    try {
      const targetUrl = `https://r.jina.ai/${this.linkedinUrlStr}`;
      const response = await fetch(targetUrl);
      const text = await response.text();

      // Detection of LinkedIn anti-bot measures
      if (text.includes('error 999') || text.includes('LinkedIn Login') || text.includes('Security Check')) {
        alert('LinkedIn ha bloqueado el acceso automático (LinkedIn Anti-Bot Protection). \n\nPor favor, abre tu perfil en el navegador, selecciona todo (Ctrl+A), cápialo y pégalo en el cuadro de texto de abajo.');
        return;
      }

      this.profileTextStr = text;
      console.log('LinkedIn Analysis Successful');
    } catch (e) {
      alert('Error de conexión al analizar LinkedIn. Por favor pega el texto manualmente.');
    } finally {
       this.isAnalyzing = false;
    }
  }

  saveProfileAndNext() {
    this.profileSvc.updateProfile({
      profileText: this.profileTextStr,
      linkedinUrl: this.linkedinUrlStr
    });
    this.nextStep();
  }

  finalizeSetup() {
    this.interview.resetInterview();
    this.interview.isSetupMode.set(false);
  }
}
