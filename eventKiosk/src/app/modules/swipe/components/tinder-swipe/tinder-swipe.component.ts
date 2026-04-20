import { Component, Input, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EventPhoto } from '../../../../core/services/kiosk.service';

@Component({
  selector: 'app-tinder-swipe',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="relative w-full h-[550px] max-w-[400px] mx-auto perspective-1000 flex flex-col justify-center items-center px-6">
      <!-- Empty Stack Message -->
      <div *ngIf="photos.length === 0" class="text-center p-12 bg-brand-surface rounded-[40px] border border-white/5 shadow-2xl w-full">
        <div class="h-24 w-24 bg-brand-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <span class="material-icons text-brand-primary text-5xl">auto_awesome</span>
        </div>
        <h3 class="text-white font-black text-2xl mb-2">¡Todo al día!</h3>
        <p class="text-white/40 text-sm font-medium leading-relaxed">No hay más fotos pendientes por aprobar en este momento.</p>
        <button  
          class="mt-8 px-8 py-3 bg-brand-primary text-brand-dark rounded-full font-black text-sm uppercase tracking-widest shadow-lg shadow-brand-primary/20 active:scale-95 transition-transform">
          Ver Galería
        </button>
      </div>

      <!-- PHOTO STACK -->
      <div class="relative w-full h-[480px] rounded-[40px] overflow-hidden shadow-[0_30px_60px_rgba(0,0,0,0.6)] bg-brand-surface border border-white/10" *ngIf="photos.length > 0">
        <!-- Next Photo (Hinting) -->
        <div 
          *ngIf="photos[1]"
          class="absolute inset-0 bg-cover bg-center opacity-30 scale-95"
          [style.backgroundImage]="'url(' + getPhotoUrl(photos[1]) + ')'">
        </div>

        <!-- TOP Photo -->
        <div 
          class="absolute inset-0 bg-cover bg-center transition-all duration-300 ease-out z-10"
          [style.backgroundImage]="'url(' + getPhotoUrl(photos[0]) + ')'"
          [style.transform]="'translateX(' + xOffset() + 'px) rotate(' + rotation() + 'deg) scale(' + (1 - Math.abs(xOffset())/2000) + ')'"
          [style.opacity]="1 - Math.abs(xOffset())/800">
          
          <!-- STAMPS Overlay -->
          <div 
            class="absolute top-16 left-10 border-[6px] border-brand-success rounded-2xl px-6 py-3 rotate-[-15deg] opacity-0 transition-opacity z-20 backdrop-blur-sm bg-brand-success/10"
            [class.opacity-100]="xOffset() > 60">
            <span class="text-brand-success font-black text-4xl tracking-tighter shadow-2xl">APROBADA</span>
          </div>
          <div 
            class="absolute top-16 right-10 border-[6px] border-brand-danger rounded-2xl px-6 py-3 rotate-[15deg] opacity-0 transition-opacity z-20 backdrop-blur-sm bg-brand-danger/10"
            [class.opacity-100]="xOffset() < -60">
            <span class="text-brand-danger font-black text-4xl tracking-tighter shadow-2xl">DESCARTAR</span>
          </div>

          <!-- N-Approver Quórum Indicators (Top) -->
          <div class="absolute top-4 inset-x-0 flex flex-col items-center z-30">
              <div class="flex space-x-2">
                  <div *ngFor="let i of range(photos[0].required_approvals || 2)" 
                       class="h-3 w-3 rounded-full transition-all duration-500 border border-white/20 shadow-lg"
                       [class.bg-brand-primary]="i < photos[0].approval_count"
                       [class.shadow-brand-primary]="i < photos[0].approval_count"
                       [class.bg-white/20]="i >= photos[0].approval_count">
                  </div>
              </div>
              <p class="text-white/60 text-[9px] font-black uppercase mt-2 tracking-[0.2em] bg-black/40 px-3 py-1 rounded-full backdrop-blur-md border border-white/5">
                {{ photos[0].approval_count }} de {{ photos[0].required_approvals }} Aprobadores
              </p>
              
              <!-- Decisive Vote Hint -->
              <p *ngIf="photos[0].approval_count === (photos[0].required_approvals || 2) - 1" 
                 class="text-brand-primary text-[8px] font-black uppercase mt-1 animate-bounce">
                ¡Tu voto es el decisivo! 🚀
              </p>
          </div>

          <!-- Bottom Meta Gradient -->
          <div class="absolute bottom-0 inset-x-0 h-40 bg-gradient-to-t from-black via-black/60 to-transparent flex flex-col justify-end p-8">
             <div class="flex items-center mb-1">
               <span class="h-2 w-2 rounded-full bg-brand-primary mr-2 animate-pulse"></span>
               <span class="text-[10px] uppercase font-black text-white/60 tracking-[0.2em]">Cargada por</span>
             </div>
             <h4 class="text-white text-3xl font-black italic tracking-tight uppercase leading-none">{{ photos[0].guest_name || 'Invitado' }}</h4>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center justify-between w-full max-w-[280px] mt-8" *ngIf="photos.length > 0">
        <!-- Reject Button -->
        <button 
          (click)="swipe(-1)"
          class="h-16 w-16 bg-brand-danger/10 hover:bg-brand-danger/20 rounded-full border border-brand-danger/30 flex items-center justify-center text-brand-danger touch-scale shadow-2xl active:bg-brand-danger active:text-white transition-all">
          <span class="material-icons text-3xl font-bold">close</span>
        </button>

        <!-- Gallery Shortcut (Center) -->
        <div class="h-12 w-12 rounded-full border border-white/10 flex items-center justify-center opacity-40">
           <span class="material-icons text-xl">auto_awesome_motion</span>
        </div>

        <!-- Approve Button -->
        <button 
          (click)="swipe(1)"
          class="h-20 w-20 bg-brand-success rounded-full flex items-center justify-center text-brand-dark touch-scale shadow-[0_15px_30px_rgba(74,222,128,0.3)] hover:scale-110 active:scale-90 transition-all">
          <span class="material-icons text-5xl font-bold">favorite</span>
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; width: 100%; }
    .perspective-1000 { perspective: 1000px; }
  `]
})
export class TinderSwipeComponent {
  @Input() photos: EventPhoto[] = [];
  @Input() approverIndex: number = 1;
  @Output() onApprove = new EventEmitter<string>();
  @Output() onReject = new EventEmitter<string>();

  xOffset = signal<number>(0);
  rotation = signal<number>(0);
  Math = Math;

  range(n: number = 0): number[] {
    return Array.from({length: n}, (_, i) => i);
  }

  getPhotoUrl(photo: EventPhoto) {
     return `https://${window.location.hostname}:8020${photo.url}`;
  }

  swipe(direction: number) {
    if (this.photos.length === 0) return;
    
    // Animate out
    this.xOffset.set(direction * 600);
    this.rotation.set(direction * 40);

    setTimeout(() => {
      const topPhoto = this.photos[0];
      if (direction > 0) this.onApprove.emit(topPhoto.id);
      else this.onReject.emit(topPhoto.id);

      // Instantly reset position for the next one (which becomes the top one after the emit/slice)
      this.xOffset.set(0);
      this.rotation.set(0);
    }, 300);
  }
}
