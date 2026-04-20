import { Component, inject } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { HeaderComponent } from '../header/header.component';
import { CommonModule } from '@angular/common';
import { CameraUploadService } from '../../../core/services/camera-upload.service';

@Component({
  selector: 'app-kiosk-layout',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, RouterLink, RouterLinkActive, CommonModule],
  template: `
    <div class="min-h-screen bg-brand-dark overflow-x-hidden flex flex-col pb-24">
      <!-- HEADER -->
      <app-header></app-header>

      <!-- VIEWPORT -->
      <main class="flex-grow">
        <router-outlet></router-outlet>
      </main>

      <!-- UPLOAD OVERLAY (If uploading) -->
      <div *ngIf="upload.isUploading()" class="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex flex-col items-center justify-center p-8">
         <div class="relative h-32 w-32 mb-6">
            <svg class="w-full h-full transform -rotate-90">
              <circle cx="64" cy="64" r="60" stroke="currentColor" stroke-width="8" fill="transparent" class="text-white/10"></circle>
              <circle cx="64" cy="64" r="60" stroke="currentColor" stroke-width="8" fill="transparent" 
                class="text-brand-primary transition-all duration-300"
                [style.stroke-dasharray]="377"
                [style.stroke-dashoffset]="377 - (377 * upload.uploadProgress() / 100)"></circle>
            </svg>
            <div class="absolute inset-0 flex items-center justify-center flex-col">
               <span class="text-2xl font-black text-white italic">{{ upload.uploadProgress() }}%</span>
            </div>
         </div>
         <h3 class="text-white font-black text-xl uppercase tracking-widest animate-pulse">Optimizando Obra Maestra...</h3>
         <p class="text-white/40 text-xs mt-2 font-medium">Comprimiendo imagen para impresión de alta fidelidad</p>
      </div>

      <!-- BOTTOM NAV BAR -->
      <nav class="fixed bottom-0 inset-x-0 h-20 bg-brand-surface/90 backdrop-blur-xl border-t border-white/5 px-6 flex items-center justify-around z-50">
        <!-- Gallery -->
        <a routerLink="/gallery" routerLinkActive="text-brand-primary" class="flex flex-col items-center justify-center space-y-1 transition-colors text-white/40">
           <span class="material-icons text-2xl">grid_view</span>
           <span class="text-[9px] font-black uppercase">Galería</span>
        </a>

        <!-- Camera / Upload / Gallery -->
        <div class="relative -top-6">
          <label class="h-16 w-16 bg-brand-primary rounded-full shadow-2xl shadow-brand-primary/40 flex items-center justify-center text-brand-dark border-4 border-brand-dark active:scale-95 transition-transform cursor-pointer">
             <span class="material-icons text-3xl font-black">add_a_photo</span>
             <input type="file" accept="image/*,video/*" multiple class="hidden" (change)="onFileSelected($event)">
          </label>
        </div>

        <!-- Approval (Novio Mode) -->
        <a routerLink="/approval" routerLinkActive="text-brand-primary" class="flex flex-col items-center justify-center space-y-1 transition-colors text-white/40">
           <span class="material-icons text-2xl">favorite_border</span>
           <span class="text-[9px] font-black uppercase tracking-tighter">Aprobación</span>
        </a>
      </nav>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class KioskLayoutComponent {
  upload = inject(CameraUploadService);
  eventId = '3fa85f64-5717-4562-b3fc-2c963f66afa6'; // Mock

  onFileSelected(event: any) {
    const files = event.target.files;
    if (files && files.length > 0) {
      this.upload.compressAndUpload(files, this.eventId);
    }
  }
}
