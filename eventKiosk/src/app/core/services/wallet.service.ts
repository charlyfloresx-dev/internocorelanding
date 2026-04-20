import { Injectable, signal, computed, effect, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { celebrate } from '../utils/celebrate';

@Injectable({
  providedIn: 'root'
})
export class WalletService {
  private http = inject(HttpClient);
  
  // Settings (Could come from an environment or config endpoint)
  readonly PHOTO_PRICE = 5000; // in cents
  readonly REWARD_PER_SALE = 500; // in cents (10-to-1)

  // Pure State
  private _balanceCents = signal<number>(0);
  
  // Public Computed Signals
  balanceCents = computed(() => this._balanceCents());
  balanceFormatted = computed(() => (this._balanceCents() / 100).toFixed(2));
  
  // Progress towards a free photo (0 to 100)
  progress = computed(() => {
    const current = this._balanceCents();
    if (current >= this.PHOTO_PRICE) return 100;
    return (current / this.PHOTO_PRICE) * 100;
  });

  canAffordFreePhoto = computed(() => this._balanceCents() >= this.PHOTO_PRICE);

  constructor() {
    // Watch for balance increases to celebrate!
    let previousBalance = 0;
    effect(() => {
      const current = this._balanceCents();
      if (current > previousBalance) {
        celebrate();
      }
      previousBalance = current;
    });
  }

  setBalance(cents: number) {
    this._balanceCents.set(cents);
  }

  fetchBalance(guestSessionId: string) {
    this.http.get<any>(`https://${window.location.hostname}:8020/api/v1/kiosk/staff/finance/status`)
      .subscribe(resp => {
        // Mapeamos el balance teórico al wallet
        this.setBalance(resp.theoretical_balance_cents || 0);
      }, err => {
        console.error('Error wallet fallback', err);
        this.setBalance(0);
      });
  }
}
