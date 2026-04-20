import {Component, input, signal} from '@angular/core';
import {CommonModule} from '@angular/common';
import {MatIconModule} from '@angular/material/icon';

@Component({
  selector: 'app-accordion',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="border border-surface-border border-l-4 border-l-primary rounded-xl overflow-hidden bg-surface-card transition-all duration-300 shadow-sm hover:shadow-md">
      <button 
        (click)="toggle()"
        class="w-full flex items-center justify-between p-4 text-left hover:bg-primary/5 transition-colors group"
      >
        <div class="flex items-center gap-3">
          @if (icon()) {
            <mat-icon class="text-primary group-hover:scale-110 transition-transform">{{ icon() }}</mat-icon>
          }
          <span class="font-bold text-xs uppercase tracking-widest text-surface-text">{{ title() }}</span>
        </div>
        <div class="flex items-center gap-2">
          @if (badge()) {
            <span class="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-black uppercase border border-primary/20">
              {{ badge() }}
            </span>
          }
          <mat-icon 
            class="text-surface-text-muted transition-transform duration-500"
            [class.rotate-180]="isOpen()"
          >
            expand_more
          </mat-icon>
        </div>
      </button>
      
      <div 
        class="overflow-hidden transition-all duration-500 ease-in-out"
        [style.max-height]="isOpen() ? '1000px' : '0'"
        [class.opacity-0]="!isOpen()"
        [class.opacity-100]="isOpen()"
      >
        <div class="p-4 pt-0 text-sm text-surface-text-muted border-t border-surface-border/30">
          <div class="mt-4 animate-fade-in">
            <ng-content></ng-content>
          </div>
        </div>
      </div>
    </div>
  `
})
export class AccordionComponent {
  title = input.required<string>();
  icon = input<string>();
  badge = input<string>();
  isOpen = signal(false);

  toggle() {
    this.isOpen.update(v => !v);
  }
}
