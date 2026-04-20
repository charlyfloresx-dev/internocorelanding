import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap, timer, switchMap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiResponse } from './models/api-response.model';

export interface BookingStatus {
  status: 'CONFIRMED' | 'PENDING' | 'NO_BOOKING';
  group_id: string;
  package_name: string;
  is_active: boolean;
  last_sky_sentinel?: string;
  last_stay_guardian?: string;
  is_grace_period?: boolean;
}

export interface PaymentHistory {
  id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class PaymentService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8012/api/v1'; // Moved to 8012 to avoid chrome conflicts on 8011

  // Signals for Reactive State
  public bookingStatus = signal<BookingStatus | null>(null);
  public paymentHistory = signal<PaymentHistory[]>([]);
  public isLoading = signal<boolean>(true);

  // Computed Values
  public isLocked = computed(() => this.bookingStatus()?.status !== 'CONFIRMED');

  constructor() {
    // Auto-start polling on service initialization
    this.startStatusPolling();
    this.refreshPaymentHistory();
  }

  private startStatusPolling() {
    timer(0, 5000).pipe(
      switchMap(() => this.getBookingStatus()),
      takeUntilDestroyed()
    ).subscribe(response => {
      // BINGO: El middleware envuelve ahora la respuesta en { status: 'success', data: {...} }
      // Debemos desempacar .data para que el signal reciba el BookingStatus real
      this.bookingStatus.set((response as any).data || response);
      this.isLoading.set(false);
    });
  }

  public refreshPaymentHistory() {
    this.getPaymentHistory().subscribe(history => this.paymentHistory.set(history));
  }

  getBookingStatus() {
    return this.http.get<BookingStatus>(`${this.apiUrl}/booking/status`);
  }

  getPaymentHistory() {
    return this.http.get<PaymentHistory[]>(`${this.apiUrl}/payments/history`);
  }

  createCheckoutSession(groupId: string) {
    const payload = {
      group_id: groupId,
      success_url: `${window.location.origin}/dashboard?success=true`,
      cancel_url: `${window.location.origin}/dashboard?cancel=true`
    };
    return this.http.post<{ checkout_url: string }>(`${this.apiUrl}/payments/create-checkout-session`, payload);
  }

  downloadItinerary(groupId: string) {
    return this.http.get(`${this.apiUrl}/booking/itinerary/${groupId}/download`, {
      responseType: 'blob'
    });
  }
}


