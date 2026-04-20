import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { firstValueFrom } from 'rxjs';

export interface Currency {
  code: string;
  name: string;
  symbol: string;
}

@Injectable({
  providedIn: 'root'
})
export class CurrencyService {
  private http = inject(HttpClient);
  private readonly STORAGE_KEY = '_ic_currency';
  
  // Lista inmutable de monedas soportadas
  readonly currencies: Currency[] = [
    { code: 'USD', name: 'US Dollar', symbol: '$' },
    { code: 'MXN', name: 'Peso Mexicano', symbol: '$' }
  ];

  // Señales para el estado reactivo
  private _selectedCurrencyCode = signal<string>(this.getInitialCurrency());
  private _conversionRates = signal<Record<string, number>>({ 'USD': 1.0, 'MXN': 16.85 });
  
  // Dashboard de Decisión (Fuentes de Verdad)
  markets = signal<Record<string, number>>({});

  // Señal combinada para la moneda actual
  currentCurrency = computed(() => {
    const code = this._selectedCurrencyCode();
    return this.currencies.find(c => c.code === code) || this.currencies[0];
  });

  constructor() {
    this.refreshRates();
  }

  private getInitialCurrency(): string {
    return localStorage.getItem(this.STORAGE_KEY) || 'USD';
  }

  /**
   * Cambia la moneda activa y persiste en localStorage.
   */
  setCurrency(code: string) {
    if (this.currencies.some(c => c.code === code)) {
      this._selectedCurrencyCode.set(code);
      localStorage.setItem(this.STORAGE_KEY, code);
    }
  }

  /**
   * Sincroniza las tasas de cambio con el backend real.
   */
  async refreshRates() {
    try {
      const baseUrl = environment.currencyUrl;
      const response = await firstValueFrom(
        this.http.get<{ 
          status: string, 
          data: { base: string, rates: Record<string, number>, markets?: Record<string, number> }, 
          message: string 
        }>(`${baseUrl}/currencies/active-rate`)
      );
      
      if (response && response.status === 'success' && response.data?.rates) {
        // Aseguramos que USD siempre sea 1.0 si es la base
        const { base, rates, markets } = response.data;
        this._conversionRates.set({ ...rates, [base]: 1.0 });
        if (markets) {
           this.markets.set(markets);
        }
        console.log('[CurrencyService] ✅ Rates synchronized successfully.');
      }
    } catch (error) {
      console.warn('[CurrencyService] ⚠️ Could not refresh rates from backend. Falling back to default rates.', error);
      // Fallback is already set in the signal initialization
    }
  }

  /**
   * Persiste una tasa manual en el backend y actualiza la UI.
   */
  async manualUpdateRate(rate: number) {
    try {
      const baseUrl = environment.currencyUrl;
      const response = await firstValueFrom(
        this.http.post<{ status: string, data: any }>(`${baseUrl}/currencies/manual`, {
          base_currency: 'USD',
          target_currency: 'MXN',
          rate: rate
        })
      );

      if (response && response.status === 'success') {
        // Actualizar el signal local de tasas inmediatamente
        const current = this._conversionRates();
        this._conversionRates.set({ ...current, 'MXN': rate });
        return true;
      }
      return false;
    } catch (error) {
      console.error('[CurrencyService] ❌ Failed to persist manual rate:', error);
      return false;
    }
  }

  /**
   * Convierte un monto de USD a la moneda seleccionada.
   */
  convert(amount: number): number {
    const code = this._selectedCurrencyCode();
    const rate = this._conversionRates()[code] || 1.0;
    return amount * rate;
  }

  /**
   * Formatea un monto según la moneda activa.
   */
  format(amount: number): string {
    const convertedAmount = this.convert(amount);
    const currency = this.currentCurrency();

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.code,
      minimumFractionDigits: 2
    }).format(convertedAmount);
  }
}
