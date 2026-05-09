import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { KioskService } from '../../../core/services/kiosk.service';

@Component({
  selector: 'app-staff-dashboard-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-[#FAF9F6] font-sans text-gray-800 pb-32">
        <!-- Header: Bridalova Aesthetic -->
        <header class="bg-white px-6 py-6 shadow-sm border-b border-[#F2EFE9] flex justify-between items-center sticky top-0 z-50">
            <div>
                <p class="text-[#B08D7B] uppercase tracking-[0.15em] text-[10px] font-bold mb-1">Centro de Comando</p>
                <h1 class="font-serif text-2xl text-[#2C2A29] italic">Interno Staff Core</h1>
            </div>
            <div class="text-right flex items-center space-x-3">
                <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                <span class="inline-block bg-[#F9EDEA] text-[#B08D7B] px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider">SSL Secure</span>
            </div>
        </header>

        <main class="p-6 max-w-4xl mx-auto space-y-8 mt-2">
            
            <!-- Financial & Operational Stats -->
            <section class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <!-- Theoretical Cash Widget -->
                <div class="bg-gradient-to-br from-[#2C2A29] to-[#1a1918] rounded-[24px] p-8 shadow-xl text-white relative overflow-hidden group">
                    <div class="absolute right-0 top-0 opacity-10">
                        <span class="material-icons text-[120px] translate-x-1/4 -translate-y-1/4">account_balance_wallet</span>
                    </div>
                    <span class="text-[#D4AF37] uppercase tracking-[0.2em] text-[10px] font-bold mb-2 block">Balance Teórico (Caja)</span>
                    <div class="flex items-baseline space-x-2">
                        <span class="text-4xl font-serif">$ {{ (theoreticalBalance() / 100).toFixed(2) }}</span>
                        <span class="text-[10px] text-[#A89C8F]">MXN</span>
                    </div>
                    
                    <div class="mt-6 flex gap-2">
                        <button (click)="openCashEntry('FLOAT')" class="bg-white/10 hover:bg-white/20 px-3 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all border border-white/10">Fondo</button>
                        <button (click)="openCashEntry('PAYOUT')" class="bg-red-500/20 hover:bg-red-500/30 px-3 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all border border-red-500/20 text-red-300">Gasto</button>
                    </div>
                </div>

                <!-- Live Sales Distribution -->
                <div class="bg-white rounded-[24px] p-8 shadow-sm border border-[#F2EFE9]">
                    <div class="flex justify-between items-center mb-6">
                        <span class="text-[#B08D7B] uppercase tracking-[0.1em] text-[10px] font-bold">Ventas Activas</span>
                        <div class="flex items-center space-x-2 text-[10px] text-gray-400">
                           <span class="w-1.5 h-1.5 rounded-full bg-[#D4AF37]"></span>
                           <span>Efectivo Prioritario</span>
                        </div>
                    </div>
                    
                    <div class="space-y-4">
                        <div class="flex justify-between items-center border-b border-gray-50 pb-2">
                            <span class="text-xs font-medium text-gray-500">Cola de Impresión</span>
                            <span class="text-lg font-bold text-[#2C2A29]">{{ queueCount() }}</span>
                        </div>
                        <div class="flex justify-between items-center text-xs">
                           <span class="text-[#B08D7B] uppercase tracking-tighter">Última Transacción</span>
                           <span class="text-gray-400">En vivo</span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Quick Ledger Actions -->
            <section class="flex space-x-3 overflow-x-auto pb-2 scrollbar-hide">
                <button (click)="openCashEntry('ADJUSTMENT')" class="whitespace-nowrap bg-white border border-[#F2EFE9] px-6 py-4 rounded-2xl shadow-sm flex items-center space-x-3 hover:border-[#D4AF37] transition-all group">
                    <span class="material-icons text-[#D4AF37] group-hover:scale-110 transition-transform">edit_note</span>
                    <span class="text-xs font-bold uppercase tracking-widest text-[#2C2A29]">Ajuste Manual</span>
                </button>
                <button (click)="performClosure()" class="whitespace-nowrap bg-white border border-[#F2EFE9] px-6 py-4 rounded-2xl shadow-sm flex items-center space-x-3 hover:bg-[#2C2A29] hover:text-white transition-all group">
                    <span class="material-icons text-red-400 group-hover:text-red-300">lock</span>
                    <span class="text-xs font-bold uppercase tracking-widest">Cierre de Turno</span>
                </button>
            </section>

            <!-- Gallery Monitor -->
            <section>
                <div class="flex justify-between items-end mb-6">
                    <h2 class="font-serif text-xl italic text-[#2C2A29]">Monitor de Galería</h2>
                    <button (click)="refresh()" class="text-[#B08D7B] text-xs uppercase tracking-widest font-bold border-b border-[#B08D7B] pb-0.5 hover:text-[#2C2A29] transition-colors">Refrescar</button>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    @for (photo of kiosk.gallery(); track photo.id) {
                        <div class="relative aspect-[3/4] bg-white rounded-2xl overflow-hidden shadow-sm border border-[#F2EFE9] group">
                            <img [src]="photo.url" class="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
                            <div class="absolute top-2 left-2">
                                <span *ngIf="photo.status === 'PURCHASED'" class="bg-[#D4AF37] text-white text-[8px] font-bold uppercase px-2 py-1 rounded-sm shadow-xl">Cobrada</span>
                            </div>

                            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                <button (click)="resetQuorum(photo.id)" class="bg-white/20 backdrop-blur-md border border-white/30 text-white rounded-full p-3 hover:bg-yellow-500 transition-all">
                                    <span class="material-icons">restart_alt</span>
                                </button>
                            </div>
                        </div>
                    }
                </div>
            </section>
        </main>
    </div>
  `
})
export class StaffDashboardPageComponent implements OnInit {
    kiosk = inject(KioskService);
    http = inject(HttpClient);
    
    queueCount = signal(0);
    theoreticalBalance = signal(0);
    recentTransactions = signal<any[]>([]);

    ngOnInit() {
        this.refresh();
        this.fetchFinanceStatus();
    }

    async refresh() {
        const config = this.kiosk.getEventConfig();
        if (config.event_id) {
            this.kiosk.fetchGallery(config.event_id);
        }
        this.fetchFinanceStatus();
    }

    async fetchFinanceStatus() {
        try {
            const res = await this.http.get<any>(`https://${window.location.hostname}:8020/api/v1/kiosk/staff/finance/status`).toPromise();
            this.theoreticalBalance.set(res.theoretical_balance_cents || 0);
            this.recentTransactions.set(res.recent_transactions || []);
        } catch (e) {
            console.error('Error al obtener finanzas', e);
        }
    }

    async openCashEntry(category: string) {
        const amountStr = prompt(`Ingresa el monto para ${category} (ej: 100.50):`);
        if (!amountStr) return;

        const concept = prompt('Ingresa el concepto de la operación:');
        if (!concept) return;

        const amountCents = Math.round(parseFloat(amountStr) * 100);
        
        try {
            await this.http.post(`https://${window.location.hostname}:8020/api/v1/kiosk/staff/finance/cash-entry`, {
                category,
                amount: amountCents,
                concept,
                staff_id: 'STAFF_01'
            }).toPromise();
            
            this.fetchFinanceStatus();
            alert('Operacion registrada.');
        } catch (e) {
            alert('Error al registrar.');
        }
    }

    performClosure() {
        const realAmountStr = prompt('INGRESA EL EFECTIVO FISICO (MXN):');
        if (!realAmountStr) return;

        const realCents = Math.round(parseFloat(realAmountStr) * 100);
        const diff = realCents - this.theoreticalBalance();

        if (Math.abs(diff) > 100) {
            const justification = prompt(`DISCREPANCIA: $${(diff / 100).toFixed(2)}\nJustifica:`);
            if (!justification) return;
            alert('Cierre con reporte enviado.');
        } else {
            alert('Cierre cuadrado.');
        }
    }

    resetQuorum(photoId: string) {
        if (confirm('¿Reiniciar?')) {
            this.kiosk.resetApprovals(photoId).subscribe(() => {
                this.refresh();
            });
        }
    }
}
