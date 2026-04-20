import { Component, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PaymentService } from '../../core/payment.service';

@Component({
  selector: 'app-traveler-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './traveler-dashboard.component.html',
  styleUrl: './traveler-dashboard.component.scss'
})
export class TravelerDashboardComponent {
  public paymentService = inject(PaymentService);

  // Derivations for UI
  public status = this.paymentService.bookingStatus;
  public isLocked = this.paymentService.isLocked;
  public payments = this.paymentService.paymentHistory;
  public loading = this.paymentService.isLoading;

  constructor() {
    // Optional: Log status changes
    effect(() => {
      console.log('Operational Status Update:', this.status());
    });
  }

  onPayClick() {
    const status = this.status();
    if (status?.group_id) {
      this.paymentService.createCheckoutSession(status.group_id).subscribe(res => {
        if (res.checkout_url) {
          window.location.href = res.checkout_url;
        }
      });
    }
  }

  async downloadItinerary() {
    const status = this.status();
    if (status?.group_id) {
      const gid = status.group_id;
      
      this.paymentService.downloadItinerary(gid).subscribe({
        next: async (blob: Blob) => {
          // Cache the blob for offline use
          const cache = await caches.open('viatra-itineraries');
          await cache.put(`/itinerary-${gid}`, new Response(blob));
          this.triggerDownload(blob);
        },
        error: async (err) => {
          console.error('Backend offline, checking cache...');
          const cache = await caches.open('viatra-itineraries');
          const cachedRes = await cache.match(`/itinerary-${gid}`);
          if (cachedRes) {
            const blob = await cachedRes.blob();
            this.triggerDownload(blob, true);
          } else {
            alert('No se pudo descargar el itinerario y no hay copia offline.');
          }
        }
      });
    }
  }

  private triggerDownload(blob: Blob, isOffline = false) {
    const status = this.status();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Itinerario_${status?.package_name || 'Viaje'}${isOffline ? '_Copia_Local' : ''}.pdf`;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}



