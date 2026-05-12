import { Component, inject, ChangeDetectionStrategy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InterviewService } from '../../core/interview.service';
import { AudioService } from '../../core/audio.service';
import { SetupComponent } from '../setup/setup.component';
import { TrainerV2Component } from '../trainer-v2/trainer-v2.component';
import { TrainerV3Component } from '../trainer-v3/trainer-v3.component';
import { FeedbackPanelComponent } from '../feedback-panel/feedback-panel.component';

@Component({
  selector: 'app-main-trainer',
  standalone: true,
  imports: [CommonModule, SetupComponent, TrainerV2Component, TrainerV3Component, FeedbackPanelComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="h-screen bg-surface-bg text-surface-text font-inter flex flex-col overflow-hidden">
      


      <main class="flex-1 relative overflow-hidden">
        @if (interview.isSetupMode()) {
          <div class="w-full h-full overflow-y-auto"><app-setup /></div>
        } @else {
          <div class="w-full h-full">
            @if (mode() === 'v3') {
               <div class="w-full h-full"><app-trainer-v3 /></div>
            } @else if (mode() === 'v2') {
               <!-- DASHBOARD V2 (SIN TOCAR) -->
               <div class="w-full h-full overflow-y-auto scrollbar-hide"><app-trainer-v2 /></div>
            } @else {
               <!-- GUIDED MODE V1 (ULTRA COMPRIMIDO) -->
               <div class="w-full h-full flex flex-col items-center justify-center p-2 md:p-4">
                <div class="w-full max-w-4xl h-[92vh] bg-surface-card border border-surface-border rounded-[24px] shadow-2xl relative flex flex-col overflow-hidden animate-in zoom-in duration-300">
                  
                  <!-- CARD HEADER (MODO NANO) -->
                  <div class="px-4 py-2 bg-black/40 border-b border-white/5 flex items-center justify-between shrink-0">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center font-black text-primary text-sm">Q{{ interview.currentIndex() + 1 }}</div>
                      <span class="text-[7px] font-black uppercase text-white/40 tracking-[0.3em]">{{ currentTab().toUpperCase() }} PHASE</span>
                    </div>

                    <div class="flex items-center gap-2">
                       <button (click)="toggleRecording()" 
                               class="flex items-center gap-2 px-4 py-2 rounded-xl transition-all duration-300 border border-white/10 group shadow-md"
                               [class]="interview.isRecording() ? 'bg-rose-500 text-white' : 'bg-primary text-white border-primary/20 shadow-primary/20'">
                          <span class="material-icons !text-sm">{{ interview.isRecording() ? 'stop' : 'mic' }}</span>
                          <span class="text-[7px] font-black uppercase tracking-widest">{{ interview.isRecording() ? 'STOP' : 'RECORD' }}</span>
                       </button>

                       <button (click)="audio.readText(interview.currentQuestion().questionEn)" 
                               class="w-8 h-8 rounded-lg bg-white/5 hover:bg-primary/20 flex items-center justify-center transition-all border border-white/5 text-primary">
                           <span class="material-icons !text-sm">volume_up</span>
                       </button>
                    </div>
                  </div>

                  <!-- CONTENT (DENSIDAD MÁXIMA) -->
                  <div class="flex-1 overflow-y-auto p-4 md:p-6 custom-scrollbar focus:outline-none">
                    
                    @if (currentTab() === 'script') {
                      <div class="flex flex-col space-y-3 animate-in fade-in duration-500">
                        <div>
                           <div class="flex items-center gap-1.5 mb-1 group cursor-pointer" (click)="audio.readText(interview.currentQuestion().questionEn)">
                              <span class="text-[7px] font-black text-primary uppercase tracking-[0.2em]">1. THE CHALLENGE</span>
                              <span class="material-icons !text-[9px] text-primary/30 group-hover:text-primary transition-colors">campaign</span>
                           </div>
                           <h1 class="text-base md:text-xl font-black text-white leading-snug">
                              {{ interview.currentQuestion().questionEn }}
                           </h1>
                        </div>
                        
                        <div class="p-4 rounded-xl bg-black/40 border border-dashed border-white/10 flex flex-col relative group transition-all">
                          <div class="flex items-center justify-between mb-1.5">
                             <span class="text-[7px] font-black uppercase text-primary tracking-[0.2em] opacity-40 italic">2. MASTER SCRIPT</span>
                             <button (click)="audio.readText(interview.currentQuestion().fullSuggestedResponseEn)" class="text-[6px] font-black text-white/20 hover:text-primary transition-all">LISTEN</button>
                          </div>
                          <p class="text-white/70 text-[13px] md:text-base font-medium leading-relaxed italic pr-2 group-hover:text-white transition-colors">
                            "{{ interview.currentQuestion().fullSuggestedResponseEn }}"
                          </p>
                        </div>

                        <!-- FEEDBACK BREVE -->
                        <div class="flex justify-start opacity-20">
                           <div class="px-2 py-0.5 rounded-full bg-white/5 border border-white/5 flex items-center gap-1.5 overflow-hidden">
                             <div class="w-0.5 h-0.5 rounded-full bg-primary animate-pulse"></div>
                             <span class="text-[6px] font-black uppercase text-surface-muted tracking-[0.1em] whitespace-nowrap">Awaiting Performance Data Stream...</span>
                           </div>
                        </div>
                      </div>
                    }

                    @if (currentTab() === 'performance') {
                      <div class="h-full flex flex-col items-center justify-center text-center py-2 animate-in fade-in duration-300">
                         <div class="mb-4">
                            <h3 class="text-[7px] font-black uppercase tracking-[0.4em] mb-4 text-rose-500 animate-pulse leading-none">Scanning Voice Signature</h3>
                            <div class="relative">
                               <div class="w-16 h-16 rounded-full flex items-center justify-center bg-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.3)] border-2 border-white/10">
                                  <span class="material-icons text-3xl text-white">graphic_eq</span>
                               </div>
                            </div>
                         </div>
                         <div class="w-full max-w-sm p-4 bg-black/40 border border-primary/20 rounded-xl">
                            <p class="text-[11px] font-medium text-white/30 leading-tight italic">"{{ interview.currentQuestion().fullSuggestedResponseEn }}"</p>
                         </div>
                      </div>
                    }

                    @if (currentTab() === 'audit') {
                      <div class="h-full animate-in slide-in-from-bottom-2 duration-500">
                         @if (interview.hasAnalysis()) { <div class="h-full overflow-y-auto custom-scrollbar"><app-feedback-panel /></div> }
                         @else { <div class="h-full flex items-center justify-center opacity-5 grayscale"><span class="material-icons text-8xl">analytics</span></div> }
                      </div>
                    }
                  </div>

                  <!-- TABS SELECTOR (NANO) -->
                  <div class="p-1 px-2 bg-black/80 border-t border-white/5 flex items-center justify-center gap-1 shrink-0 backdrop-blur-xl">
                     <button (click)="currentTab.set('script')" class="flex-1 flex flex-col items-center gap-0.5 py-1 rounded-lg text-[6px] font-black uppercase tracking-widest transition-all" [ngClass]="{'bg-white/10 text-white shadow-lg': currentTab() === 'script', 'text-surface-muted opacity-40': currentTab() !== 'script'}">
                        <span class="material-icons !text-xs">description</span> MISSION
                     </button>
                     <button (click)="currentTab.set('performance')" class="flex-1 flex flex-col items-center gap-0.5 py-1 rounded-lg text-[6px] font-black uppercase tracking-widest transition-all" [ngClass]="{'bg-rose-500/10 text-rose-400': currentTab() === 'performance', 'text-surface-muted opacity-40': currentTab() !== 'performance'}">
                        <span class="material-icons !text-xs">face</span> PERFORMANCE
                     </button>
                     <button (click)="currentTab.set('audit')" class="flex-1 flex flex-col items-center gap-0.5 py-1 rounded-lg text-[6px] font-black uppercase tracking-widest transition-all" [ngClass]="{'bg-emerald-500/10 text-emerald-400': currentTab() === 'audit', 'text-surface-muted opacity-40': currentTab() !== 'audit'}">
                        <span class="material-icons !text-xs">insights</span> AUDIT
                     </button>
                  </div>
                </div>
              </div>
            }
          </div>
        }
      </main>
    </div>
  `,
  styles: [`
    .material-icons { vertical-align: middle; }
    .custom-scrollbar::-webkit-scrollbar { width: 2px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(129, 140, 248, 0.1); border-radius: 20px; }
    .scrollbar-hide::-webkit-scrollbar { display: none; }
  `]
})
export class MainTrainerComponent {
  protected interview = inject(InterviewService);
  protected audio = inject(AudioService);
  protected mode = signal<'v1' | 'v2' | 'v3'>('v3');
  protected currentTab = signal<'script' | 'performance' | 'audit'>('script');

  setMode(m: 'v1' | 'v2' | 'v3') { this.mode.set(m); }

  async toggleRecording() {
    if (this.interview.isRecording()) {
      this.interview.setRecording(false);
      this.interview.setProcessing(true);
      const result = await this.audio.stopRecording(this.interview.currentQuestion());
      this.interview.setAnalysisResult(result);
      this.currentTab.set('audit');
    } else {
      this.interview.setRecording(true);
      this.currentTab.set('performance');
      await this.audio.startRecording();
    }
  }
}
