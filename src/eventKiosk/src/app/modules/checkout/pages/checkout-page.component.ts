import { Component, inject, OnInit, ViewChild, ElementRef, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { loadStripe, Stripe, StripeElements, StripePaymentElement } from '@stripe/stripe-js';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-checkout-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="h-full flex flex-col pt-8 bg-brand-dark px-6 pb-32">
      <div class="mb-8">
        <h2 class="text-white text-3xl font-black italic uppercase leading-none mb-1 tracking-tighter">Tu Selección</h2>
        <p class="text-white/40 text-xs font-bold uppercase tracking-widest">
           3 Fotos listas para imprimir
        </p>
      </div>

      <!-- Payment Summary -->
      <div class="bg-brand-surface rounded-[30px] p-6 mb-6 border border-white/10 shadow-2xl">
         <div class="flex justify-between items-center mb-4">
             <span class="text-white/60 text-sm font-medium">Subtotal (3)</span>
             <span class="text-white font-bold">$150.00 MXN</span>
         </div>
          <div class="h-px w-full bg-white/5 mb-4"></div>
          <div class="flex justify-between items-center" *ngIf="walletDeducted() > 0">
              <span class="text-white/60 text-sm font-medium">Descuento (Monedero)</span>
              <span class="text-brand-success font-bold">-$ {{ (walletDeducted() / 100).toFixed(2) }} MXN</span>
          </div>
          <div class="flex justify-between items-center mt-2">
              <span class="text-white/60 text-sm font-medium">Total a pagar</span>
              <span class="text-brand-primary font-black text-2xl tracking-tighter">$ {{ (amountDue() / 100).toFixed(2) }} MXN</span>
          </div>
       </div>
 
       <!-- Payment Methods -->
       <div class="space-y-4" *ngIf="!paymentComplete()">
          <button 
             (click)="toggleWallet()"
             class="w-full flex items-center justify-between p-4 rounded-2xl border-2 transition-transform"
             [ngClass]="useWallet() ? 'border-brand-primary bg-brand-primary/10 text-brand-primary' : 'border-white/10 bg-brand-surface text-white/60'">
              <div class="flex items-center space-x-3">
                  <span class="material-icons text-3xl">account_balance_wallet</span>
                  <div class="flex flex-col text-left">
                      <span class="font-black text-sm uppercase tracking-wider">Usar Monedero</span>
                  </div>
              </div>
              <span class="material-icons opacity-50">{{ useWallet() ? 'check_circle' : 'circle' }}</span>
          </button>
 
          <div class="w-full h-px relative bg-white/5 my-8">
              <span class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-brand-dark px-4 text-xs font-bold text-white/30 uppercase tracking-widest">Pago con Tarjeta</span>
          </div>
 
          <!-- Stripe Mount Point -->
          <div class="bg-white rounded-2xl p-4 min-h-[200px]" [class.hidden]="!elements || amountDue() === 0">
               <div #paymentElement></div>
          </div>
          <div *ngIf="isLoading()" class="flex justify-center p-4">
              <span class="material-icons animate-spin text-brand-primary text-3xl">loop</span>
          </div>
 
          <button *ngIf="elements || amountDue() === 0"
             (click)="handlePayment()"
             [disabled]="isLoading()"
             class="w-full mt-4 h-16 bg-brand-primary rounded-full text-brand-dark font-black uppercase tracking-widest shadow-[0_15px_30px_rgba(255,215,0,0.3)] active:scale-95 transition-transform disabled:opacity-50">
              {{ amountDue() === 0 ? 'Confirmar Pago en Créditos' : 'Pagar Seguro' }}
          </button>
       </div>
 
       <!-- Success Screen -->
       <div *ngIf="paymentComplete()" class="flex flex-col items-center justify-center p-8 bg-brand-surface rounded-[40px] border border-brand-primary/20 shadow-[0_0_50px_rgba(255,215,0,0.1)] text-center mt-8">
           <div class="relative w-24 h-24 mb-6">
              <div class="absolute inset-0 bg-brand-primary/20 rounded-full animate-ping"></div>
              <div class="absolute inset-2 bg-brand-primary rounded-full flex items-center justify-center shadow-xl">
                 <span class="material-icons text-brand-dark text-4xl">print</span>
              </div>
           </div>
           <h3 class="text-white text-2xl font-black italic uppercase tracking-tighter mb-2">¡Pago Exitoso!</h3>
           <p class="text-white/60 text-sm font-medium max-w-[200px] leading-relaxed">
               Tus fotos están en la fila de impresión. Acércate al quiosco en 2 minutos para recogerlas.
           </p>
       </div>
     </div>
   `
 })
 export class CheckoutPageComponent implements OnInit {
   @ViewChild('paymentElement') paymentElementRef!: ElementRef;
   
   private http = inject(HttpClient);
   
   stripe: Stripe | null = null;
   elements: StripeElements | null = null;
   paymentElement: StripePaymentElement | null = null;
   
   isLoading = signal(true);
   paymentComplete = signal(false);
   
   totalCents = signal(15000); // MOCK 3 photos x 50
   walletDeducted = signal(0);
   amountDue = signal(15000);
   useWallet = signal(false);
   
   // STRIPE_PUB
   stripePubKey = 'pk_test_51T82t2F8I6Cop2aUrcc9PM8SnkJgvzDXz2XU6mDS9zhp5HN3ROdqzR4903kbwWRcYSOQS3piILXolAoA1Y8vAAqK00rdofsmRp'; 
 
   async ngOnInit() {
     this.stripe = await loadStripe(this.stripePubKey);
     await this.initializeStripe();
   }
 
   toggleWallet() {
       this.useWallet.set(!this.useWallet());
       this.isLoading.set(true);
       if (this.elements) {
           this.elements.getElement('payment')?.destroy();
           this.elements = null;
       }
       this.initializeStripe();
   }
 
   async initializeStripe() {
     try {
         const payload = {
             photo_ids: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000003'], 
             company_id: '00000000-0000-0000-0000-000000000002',
             event_id: '00000000-0000-0000-0000-000000000003',
             guest_session_id: 'GUEST_001',
             method: 'STRIPE',
             use_wallet_balance: this.useWallet()
         };
 
         const res = await this.http.post<any>(`https://${window.location.hostname}:8020/api/v1/kiosk/payments/checkout`, payload).toPromise();
         
         this.totalCents.set(res.total_cents);
         this.walletDeducted.set(res.wallet_deducted);
         this.amountDue.set(res.amount_due);
 
         if (res.status === 'COMPLETED') {
             // Wallet paid 100%
             this.elements = null;
         } else if (res.stripe_client_secret) {
            this.mountStripeElement(res.stripe_client_secret);
         }
 
         this.isLoading.set(false);
     } catch (e) {
         console.error("Error init Stripe", e);
         this.isLoading.set(false);
     }
   }
 
   mountStripeElement(clientSecret: string) {
       if (!this.stripe) return;
       
       this.elements = this.stripe.elements({ clientSecret, appearance: { theme: 'night' } });
       this.paymentElement = this.elements.create('payment');
       this.paymentElement.mount(this.paymentElementRef.nativeElement);
   }
 
   async handlePayment() {
       if (this.amountDue() === 0) {
           // 100% Wallet Paid
           this.paymentComplete.set(true);
           return;
       }
 
       if (!this.stripe || !this.elements) return;
       
       this.isLoading.set(true);
       const { error } = await this.stripe.confirmPayment({
           elements: this.elements,
           redirect: 'if_required' 
       });
       
       if (error) {
           console.error('[Stripe Error]', error);
           // Podríamos mostrar UI Error aquí
       } else {
           // Success!
           this.paymentComplete.set(true);
       }
       this.isLoading.set(false);
   }
 }
