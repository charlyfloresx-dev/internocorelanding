import { Component, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InterviewService } from '../../core/interview.service';
import { AudioService } from '../../core/audio.service';

@Component({
  selector: 'app-record-button',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button
      (click)="toggleRecording()"
      [disabled]="interview.isProcessing()"
      [class]="getButtonClasses()"
      class="group relative w-24 h-24 md:w-32 md:h-32 rounded-full flex flex-col items-center justify-center transition-all duration-500 active:scale-95 shadow-2xl border-4"
    >
      <!-- Pulsating outer ring -->
      @if (interview.isRecording()) {
        <div class="absolute inset-[-12px] rounded-full border-2 border-primary animate-ping opacity-30"></div>
        <div class="absolute inset-[-4px] rounded-full border-4 border-primary/20 animate-pulse"></div>
      }

      <!-- Icon & Text -->
      <div class="relative z-10 flex flex-col items-center">
        <span class="material-icons text-3xl md:text-5xl mb-1 transition-transform group-hover:scale-110">
          {{ interview.isRecording() ? 'stop' : 'mic' }}
        </span>
        <span class="text-[9px] font-black uppercase tracking-[0.2em]">
          {{ interview.isRecording() ? 'Stop' : 'Tell me' }}
        </span>
      </div>

      <!-- Processing State -->
      @if (interview.isProcessing()) {
        <div class="absolute inset-0 rounded-full bg-surface-bg/80 flex items-center justify-center backdrop-blur-sm">
          <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
        </div>
      }
    </button>
  `,
  styles: [`
    .glow-primary { box-shadow: 0 0 30px rgba(129, 140, 248, 0.4); }
    .glow-active { box-shadow: 0 0 50px rgba(244, 63, 94, 0.5); }
  `]
})
export class RecordButtonComponent {
  protected interview = inject(InterviewService);
  protected audio = inject(AudioService);

  async toggleRecording() {
    if (this.interview.isProcessing()) return;

    if (!this.interview.isRecording()) {
      // Start Recording
      this.interview.setRecording(true);
      this.interview.setAnalysisResult(null as any);
      
      try {
        await this.audio.startRecording();
      } catch (err) {
        console.error('Recording start failed:', err);
        this.interview.setRecording(false);
      }
    } else {
      // Stop & Analyze
      this.interview.setRecording(false);
      this.interview.setProcessing(true);
      
      try {
        const result = await this.audio.stopRecording(this.interview.currentQuestion());
        this.interview.setAnalysisResult(result);
      } catch (err) {
        console.error('Recording stop or Analysis failed:', err);
      } finally {
        this.interview.setProcessing(false);
      }
    }
  }

  getButtonClasses(): string {
    if (this.interview.isProcessing()) return 'bg-surface-card border-surface-border text-surface-muted cursor-wait opacity-50';
    if (this.interview.isRecording()) return 'bg-rose-500 text-white border-rose-400 glow-active animate-pulse scale-110 ring-8 ring-rose-500/10';
    return 'bg-primary text-white border-primary-light glow-primary hover:scale-105 active:scale-110';
  }
}
