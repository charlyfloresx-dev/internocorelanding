import { Component, inject, ChangeDetectionStrategy, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InterviewService } from '../../core/interview.service';
import { AudioService } from '../../core/audio.service';
import { FeedbackPanelComponent } from '../feedback-panel/feedback-panel.component';

@Component({
  selector: 'app-trainer-v2',
  standalone: true,
  imports: [CommonModule, FeedbackPanelComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="w-full h-full flex flex-col p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 overflow-x-hidden font-inter overflow-y-auto custom-scrollbar">
      
      <!-- DASHBOARD TÁCTICO CON NAVEGACIÓN EN CÍRCULO ROJO -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <!-- COLUMNA IZQUIERDA: MASTER SCRIPT & NAVEGACIÓN -->
        <div class="lg:col-span-12 xl:col-span-5 flex flex-col gap-6 font-inter">
           <div class="p-6 md:p-8 bg-surface-card border border-surface-border rounded-[40px] shadow-2xl relative overflow-hidden flex flex-col min-h-[440px]">
              
              <!-- HEADER DE PREGUNTA -->
              <div class="flex items-center gap-4 mb-6 shrink-0 text-white">
                <div class="w-10 h-10 rounded-xl bg-primary flex items-center justify-center font-black text-lg shadow-lg shadow-primary/20">
                  Q{{ interview.currentIndex() + 1 }}
                </div>
                <div class="flex flex-col">
                  <span class="text-[8px] font-black uppercase text-primary tracking-[0.4em]">Audit Strategy</span>
                  <div class="flex items-center gap-2 mt-1">
                    <button (click)="audio.readText(interview.currentQuestion().questionEn)" 
                            class="w-6 h-6 rounded-lg bg-white/5 flex items-center justify-center hover:bg-primary/20 transition-all border border-white/5 text-primary">
                      <span class="material-icons !text-[12px]">volume_up</span>
                    </button>
                    <span class="text-[7px] font-black uppercase text-surface-muted tracking-widest opacity-40 italic">Biometrics Scan Ready</span>
                  </div>
                </div>
              </div>

              <!-- PREGUNTA + CONTROL GRABACIÓN -->
              <div class="relative mb-8 pr-20 group/q">
                <h1 class="text-xl md:text-2xl lg:text-3xl font-black text-white leading-tight tracking-tight">
                   {{ interview.currentQuestion().questionEn }}
                </h1>
                
                <button (click)="toggleRecording()" 
                        class="absolute right-0 top-0 w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-500 hover:scale-110 active:scale-95 shadow-2xl border-2"
                        [class]="interview.isRecording() ? 'bg-rose-500 text-white border-rose-400 shadow-rose-500/30' : 'bg-primary text-white border-white/10 shadow-primary/30'">
                  <span class="material-icons text-3xl">{{ interview.isRecording() ? 'stop' : 'mic' }}</span>
                  @if (interview.isRecording()) {
                    <div class="absolute -inset-1 rounded-2xl border-2 border-rose-500 animate-ping opacity-20"></div>
                  }
                </button>
              </div>

              <!-- MASTER SCRIPT INTERACTIVO -->
              <div class="flex-1 p-5 rounded-3xl bg-black/20 border border-white/5 border-dashed relative group overflow-hidden mb-6">
                 <span class="text-[8px] font-black uppercase text-primary tracking-[0.4em] mb-4 block italic opacity-50 underline decoration-primary/20">MASTER SCRIPT STRATEGY:</span>
                 <div class="text-white/60 text-sm md:text-base font-medium leading-relaxed italic pr-4 flex flex-wrap gap-x-1 gap-y-0">
                    <span class="text-white/40">"</span>
                    @for (word of getMasterWords(); track $index) {
                      <button (click)="audio.readText(word)" 
                              class="px-0 py-0 bg-transparent text-white/50 hover:text-primary transition-all duration-200 cursor-pointer text-sm md:text-base font-medium italic">
                        {{ word }}
                      </button>
                    }
                    <span class="text-white/40">"</span>
                 </div>
              </div>

              <!-- FOOTER: AUDIO FULL + NAVEGACIÓN (CÍRCULO ROJO) -->
              <div class="shrink-0 flex items-center justify-between mt-auto">
                 <button (click)="audio.readText(interview.currentQuestion().fullSuggestedResponseEn)" 
                         class="flex items-center gap-3 px-5 py-2.5 rounded-xl bg-white/5 hover:bg-primary/20 text-[8px] font-black uppercase text-white transition-all border border-white/5 group">
                   <span class="material-icons !text-sm text-primary group-hover:scale-110 transition-transform">campaign</span> Play Full Reference
                 </button>

                 <!-- NAVEGADOR DE PREGUNTAS (ZONA ROJA) -->
                 <div class="flex items-center gap-3 p-1.5 rounded-2xl bg-black/40 border border-white/5">
                    <button (click)="interview.prevQuestion()" 
                            [disabled]="interview.currentIndex() === 0"
                            class="w-10 h-10 rounded-xl flex items-center justify-center transition-all bg-white/5 hover:bg-primary/20 disabled:opacity-10 text-white border border-white/5">
                       <span class="material-icons !text-xl">chevron_left</span>
                    </button>
                    
                    <div class="flex flex-col items-center px-2">
                       <span class="text-[7px] font-black text-primary/40 uppercase tracking-[0.3em]">Progress</span>
                       <span class="text-[10px] font-black text-white tracking-widest">{{ interview.currentIndex() + 1 }} / {{ interview.totalQuestions() }}</span>
                    </div>

                    <button (click)="interview.nextQuestion()" 
                            [disabled]="interview.currentIndex() === interview.totalQuestions() - 1"
                            class="w-10 h-10 rounded-xl flex items-center justify-center transition-all bg-white/5 hover:bg-primary/20 disabled:opacity-10 text-white border border-white/5">
                       <span class="material-icons !text-xl">chevron_right</span>
                    </button>
                 </div>
              </div>
           </div>
        </div>

        <!-- COLUMNA DERECHA: BIO-RESPONSE & MÉTRICAS -->
        <div class="lg:col-span-12 xl:col-span-7 flex flex-col gap-6 h-full font-inter">
           
           <!-- PERFORMANCE AUDIT -->
           <div class="p-6 md:p-8 rounded-[40px] bg-white/[0.03] border border-white/5 shadow-2xl relative overflow-hidden flex flex-col min-h-[380px] max-h-[480px]">
              
              <div class="flex items-center justify-between mb-6 shrink-0">
                <span class="text-[8px] font-black uppercase text-primary tracking-[0.6em] flex items-center gap-2 underline decoration-primary/20">
                  <span class="material-icons !text-sm">graphic_eq</span> PERFORMANCE BIOMETRIC AUDIT
                </span>
                
                @if (audio.getRecordingUrl()) {
                  <button (click)="audio.playRecording()" 
                          class="flex items-center gap-3 px-4 py-2 rounded-2xl bg-white/5 hover:bg-primary/20 border border-white/5 transition-all text-white group">
                     <span class="material-icons !text-base text-primary group-hover:scale-110 transition-transform">play_circle</span>
                     <span class="text-[8px] font-black uppercase tracking-widest">Listen Response</span>
                  </button>
                }
              </div>

              <!-- RESPUESTA MIMÉTICA -->
              <div class="flex-1 overflow-y-auto custom-scrollbar flex flex-wrap gap-x-1.5 gap-y-1 content-start pr-6 py-2 leading-relaxed">
                <span class="text-white/40 text-sm md:text-base font-medium italic">"</span>
                @for (word of getWords(); track $index) {
                  <button (click)="audio.readText(word)" 
                          class="px-0 py-0 bg-transparent text-sm md:text-base font-medium italic transition-all duration-300 hover:scale-110 cursor-pointer inline-block lowercase first-letter:uppercase"
                          [class]="getWordMimeClass(word)">
                    {{ word }}
                  </button>
                } @empty {
                  <div class="w-full h-full flex flex-col items-center justify-center opacity-5 grayscale py-8">
                    <span class="material-icons text-7xl mb-4">psychology</span>
                    <p class="font-black uppercase tracking-[0.8em] text-[8px]">Awaiting Scan</p>
                  </div>
                }
                <span class="text-white/40 text-sm md:text-base font-medium italic" *ngIf="getWords().length > 0">"</span>
              </div>

              <!-- MÉTRICAS EN CÍRCULO ROJO (ZONA INFERIOR) -->
              <div class="mt-6 pt-6 border-t border-white/5 flex items-center justify-between shrink-0">
                 <div class="flex items-center gap-6 shrink-0 md:flex hidden">
                    <div class="flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-emerald-400"></div><span class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em]">Excellence</span></div>
                    <div class="flex items-center gap-2"><div class="w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(129,140,248,0.3)]"></div><span class="text-[8px] font-black text-white/30 uppercase tracking-[0.2em]">Tech</span></div>
                 </div>

                 <div class="flex items-center gap-6 pr-2">
                    <div class="flex flex-col items-end">
                       <span class="text-[5px] font-black uppercase text-surface-muted/50 tracking-[0.4em] mb-1">Confidence</span>
                       <span class="text-xs font-black text-white tracking-widest tabular-nums">{{ bioMetrics().confidence }}%</span>
                    </div>
                    <div class="flex flex-col items-end border-l border-white/5 pl-6">
                       <span class="text-[5px] font-black uppercase text-surface-muted/50 tracking-[0.4em] mb-1">Accuracy</span>
                       <span class="text-xs font-black text-primary tracking-widest tabular-nums">{{ bioMetrics().techAccuracy }}%</span>
                    </div>
                    <div class="flex flex-col items-end border-l border-white/5 pl-6">
                       <span class="text-[5px] font-black uppercase text-surface-muted/50 tracking-[0.4em] mb-1">Lock</span>
                       <div class="flex items-center gap-2">
                          <span class="text-[10px] font-black text-emerald-400 tracking-widest">{{ bioMetrics().clarity }}</span>
                          <div class="w-1 h-1 rounded-full bg-emerald-400 animate-pulse"></div>
                       </div>
                    </div>
                 </div>
              </div>
           </div>

           <!-- EL PANAL DE COACHING -->
           <div class="shrink-0">
              <app-feedback-panel />
           </div>
        </div>

      </div>
    </div>
  `,
  styles: [`
    .material-icons { vertical-align: middle; }
    .custom-scrollbar::-webkit-scrollbar { width: 3px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
    .scrollbar-hide::-webkit-scrollbar { display: none; }
  `]
})
export class TrainerV2Component {
  protected interview = inject(InterviewService);
  protected audio = inject(AudioService);

  getWords() {
    const transcript = this.audio.liveTranscript();
    if (!transcript) return [];
    return transcript.split(' ').filter(w => w.length > 0);
  }

  getMasterWords() {
    const script = this.interview.currentQuestion().fullSuggestedResponseEn;
    if (!script) return [];
    return script.split(' ').filter(w => w.length > 0);
  }

  bioMetrics = computed(() => {
    const analysis = this.interview.lastAnalysis();
    if (!analysis) return { confidence: 0, techAccuracy: 0, clarity: 'SCAN' };

    const insights = (analysis as any).wordInsights || [];
    const avgConfidence = insights.length > 0
      ? (insights.reduce((acc: number, val: any) => acc + (val.confidence || 0), 0) / insights.length)
      : 0;

    const techTerms = ['mes', 'tulip', 'safran', 'wip', 'kpi', 'real-time', 'traceability', 'manufacturing'];
    const capturedTech = techTerms.filter(term => 
      analysis.transcript?.toLowerCase().includes(term)
    );
    const techAcc = Math.round((capturedTech.length / techTerms.length) * 100);

    return {
      confidence: Math.round(avgConfidence * 100),
      techAccuracy: techAcc,
      clarity: avgConfidence > 0.8 ? 'OPTIMAL' : (avgConfidence > 0.6 ? 'STABLE' : 'AUDIT')
    };
  });

  getWordMimeClass(word: string): string {
    const analysis = this.interview.lastAnalysis();
    if (!analysis) return 'text-white/20';

    const normalizedWord = word.toLowerCase().replace(/[.,!?;]/g, '');
    const techTerms = ['mes', 'tulip', 'safran', 'wip', 'kpi', 'real-time', 'deployment', 'ecosystem', 'traceability', 'manufacturing'];
    
    if (techTerms.includes(normalizedWord)) return 'text-primary font-bold';

    const insights = (analysis as any).wordInsights || [];
    const feedback = (insights as any[]).find(f => f.word.toLowerCase() === normalizedWord);
    
    if (!feedback) return 'text-white/60';
    const confidence = feedback.confidence || 0;
    
    if (confidence >= 0.9) return 'text-emerald-400 font-bold';
    if (confidence >= 0.7) return 'text-white/80';
    return 'text-rose-500 font-bold';
  }

  async toggleRecording() {
    if (this.interview.isRecording()) {
      this.interview.setRecording(false);
      this.interview.setProcessing(true);
      const result = await this.audio.stopRecording(this.interview.currentQuestion());
      this.interview.setAnalysisResult(result);
    } else {
      this.interview.setRecording(true);
      await this.audio.startRecording();
    }
  }
}
