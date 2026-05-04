// temp_future/src/app/modules/billing/pages/subscription/subscription.component.ts
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { BillingService, Plan } from '../../../../core/services/billing.service';
import { ThemeService } from '../../../../core/services/theme.service';
import { TranslationService } from '../../../../core/services/translation.service';
import { ToastService } from '../../../../core/services/toast.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-subscription',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="min-h-screen p-4 md:p-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
      <!-- Header -->
      <header class="max-w-6xl mx-auto mb-16">
        <h1 class="text-4xl md:text-6xl font-black uppercase tracking-tighter mb-4 text-slate-900 dark:text-white leading-none">
          Escala tu Operación: <span class="text-primary">Suscripciones</span>
        </h1>
        <p class="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-widest text-xs md:text-sm max-w-2xl">
          Selecciona el nivel de potencia que tu empresa necesita. Desde el núcleo operativo hasta la digitalización industrial total.
        </p>
      </header>

      <!-- Current Status Banner -->
      @if (billing.subscription(); as sub) {
        <div class="max-w-6xl mx-auto mb-12 p-8 rounded-3xl border border-primary/20 bg-primary/5 backdrop-blur-3xl flex flex-col md:flex-row items-center justify-between gap-8 group hover:border-primary/40 transition-all">
          <div class="flex items-center gap-6">
            <div class="w-16 h-16 rounded-2xl bg-primary/20 flex items-center justify-center text-primary animate-pulse">
              <mat-icon class="text-3xl">verified_user</mat-icon>
            </div>
            <div>
              <p class="text-[10px] font-black text-primary uppercase tracking-[0.3em] mb-1">Estado del Tenant</p>
              <h2 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
                {{ sub.status === 'TRIAL' ? 'Periodo de Prueba' : 'Suscripción ' + sub.status }}
              </h2>
              <p class="text-xs font-medium text-slate-500 dark:text-slate-400">
                Tu plan actual es <b>{{ sub.plan.name }}</b>. Vence el: {{ sub.current_period_end | date:'mediumDate' }}
              </p>
            </div>
          </div>
          
          <div class="flex items-center gap-4">
             <div class="text-right hidden sm:block">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-none mb-1">Días Restantes</p>
                <p class="text-2xl font-black text-slate-900 dark:text-white">14</p>
             </div>
             <button class="px-8 py-3 bg-primary text-ic-dark font-black uppercase tracking-widest text-[10px] rounded-xl hover:scale-105 transition-transform shadow-lg shadow-primary/20">
                Gestionar Cuenta
             </button>
          </div>
        </div>
      }

      <!-- Plans Grid -->
      <div class="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
        @for (plan of plans; track plan.id) {
          <div 
            class="relative flex flex-col p-8 rounded-[2.5rem] border border-surface-border bg-surface-card/30 backdrop-blur-xl transition-all duration-500 hover:scale-[1.02] hover:bg-surface-card/50 overflow-hidden group"
            [class.border-primary/40]="plan.is_popular"
            [class.shadow-2xl]="plan.is_popular"
            [class.shadow-primary/10]="plan.is_popular"
          >
            <!-- Popular Badge -->
            @if (plan.is_popular) {
              <div class="absolute top-8 right-8 px-4 py-1 bg-primary text-ic-dark text-[8px] font-black uppercase tracking-widest rounded-full">
                Recomendado
              </div>
            }

            <div class="mb-10">
              <div class="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center text-primary mb-6 group-hover:scale-110 transition-transform">
                <mat-icon>{{ plan.icon }}</mat-icon>
              </div>
              <h3 class="text-2xl font-black text-slate-900 dark:text-white uppercase tracking-tight mb-2">{{ plan.name }}</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400 font-medium leading-relaxed">{{ plan.description }}</p>
            </div>

            <div class="mb-10 flex items-baseline gap-1">
              <span class="text-4xl font-black text-slate-900 dark:text-white">$</span>
              <span class="text-6xl font-black text-slate-900 dark:text-white tracking-tighter">{{ plan.price }}</span>
              @if (plan.id === 'plan_enterprise') {
                <span class="text-3xl font-black text-primary -ml-2 tracking-tighter">+</span>
              }
              <span class="text-slate-500 dark:text-slate-400 font-bold uppercase text-[10px] tracking-widest ml-2">/ Mes</span>
            </div>

            <ul class="flex-1 space-y-4 mb-12">
              @for (feat of plan.features; track feat) {
                <li class="flex items-center gap-3 text-xs font-bold text-slate-600 dark:text-slate-300">
                  <mat-icon class="text-primary text-sm">check_circle</mat-icon>
                  {{ feat }}
                </li>
              }
            </ul>

            <button 
              (click)="checkout(plan.id)"
              class="w-full py-4 rounded-2xl font-black uppercase tracking-[0.2em] text-[10px] transition-all relative overflow-hidden group/btn"
              [class.bg-primary]="plan.is_popular"
              [class.text-ic-dark]="plan.is_popular"
              [class.bg-white/5]="!plan.is_popular"
              [class.text-white]="!plan.is_popular"
              [class.hover:bg-primary]="!plan.is_popular"
              [class.hover:text-ic-dark]="!plan.is_popular"
            >
              <span class="relative z-10">Seleccionar Plan</span>
              <div class="absolute inset-0 bg-white/20 translate-y-full group-hover/btn:translate-y-0 transition-transform duration-300"></div>
            </button>
          </div>
        }
      </div>

      <!-- Footer Help -->
      <footer class="max-w-6xl mx-auto mt-20 p-8 rounded-3xl border border-dashed border-surface-border flex flex-col md:flex-row items-center justify-between gap-6 opacity-60">
        <div class="flex items-center gap-4">
          <mat-icon class="text-slate-400">help_outline</mat-icon>
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">¿Necesitas un plan personalizado para múltiples plantas?</p>
        </div>
        <button class="text-[10px] font-black text-primary uppercase tracking-[0.2em] hover:underline">Contactar a Ventas</button>
      </footer>
    </div>
  `
})
export class SubscriptionComponent implements OnInit {
  billing = inject(BillingService);
  theme = inject(ThemeService);
  router = inject(Router);
  toast = inject(ToastService);

  plans = [
    {
      id: 'plan_operative',
      name: 'Plan Operativo',
      description: 'Gestión esencial para micro-operaciones. Incluye el núcleo del sistema.',
      price: 45,
      icon: 'receipt_long',
      is_popular: false,
      features: [
        'Core (Inventario + Catálogo)',
        'Centro de Tickets Individiales',
        'Gestión de Almacén Básica',
        'Hasta 3 usuarios concurrentes',
        'Soporte por Email'
      ]
    },
    {
      id: 'plan_industrial',
      name: 'Plan Industrial',
      description: 'Potencia total para plantas de manufactura. Control total de piso y logística.',
      price: 350,
      icon: 'precision_manufacturing',
      is_popular: true,
      features: [
        'Todo lo del Plan Operativo',
        'Módulo de Producción (MES)',
        'Logística Avanzada (WMS)',
        'Usuarios Ilimitados',
        'Ahorro del 15% incluido'
      ]
    },
    {
      id: 'plan_enterprise',
      name: 'Full Enterprise',
      description: 'Ecosistema completo sin restricciones. Arquitectura escalable y prioritaria.',
      price: 550,
      icon: 'diamond',
      is_popular: false,
      features: [
        'Todos los Módulos Activos',
        'Soporte Prioritario 24/7',
        'Integración ERP Custom',
        'Infraestructura Dedicada',
        'Account Manager Dedicado'
      ]
    }
  ];

  ngOnInit() {
    this.billing.loadSubscriptionStatus();
  }

  async checkout(planId: string) {
    this.toast.info('Iniciando pasarela de pago segura...', 'Billing');
    try {
      const clientSecret = await this.billing.createCheckoutSession();
      // En una implementación real, aquí usaríamos el Stripe SDK para abrir el modal embedded
      // O redirigir a una página de Stripe.
      console.log('Stripe Client Secret:', clientSecret);
      this.toast.success('Sesión de pago preparada. Redirigiendo...', 'Success');
      
      // Mock de redirección por ahora
      // window.location.href = `https://checkout.stripe.com/pay/${clientSecret}`;
    } catch (err) {
      this.toast.error('Error al conectar con el proveedor de pagos', 'Billing Error');
    }
  }
}
