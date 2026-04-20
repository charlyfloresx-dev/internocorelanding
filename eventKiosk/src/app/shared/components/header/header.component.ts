import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WalletService } from '../../../core/services/wallet.service';
import { SessionService } from '../../../core/services/session.service';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="bg-brand-surface p-4 shadow-xl flex items-center justify-between sticky top-0 z-50 border-b border-white/5">
      <div class="flex flex-col">
        <span class="text-[9px] uppercase text-white/40 font-black tracking-widest leading-none mb-1">Paparazzi Wallet</span>
        <h1 class="text-brand-primary text-xl font-black leading-none tracking-tight">
          \${{ wallet.balanceFormatted() }} <span class="text-[10px] text-white/30 ml-0.5">MXN</span>
        </h1>
      </div>

      <div class="flex-1 max-w-[160px] ml-6 mr-4">
        <!-- Thermometer progress -->
        <div class="relative h-2.5 bg-brand-dark rounded-full overflow-hidden border border-white/5 ring-1 ring-white/10 shadow-inner">
          <div 
            class="h-full bg-gradient-to-r from-yellow-700 via-brand-primary to-yellow-300 transition-all duration-1000 ease-out shadow-[0_0_15px_rgba(226,183,20,0.4)]"
            [style.width.%]="wallet.progress()">
          </div>
        </div>
        
        <div class="flex justify-between items-center mt-1.5 h-3">
          <span class="text-[8px] text-white/30 uppercase font-black tracking-tighter">Meta Foto Gratis</span>
          
          <div class="flex items-center" *ngIf="wallet.canAffordFreePhoto()">
            <span class="material-icons text-[10px] text-brand-success mr-0.5 animate-pulse">check_circle</span>
            <span class="text-[9px] text-brand-success font-black uppercase tracking-tighter animate-pulse">¡LISTO!</span>
          </div>
          
          <span class="text-[8px] text-white/40 font-medium tabular-nums" *ngIf="!wallet.canAffordFreePhoto()">
            Faltan \${{ (wallet.PHOTO_PRICE - wallet.balanceCents()) / 100 }} para tu foto gratis
          </span>
        </div>
      </div>

      <div class="flex-shrink-0 touch-scale group curon-pointer">
        <div class="h-10 w-10 bg-brand-primary/10 rounded-xl flex items-center justify-center border border-brand-primary/20 group-hover:border-brand-primary transition-colors shadow-sm overflow-hidden">
          <img [src]="'https://api.dicebear.com/7.x/initials/svg?seed=' + session.guestSessionId()" class="w-full h-full" alt="Avatar">
        </div>
      </div>
    </header>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class HeaderComponent implements OnInit {
  wallet = inject(WalletService);
  session = inject(SessionService);

  ngOnInit() {
    // Initial fetch
    this.wallet.fetchBalance(this.session.guestSessionId());
    
    // Poll every 30 seconds for balance updates in background
    setInterval(() => {
      this.wallet.fetchBalance(this.session.guestSessionId());
    }, 30000);
  }
}
