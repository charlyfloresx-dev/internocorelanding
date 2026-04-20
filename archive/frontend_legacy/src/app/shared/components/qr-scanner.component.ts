
import { Component, output, OnDestroy, AfterViewInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

declare var Html5Qrcode: any;

@Component({
  selector: 'app-qr-scanner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- OVERLAY: bg-black/80 as requested -->
    <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-fade-in">
      
      <!-- MAIN CONTAINER: bg-gray-900 border-gray-700 -->
      <div class="relative w-full max-w-lg bg-gray-900 rounded-3xl border-2 border-gray-700 shadow-2xl overflow-hidden animate-fade-in-up mx-4 flex flex-col">
        
        <!-- HEADER: Large Close Button -->
        <div class="flex items-center justify-between p-6 border-b border-gray-800 bg-gray-950">
          <h3 class="text-white font-bold text-2xl flex items-center gap-3">
            <i class="fa-solid fa-qrcode text-sky-500"></i> Escanear Orden
          </h3>
          <!-- Fat Finger Close Button (w-14 h-14) -->
          <button (click)="closeScanner()" 
                  class="w-14 h-14 flex items-center justify-center rounded-full bg-gray-800 text-gray-400 border border-gray-700 hover:text-white hover:bg-red-500/20 hover:border-red-500/50 transition-all active:scale-95">
            <i class="fa-solid fa-times text-2xl"></i>
          </button>
        </div>

        <!-- SCANNER VIEWPORT -->
        <div class="relative bg-black aspect-square overflow-hidden group">
           <div id="reader" class="w-full h-full object-cover"></div>
           
           <!-- VISUAL GUIDE OVERLAY -->
           <div class="absolute inset-0 pointer-events-none flex items-center justify-center">
             <!-- Corner Guides -->
             <div class="w-72 h-72 relative">
               <div class="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-sky-500 rounded-tl-lg shadow-[0_0_15px_rgba(14,165,233,0.8)]"></div>
               <div class="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-sky-500 rounded-tr-lg shadow-[0_0_15px_rgba(14,165,233,0.8)]"></div>
               <div class="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-sky-500 rounded-bl-lg shadow-[0_0_15px_rgba(14,165,233,0.8)]"></div>
               <div class="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-sky-500 rounded-br-lg shadow-[0_0_15px_rgba(14,165,233,0.8)]"></div>
               
               <!-- Scan Line Animation -->
               <div class="absolute top-0 left-0 w-full h-1 bg-sky-400 shadow-[0_0_20px_rgba(14,165,233,1)] animate-scan opacity-80"></div>
             </div>
           </div>
           
           <!-- Loading State Mock -->
           <div id="scanner-loading" class="absolute inset-0 flex items-center justify-center bg-gray-900 z-0">
             <i class="fa-solid fa-camera text-gray-700 text-4xl animate-pulse"></i>
           </div>
        </div>

        <!-- FOOTER INSTRUCTIONS -->
        <div class="p-6 bg-gray-900 text-center border-t border-gray-800">
          <p class="text-white text-lg font-medium">Coloque el código QR dentro del marco</p>
          <p class="text-gray-500 text-sm mt-1">La lectura es automática</p>
        </div>
      </div>
    </div>
  `,
  styles: [`
    @keyframes scan {
      0% { transform: translateY(0); opacity: 0; }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { transform: translateY(288px); opacity: 0; } /* 288px matches h-72 */
    }
    .animate-scan {
      animation: scan 2.5s ease-in-out infinite;
    }
    /* Hide HTML5-QRCode default buttons if they appear */
    ::ng-deep #reader__dashboard_section_csr button {
      display: none !important;
    }
  `]
})
export class QrScannerComponent implements AfterViewInit, OnDestroy {
  scanSuccess = output<string>();
  close = output<void>();
  
  private html5QrCode: any;

  ngAfterViewInit() {
    const config = { 
      fps: 10, 
      qrbox: { width: 280, height: 280 },
      aspectRatio: 1.0
    };
    
    if (typeof Html5Qrcode === 'undefined') {
      console.error('Html5Qrcode library not loaded.');
      return;
    }

    this.html5QrCode = new Html5Qrcode("reader");

    this.html5QrCode.start(
      { facingMode: "environment" }, 
      config,
      (decodedText: string) => {
        this.handleScan(decodedText);
      },
      (errorMessage: any) => {
        // Parse error, ignore
      }
    ).then(() => {
      // Hide loading placeholder once camera starts
      const loader = document.getElementById('scanner-loading');
      if (loader) loader.style.display = 'none';
    }).catch((err: any) => {
      console.error("Error starting scanner", err);
    });
  }

  handleScan(text: string) {
    if (this.html5QrCode) {
      this.html5QrCode.stop().then(() => {
        this.html5QrCode.clear();
        this.scanSuccess.emit(text);
      }).catch((err: any) => console.log('Stop failed', err));
    }
  }

  closeScanner() {
    if (this.html5QrCode && this.html5QrCode.isScanning) {
      this.html5QrCode.stop().then(() => {
        this.html5QrCode.clear();
        this.close.emit();
      }).catch(() => {
        this.close.emit();
      });
    } else {
      this.close.emit();
    }
  }

  ngOnDestroy() {
    if (this.html5QrCode && this.html5QrCode.isScanning) {
       this.html5QrCode.stop().then(() => this.html5QrCode.clear());
    }
  }
}
