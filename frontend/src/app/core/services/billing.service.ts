// temp_future/src/app/core/services/billing.service.ts
import { inject, Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { firstValueFrom } from 'rxjs';
import { ApiResponse } from '../models/domain.types';

export interface Plan {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  modules: string[];
}

export interface Subscription {
  id: string;
  plan: Plan;
  status: string;
  start_date: string;
  current_period_end: string;
  readonly: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class BillingService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private baseUrl = `${environment.apiUrl}/v1/billing`;

  private _subscription = signal<Subscription | null>(null);
  private _plans = signal<Plan[]>([]);
  private _loading = signal<boolean>(false);

  readonly subscription = computed(() => this._subscription());
  readonly plans = computed(() => this._plans());
  readonly loading = computed(() => this._loading());

  async loadSubscriptionStatus() {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) return;

    this._loading.set(true);
    try {
      const resp = await firstValueFrom(
        this.http.get<ApiResponse<Subscription>>(`${this.baseUrl}/status`)
      );
      this._subscription.set(resp.data);
    } catch (e) {
      console.error('[BillingService] Error loading subscription:', e);
    } finally {
      this._loading.set(false);
    }
  }

  async loadAvailablePlans() {
    try {
      const resp = await firstValueFrom(
        this.http.get<ApiResponse<Plan[]>>(`${this.baseUrl}/plans`)
      );
      this._plans.set(resp.data);
    } catch (e) {
      console.error('[BillingService] Error loading plans:', e);
    }
  }

  async createCheckoutSession() {
    const companyId = this.auth.activeCompanyId();
    if (!companyId) throw new Error('No company selected');

    try {
      const resp = await firstValueFrom(
        this.http.post<ApiResponse<{ client_secret: string }>>(
          `${this.baseUrl}/sessions/create-embedded`, 
          {}, 
          { headers: { 'X-Company-ID': companyId } }
        )
      );
      return resp.data.client_secret;
    } catch (e) {
      console.error('[BillingService] Error creating session:', e);
      throw e;
    }
  }
}
