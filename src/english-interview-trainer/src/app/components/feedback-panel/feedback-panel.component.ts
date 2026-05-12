import { Component, inject, ChangeDetectionStrategy, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InterviewService } from '../../core/interview.service';
import { AudioService } from '../../core/audio.service';

/** 🔵 Pro Auditor: High Accuracy Phonetic Scanner */
@Component({
  selector: 'app-feedback-panel',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="w-full flex md:flex-row flex-col gap-5 animate-in slide-in-from-bottom-4 duration-700 font-inter">
      
      <!-- PHONETIC COACHING (SIEMPRE PRESENTE) -->
      <div class="flex-1 p-6 rounded-[32px] bg-black/40 border border-white/5 flex flex-col group/panel min-h-[160px] relative overflow-hidden">
        <!-- Indicador de Scan -->
        <div class="absolute top-0 right-0 p-3 opacity-20 group-hover:opacity-40 transition-opacity">
           <div class="w-1.5 h-1.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(129,140,248,0.5)]"></div>
        </div>

        <div class="flex items-center gap-2 mb-4">
          <span class="material-icons text-primary !text-sm">record_voice_over</span>
          <h3 class="text-[9px] font-black uppercase text-white tracking-[0.4em] drop-shadow-sm">Phonetic Coaching</h3>
        </div>
        
        <div class="space-y-3">
          @for (tip of coachingTips().pronunciation; track $index) {
            <div class="flex items-start gap-4 p-3 rounded-2xl bg-white/5 border border-white/5 hover:bg-primary/10 transition-all cursor-pointer group" (click)="audio.readText(tip.word)">
               <div class="w-2 h-2 rounded-full bg-rose-500 mt-1.5 shrink-0 shadow-[0_0_10px_rgba(244,63,94,0.4)]"></div>
               <div class="flex flex-col">
                  <span class="text-[10px] font-bold text-white uppercase tracking-wider mb-0.5 group-hover:text-primary transition-colors">{{ tip.word }}</span>
                  <p class="text-[10px] text-white/50 leading-relaxed italic group-hover:text-white/80 transition-colors">{{ tip.advice }}</p>
               </div>
            </div>
          } @empty {
            <div class="flex-1 flex flex-col items-center justify-center py-6 opacity-30 grayscale transition-all group-hover:opacity-60">
              <span class="material-icons text-3xl mb-3 text-emerald-400">check_circle</span>
              <p class="text-[8px] font-black uppercase tracking-[0.6em] italic text-center text-emerald-400">Bio-Scan Clean</p>
              <p class="text-[6px] font-bold uppercase tracking-tight text-white/40 mt-1">Optimal Phonetic Accuracy Detected</p>
            </div>
          }
        </div>
      </div>

      <!-- TECHNICAL STRATEGY INVENTORY (DOBLE COLUMNA) -->
      <div class="flex-[1.5] p-6 rounded-[32px] bg-black/40 border border-white/5 flex flex-col min-h-[160px]">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-icons text-emerald-400 !text-sm">analytics</span>
          <h3 class="text-[9px] font-black uppercase text-white tracking-[0.4em]">Strategy Inventory</h3>
        </div>
        
        <div class="grid grid-cols-2 gap-2.5 overflow-y-auto custom-scrollbar max-h-[180px] pr-2">
           @for (item of terminologyStatus(); track $index) {
             <div class="flex items-center gap-3 p-3 rounded-xl border transition-all"
                  [class]="item.found ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-white/[0.02] border-white/5 opacity-30 group hover:opacity-100 hover:bg-white/5 hover:border-white/10'">
                
                <div class="w-5 h-5 rounded-lg flex items-center justify-center shrink-0"
                     [class]="item.found ? 'bg-emerald-500/20 text-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.2)]' : 'bg-white/5 text-white/10 border border-white/5'">
                  <span class="material-icons !text-[12px] font-bold">{{ item.found ? 'check' : 'close' }}</span>
                </div>
                
                <div class="flex flex-col min-w-0">
                  <span class="text-[9px] font-black uppercase tracking-widest truncate"
                        [class]="item.found ? 'text-emerald-400' : 'text-white/30'">{{ item.term }}</span>
                  @if (!item.found) {
                    <span class="text-[6px] font-bold text-white/10 uppercase tracking-tighter truncate underline decoration-white/5">Missing Strategy</span>
                  }
                </div>
             </div>
           }
        </div>
      </div>

    </div>
  `,
  styles: [`
    .material-icons { vertical-align: middle; }
    .custom-scrollbar::-webkit-scrollbar { width: 3px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.05); border-radius: 10px; }
  `]
})
export class FeedbackPanelComponent {
  protected interview = inject(InterviewService);
  protected audio = inject(AudioService);

  private readonly technicalDictionary = ['MES', 'PRODUCTION', 'REAL-TIME', 'CONSULTANT', 'SAFRAN', 'TULIP', 'WIP', 'WMS', 'TRACEABILITY', 'ECOSYSTEM', 'SCADA', 'PLC'];

  terminologyStatus = computed(() => {
    const analysis = this.interview.lastAnalysis();
    const transcript = (analysis?.transcript || '').toUpperCase();
    
    return this.technicalDictionary.map(term => ({
      term,
      found: transcript.includes(term)
    })).sort((a, b) => (a.found === b.found ? 0 : a.found ? -1 : 1));
  });

  coachingTips = computed(() => {
    const analysis = this.interview.lastAnalysis();
    if (!analysis) return { pronunciation: [], vocabulary: [] };

    // Scanner más exigente (Confianza < 90%)
    const pronunciation = (analysis.wordInsights || [])
      .filter((w: any) => (w.confidence || 0) < 0.9)
      .slice(0, 3)
      .map((w: any) => ({
        word: w.word,
        advice: this.getPhoneticTip(w.word)
      }));

    return { pronunciation, vocabulary: [] };
  });

  private getPhoneticTip(word: string): string {
    const tips: Record<string, string> = {
      'mes': 'Sharp M, clear vowel.',
      'digital': 'Soft G sound.',
      'transformation': 'Stress the MA.',
      'specialist': 'End with ST.',
      'consultant': 'Neutral U.',
      'traceability': 'Focus on BILITY.',
      'ecosystem': 'Sharp E at start.',
      'production': 'Enunciate the T-I-O-N.'
    };
    return tips[word.toLowerCase()] || `Focus on clear syllable separation for "${word}".`;
  }
}
