import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-onboarding',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule],
  template: `
    <div class="min-h-screen bg-surface-bg flex items-center justify-center p-6 relative overflow-hidden">
      <!-- Background Effects -->
      <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 blur-[120px] rounded-full animate-pulse-glow"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-ic-blue/10 blur-[120px] rounded-full animate-pulse-glow" style="animation-delay: 1s"></div>
      </div>

      <div class="max-w-2xl w-full relative z-10 animate-fade-in-up">
        <div class="text-center mb-12">
          <h2 class="text-4xl font-black text-surface-text tracking-tighter uppercase italic glow-text">Welcome to InternoCore</h2>
          <p class="text-surface-text-muted mt-2 font-mono text-[10px] tracking-widest uppercase">Let's set up your industrial workspace</p>
        </div>

        <div class="glass-card p-10 rounded-[2.5rem] border border-white/10 shadow-2xl">
          <!-- Stepper -->
          <div class="flex items-center justify-between mb-12 relative">
            <div class="absolute top-1/2 left-0 w-full h-0.5 bg-white/5 -translate-y-1/2 z-0"></div>
            <div 
              class="absolute top-1/2 left-0 h-0.5 bg-primary -translate-y-1/2 z-0 transition-all duration-500"
              [style.width.%]="(step() - 1) * 50"
            ></div>

            @for (s of [1, 2, 3]; track s) {
              <div 
                class="w-10 h-10 rounded-xl flex items-center justify-center z-10 transition-all duration-500 border-2"
                [class.bg-primary]="step() >= s"
                [class.border-primary]="step() >= s"
                [class.text-ic-dark]="step() >= s"
                [class.bg-surface-card]="step() < s"
                [class.border-white/10]="step() < s"
                [class.text-surface-text-muted]="step() < s"
              >
                <span class="font-black text-xs">{{ s }}</span>
              </div>
            }
          </div>

          @if (step() === 1) {
            <!-- Step 1: Company Info -->
            <div class="space-y-6 animate-fade-in">
              <div class="space-y-2">
                <h3 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">Company Identity</h3>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">Basic information about your organization</p>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label for="comp-name" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Company Name</label>
                  <input id="comp-name" type="text" class="w-full input-industrial" placeholder="Ej. Global Logistics SA">
                </div>
                <div class="space-y-2">
                  <label for="tax-id" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Tax ID / RFC</label>
                  <input id="tax-id" type="text" class="w-full input-industrial" placeholder="ABC123456XYZ">
                </div>
              </div>

              <div class="space-y-2">
                <label for="industry" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Industry Sector</label>
                <select id="industry" class="w-full input-industrial">
                  <option>Automotive</option>
                  <option>Logistics</option>
                  <option>Manufacturing</option>
                  <option>Textile</option>
                </select>
              </div>

              <div class="space-y-2">
                <label for="base-currency" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Base Currency</label>
                <select id="base-currency" class="w-full input-industrial">
                  <option value="USD">USD - US Dollar</option>
                  <option value="MXN">MXN - Mexican Peso</option>
                  <option value="EUR">EUR - Euro</option>
                </select>
              </div>
            </div>
          } @else if (step() === 2) {
            <!-- Step 2: First Warehouse -->
            <div class="space-y-6 animate-fade-in">
              <div class="space-y-2">
                <h3 class="text-xl font-black text-surface-text uppercase tracking-tighter italic">First Warehouse</h3>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">Define your primary storage location</p>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label for="wh-name" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Warehouse Name</label>
                  <input id="wh-name" type="text" class="w-full input-industrial" placeholder="Ej. Tijuana Central">
                </div>
                <div class="space-y-2">
                  <label for="wh-code" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Code</label>
                  <input id="wh-code" type="text" class="w-full input-industrial" placeholder="WH-TIJ">
                </div>
              </div>

              <div class="space-y-2">
                <label for="wh-address" class="block text-[9px] font-bold text-surface-text-muted uppercase tracking-widest">Location / Address</label>
                <textarea id="wh-address" class="w-full input-industrial h-24 resize-none" placeholder="Full address..."></textarea>
              </div>
            </div>
          } @else if (step() === 3) {
            <!-- Step 3: Confirmation -->
            <div class="text-center space-y-8 animate-fade-in py-10">
              <div class="w-24 h-24 bg-emerald-500/20 border-2 border-emerald-500/50 rounded-full flex items-center justify-center mx-auto animate-bounce">
                <mat-icon class="text-emerald-500 text-5xl w-12 h-12">check_circle</mat-icon>
              </div>
              <div class="space-y-2">
                <h3 class="text-2xl font-black text-surface-text uppercase tracking-tighter italic">Ready to Launch</h3>
                <p class="text-[10px] text-surface-text-muted font-bold uppercase tracking-widest">Your industrial workspace is configured</p>
              </div>
              <p class="text-xs text-surface-text-muted max-w-sm mx-auto">
                We've prepared your dashboard with default settings for your industry. You can customize everything later in the settings panel.
              </p>
            </div>
          }

          <!-- Footer Actions -->
          <div class="mt-12 flex items-center justify-between pt-8 border-t border-white/5">
            <button 
              (click)="prev()"
              [disabled]="step() === 1"
              class="px-8 py-3 text-[10px] font-black text-surface-text-muted uppercase tracking-widest hover:text-primary disabled:opacity-0 transition-all"
            >
              Back
            </button>
            
            <button 
              (click)="next()"
              class="px-10 py-4 bg-primary text-ic-dark rounded-xl font-black text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(0,229,255,0.2)] hover:shadow-primary/40 transition-all active:scale-95"
            >
              {{ step() === 3 ? 'Finish Setup' : 'Next Step' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class OnboardingComponent {
  private router = inject(Router);
  step = signal(1);

  next() {
    if (this.step() < 3) {
      this.step.update(s => s + 1);
    } else {
      this.router.navigate(['/dashboard']);
    }
  }

  prev() {
    if (this.step() > 1) {
      this.step.update(s => s - 1);
    }
  }
}
