import { Component, inject, signal, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-setup-page',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="min-h-screen bg-brand-dark p-8 flex flex-col items-center">
        <!-- Logo Header -->
        <div class="mb-10 text-center">
            <h1 class="text-white text-4xl font-black italic uppercase tracking-tighter">Event Onboarding</h1>
            <p class="text-white/60 font-medium mt-2">Configura el kiosko y genera tus accesos en formato QR.</p>
        </div>

        <div class="w-full max-w-4xl space-y-8" *ngIf="!setupComplete()">
            
            <!-- Selection vs Creation Toggle -->
            <div class="flex justify-center space-x-4 mb-4">
                <button (click)="showEventList.set(true)" [class]="showEventList() ? 'bg-brand-primary text-brand-dark' : 'bg-white/10 text-white'" class="px-6 py-2 rounded-full font-bold transition-all">
                    Seleccionar Existente
                </button>
                <button (click)="showEventList.set(false)" [class]="!showEventList() ? 'bg-brand-primary text-brand-dark' : 'bg-white/10 text-white'" class="px-6 py-2 rounded-full font-bold transition-all">
                    Crear Nuevo
                </button>
            </div>

            <div *ngIf="showEventList()" class="bg-brand-surface border border-white/10 rounded-3xl p-8 w-full">
                <h3 class="text-brand-primary font-bold uppercase tracking-widest text-sm mb-6">Eventos en la Base de Datos</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div *ngFor="let ev of existingEvents()" (click)="selectEvent(ev)" class="p-4 bg-black/40 border border-white/10 rounded-2xl cursor-pointer hover:border-brand-primary transition-all group">
                        <div class="flex justify-between items-center">
                            <div>
                                <h4 class="text-white font-bold group-hover:text-brand-primary">{{ev.name}}</h4>
                                <p class="text-white/40 text-xs mt-1">Precio: {{ev.photo_price / 100}} | Paparazzi: {{ev.rule_paparazzi ? 'SI' : 'NO'}}</p>
                            </div>
                            <span class="material-icons text-brand-primary opacity-0 group-hover:opacity-100 transition-opacity">arrow_forward</span>
                        </div>
                    </div>
                </div>
                <div *ngIf="existingEvents().length === 0" class="text-center py-10 text-white/40">
                    No hay eventos registrados. Crea uno nuevo.
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8" *ngIf="!showEventList()">
                <!-- Left: Configurations -->
                <div class="bg-brand-surface border border-white/10 rounded-3xl p-8">
                    <h3 class="text-brand-primary font-bold uppercase tracking-widest text-sm mb-6">1. Identidad Visual</h3>
                    
                    <div class="space-y-4 mb-8">
                        <div>
                            <p class="text-white/80 text-sm mb-2 font-medium">Nombre del Evento</p>
                            <input type="text" [(ngModel)]="eventName" class="w-full bg-black/30 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-brand-primary" placeholder="Ej: Boda Carlos y Paulina">
                        </div>

                        <div class="flex flex-col space-y-4 sm:flex-row sm:space-y-0 sm:items-center sm:space-x-4">
                            <label class="flex-1 cursor-pointer bg-brand-primary/20 border border-brand-primary/50 text-brand-primary rounded-xl px-4 py-3 text-center font-bold relative hover:bg-brand-primary/30 transition-colors">
                                <input type="file" (change)="onFileSelected($event)" accept="image/png, image/jpeg, image/svg+xml" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer">
                                <span class="material-icons align-middle mr-2">cloud_upload</span>
                                <span>Subir Logo (PNG/SVG)</span>
                            </label>
                            <button (click)="generateTextLogo()" class="px-4 py-3 bg-white/10 rounded-xl text-white/80 hover:bg-white/20 transition-colors font-medium whitespace-nowrap">
                                Auto-generar texto
                            </button>
                        </div>
                        
                        <div *ngIf="logoPreview()" class="h-32 w-full bg-black/50 border border-white/10 rounded-xl flex flex-col items-center justify-center relative overflow-hidden">
                           <!-- We show checkered background for transparency -->
                           <div class="absolute inset-0" style="background-image: radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px); background-size: 10px 10px;"></div>
                           <img [src]="logoPreview()" class="max-h-full max-w-full object-contain relative z-10 p-2" />
                        </div>
                        <p class="text-white/40 text-xs italic text-center" *ngIf="logoPreview()">(El Kiosko insertará este watermark en cada print 4x6)</p>
                    </div>

                    <h3 class="text-brand-primary font-bold uppercase tracking-widest text-sm mb-6">2. Parámetros de Negocio</h3>
                    
                    <div class="space-y-6">
                        <div>
                            <p class="text-white/80 text-sm mb-2 font-medium">Precio por Foto (MXN)</p>
                            <div class="flex items-center">
                                <span class="text-white/50 text-xl font-black mr-2">$</span>
                                <input type="number" [(ngModel)]="photoPrice" class="w-full text-2xl font-black bg-black/30 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-brand-primary" placeholder="50.00">
                            </div>
                        </div>

                        <div class="flex items-center justify-between p-4 bg-black/30 rounded-xl border border-white/10">
                            <div>
                                <p class="text-white font-bold">Regla Paparazzi (10 a 1)</p>
                                <p class="text-white/50 text-xs mt-1">Recompensa al fotógrafo original con un 10% si alguien más compra su foto.</p>
                            </div>
                            <label class="relative inline-flex items-center cursor-pointer ml-4">
                                <input type="checkbox" [(ngModel)]="rulePaparazzi" class="sr-only peer">
                                <div class="w-11 h-6 bg-white/20 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-primary"></div>
                            </label>
                        </div>

                        <div>
                            <p class="text-white/80 text-sm mb-2 font-medium">Número de Aprobadores</p>
                            <input type="number" [(ngModel)]="requiredApprovals" class="w-full bg-black/30 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-brand-primary" placeholder="2">
                            <p class="text-white/40 text-xs mt-1">Cuántas personas distintas deben dar el visto bueno a una foto.</p>
                        </div>
                    </div>

                </div>

                <!-- Right: Action -->
                <div class="flex flex-col justify-center items-center">
                    <button (click)="onSubmit()" [disabled]="isLoading() || !eventName" class="w-full md:w-auto px-12 py-6 bg-brand-primary text-brand-dark rounded-[30px] font-black text-2xl uppercase tracking-tighter hover:scale-105 active:scale-95 transition-transform shadow-[0_20px_50px_rgba(255,215,0,0.2)] disabled:opacity-50 disabled:hover:scale-100">
                        {{ isLoading() ? 'Configurando...' : 'Crear Evento Oficial' }}
                    </button>
                    <p class="text-white/40 mt-8 text-center max-w-sm text-sm">
                        Al confirmar, inicializaremos la instancia local base de datos y generaremos los 3 QRs de acceso.
                    </p>
                </div>
            </div>
        </div>

        <!-- Success Result: The 3 QRs -->
        <div class="w-full max-w-6xl space-y-12" *ngIf="setupComplete()">
            <div class="text-center">
                <h2 class="text-brand-success text-3xl font-black italic uppercase tracking-tighter mb-2">¡Fábrica de Eventos Inicializada!</h2>
                <p class="text-white/60">Aquí tienes tus accesos maestros. Descárgalos o pásalos.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <!-- Guest -->
                <div class="bg-brand-surface rounded-3xl p-6 flex flex-col items-center border-t-8 border-blue-500 shadow-2xl">
                    <div class="w-full flex items-center justify-center space-x-2 mb-2 text-blue-500">
                        <span class="material-icons">camera_alt</span>
                        <h3 class="font-black text-xl uppercase">El QR Público</h3>
                    </div>
                    <p class="text-white/50 text-xs text-center mb-6">Para los centros de mesa. Escanea y recauda fotos.</p>
                    <div class="p-4 bg-white rounded-2xl mb-4 shadow-xl">
                        <img [src]="qrs()?.guest_qr" class="w-48 h-48" />
                    </div>
                    <a [href]="qrs()?.guest_url" target="_blank" class="text-blue-400 text-xs underline truncate w-full text-center hover:text-white">Ver App</a>
                </div>

                <!-- Staff -->
                <div class="bg-brand-surface rounded-3xl p-6 flex flex-col items-center border-t-8 border-purple-500 shadow-2xl">
                    <div class="w-full flex items-center justify-center space-x-2 mb-2 text-purple-500">
                        <span class="material-icons">qr_code_scanner</span>
                        <h3 class="font-black text-xl uppercase">El QR Staff</h3>
                    </div>
                    <p class="text-white/50 text-xs text-center mb-6">Carga en la tablet general para escáner físico y cobrar mermas.</p>
                    <div class="p-4 bg-white rounded-2xl mb-4 shadow-xl">
                        <img [src]="qrs()?.staff_qr" class="w-48 h-48" />
                    </div>
                    <a [href]="qrs()?.staff_url" target="_blank" class="text-purple-400 text-xs underline truncate w-full text-center hover:text-white">Ver App</a>
                </div>

                <!-- Approvers Dynamic -->
                <ng-container *ngFor="let approver of qrs()?.approvers">
                    <div class="bg-brand-surface rounded-3xl p-6 flex flex-col items-center border-t-8 border-yellow-500 shadow-2xl">
                        <div class="w-full flex items-center justify-center space-x-2 mb-2 text-yellow-500">
                            <span class="material-icons">task_alt</span>
                            <h3 class="font-black text-xl uppercase">Aprobador #{{approver.index}}</h3>
                        </div>
                        <p class="text-white/50 text-xs text-center mb-6">Escanea este QR para validar las fotos del evento.</p>
                        <div class="p-4 bg-white rounded-2xl mb-4 shadow-xl">
                            <img [src]="approver.qr" class="w-48 h-48" />
                        </div>
                        <a [href]="approver.url" target="_blank" class="text-brand-primary text-xs underline truncate w-full text-center hover:text-white">Ir a App</a>
                    </div>
                </ng-container>
            </div>

            <div class="flex justify-center mt-12">
               <button (click)="reset()" class="text-white/50 hover:text-white transition-colors uppercase tracking-widest text-xs font-bold border-b border-white/20 pb-1">Retornar al Setup (Borrar Evento)</button>
            </div>
        </div>

        <!-- Hidden canvas for text-to-logo -->
        <canvas #watermarkCanvas width="600" height="200" style="display:none;"></canvas>
    </div>
  `
})
export class SetupPageComponent {
  @ViewChild('watermarkCanvas') canvasRef!: ElementRef<HTMLCanvasElement>;
  private http = inject(HttpClient);
  
  eventName = '';
  photoPrice = 50;
  rulePaparazzi = true;
  requiredApprovals = 2; // Default
  logoPreview = signal<string | null>(null);
  
  isLoading = signal(false);
  setupComplete = signal(false);
  qrs = signal<any>(null);

  // New: Event selection
  existingEvents = signal<any[]>([]);
  showEventList = signal(true); // Toggle between select and create

  constructor() {
    this.fetchEvents();
  }

  async fetchEvents() {
    try {
      const events = await this.http.get<any[]>(`https://${window.location.hostname}:8020/api/v1/kiosk/onboarding/`).toPromise();
      this.existingEvents.set(events || []);
      if (events && events.length > 0) {
        this.showEventList.set(true);
      } else {
        this.showEventList.set(false);
      }
    } catch (e) {
      console.error("Error fetching events", e);
      this.showEventList.set(false);
    }
  }

  async selectEvent(event: any) {
    this.isLoading.set(true);
    try {
      const res = await this.http.get<any>(`https://${window.location.hostname}:8020/api/v1/kiosk/onboarding/${event.id}/qrs?frontend_base_url=${window.location.origin}`).toPromise();
      this.qrs.set(res.qrs);
      this.eventName = res.event_name;
      this.setupComplete.set(true);
    } catch (e) {
      console.error("Error selecting event", e);
      alert("Error al cargar los QRs del evento.");
    }
    this.isLoading.set(false);
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.logoPreview.set(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  }

  generateTextLogo() {
    if (!this.eventName) {
        this.eventName = "C & J + Fecha"; // Fallback demo
    }
    const canvas = this.canvasRef.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Clear
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Config font
    ctx.fillStyle = '#ffffff'; // White text
    ctx.shadowColor = 'rgba(0,0,0,0.5)';
    ctx.shadowBlur = 4;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Draw Name
    ctx.font = 'bold 60px serif';
    ctx.fillText(this.eventName, canvas.width / 2, canvas.height / 2);
    
    // Add "Interno Core Moments" tiny
    ctx.font = 'italic 20px sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.fillText('Capturado por Interno Core', canvas.width / 2, canvas.height / 2 + 50);
    
    const dataUrl = canvas.toDataURL('image/png');
    this.logoPreview.set(dataUrl);
  }

  async onSubmit() {
      this.isLoading.set(true);
      try {
          const payload = {
              event_name: this.eventName.replace(/\s+/g, '_'),
              photo_price: this.photoPrice * 100, // cents
              rule_paparazzi: this.rulePaparazzi,
              required_approvals: this.requiredApprovals,
              watermark_b64: this.logoPreview(),
              frontend_base_url: window.location.origin
          };

          const res = await this.http.post<any>(`https://${window.location.hostname}:8020/api/v1/kiosk/onboarding/setup`, payload).toPromise();
          
          this.qrs.set(res.qrs);
          this.setupComplete.set(true);
      } catch (e) {
          console.error("Error setting up event", e);
          alert("Hubo un error configurando el evento. Revisa el backend.");
      }
      this.isLoading.set(false);
  }

  reset() {
      this.setupComplete.set(false);
      this.eventName = '';
      this.logoPreview.set(null);
      this.qrs.set(null);
  }
}
