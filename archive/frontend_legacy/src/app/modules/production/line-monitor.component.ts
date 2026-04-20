
import { Component, inject, OnInit, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductionDataService } from '@services/production-data.service';
import { AuthService } from '@services/auth.service';
import { WorkOrderDto } from '@models/api.types';

@Component({
  selector: 'app-line-monitor',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="min-h-screen bg-black text-white p-4 lg:p-6 flex flex-col gap-6 relative overflow-hidden font-sans">
      
      <!-- BACKGROUND AMBIENCE -->
      <div class="absolute inset-0 bg-gradient-to-br from-gray-900 via-black to-slate-950 -z-10"></div>
      <div class="absolute top-0 right-0 w-[500px] h-[500px] bg-sky-900/10 rounded-full blur-[120px] -z-10 pointer-events-none"></div>

      <!-- HEADER ROW: Status & Info -->
      <header class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
        
        <!-- Left: Station Info -->
        <div class="flex items-center gap-6">
           <div class="w-20 h-20 rounded-xl bg-gray-900 border-2 border-gray-700 flex items-center justify-center shadow-inner">
             <i class="fa-solid fa-industry text-4xl text-gray-500"></i>
           </div>
           <div>
             <h2 class="text-gray-400 text-sm font-bold uppercase tracking-widest mb-1">Recurso / Estación</h2>
             <div class="text-4xl md:text-5xl font-black tracking-tight text-white">ENS-01</div>
             <div class="text-sky-500 font-bold flex items-center gap-2 mt-1">
               <i class="fa-solid fa-clock"></i> Turno Matutino
             </div>
           </div>
        </div>

        <!-- Right: Status Indicator (Big Signal) -->
        <div class="flex items-center gap-6">
           <div class="text-right hidden md:block">
             <div class="text-gray-500 text-xs font-bold uppercase mb-1">Operador Actual</div>
             <div class="text-xl font-bold flex items-center gap-2 justify-end">
               <img [src]="auth.currentUser()?.avatar" class="w-8 h-8 rounded-full border border-gray-600">
               {{ auth.currentUser()?.firstName }} {{ auth.currentUser()?.lastName }}
             </div>
           </div>
           
           <div class="h-20 px-8 rounded-xl bg-green-500/10 border-2 border-green-500 text-green-500 flex items-center gap-4 shadow-[0_0_30px_rgba(34,197,94,0.3)] animate-pulse">
             <div class="w-6 h-6 rounded-full bg-green-500"></div>
             <span class="text-3xl font-black tracking-wider">RUNNING</span>
           </div>
        </div>
      </header>

      <!-- MAIN CONTENT GRID -->
      <div class="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        <!-- LEFT COL: CURRENT ORDER INFO (Span 7) -->
        <div class="lg:col-span-7 bg-gray-900/50 rounded-3xl border border-gray-800 p-8 flex flex-col relative overflow-hidden">
          <div class="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <i class="fa-solid fa-barcode text-9xl"></i>
          </div>

          @if (currentOrder(); as order) {
             <div class="flex-1 flex flex-col justify-center z-10">
               <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-400 text-sm font-bold w-fit mb-6">
                 <i class="fa-solid fa-play"></i> ORDEN ACTIVA
               </div>
               
               <div class="space-y-2 mb-8">
                 <h3 class="text-gray-500 text-lg font-bold uppercase tracking-widest">Número de Orden</h3>
                 <div class="text-6xl md:text-7xl font-black text-white tracking-tighter">{{ order.orderNumber }}</div>
               </div>

               <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div>
                    <h3 class="text-gray-500 text-sm font-bold uppercase tracking-widest mb-2">Producto / Descripción</h3>
                    <div class="text-3xl font-bold text-white leading-tight mb-2">{{ order.productName }}</div>
                    <div class="text-xl text-sky-500 font-mono">{{ order.sku }}</div>
                  </div>

                  <!-- Product Image Placeholder -->
                  <div class="h-40 bg-black rounded-xl border border-gray-700 flex items-center justify-center relative overflow-hidden group">
                     <img [src]="'https://picsum.photos/seed/' + order.sku + '/400/200'" class="w-full h-full object-cover opacity-60 group-hover:opacity-100 transition-opacity">
                     <div class="absolute bottom-2 right-2 bg-black/60 px-2 py-1 rounded text-xs font-mono text-white">REF IMG</div>
                  </div>
               </div>
             </div>
          } @else {
             <div class="flex-1 flex flex-col items-center justify-center text-gray-600">
               <i class="fa-solid fa-ban text-6xl mb-4"></i>
               <h3 class="text-2xl font-bold">Sin Orden Asignada</h3>
               <p>Escanee una orden para comenzar</p>
             </div>
          }
        </div>

        <!-- RIGHT COL: LIVE COUNTERS (Span 5) -->
        <div class="lg:col-span-5 flex flex-col gap-6">
           
           <!-- Counter Card -->
           <div class="flex-1 bg-gray-900 rounded-3xl border border-gray-800 p-8 flex flex-col justify-center items-center text-center relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-b from-transparent to-black/50"></div>
              
              @if (currentOrder(); as order) {
                <h3 class="text-gray-500 text-sm font-bold uppercase tracking-widest mb-4 z-10">Progreso de Lote</h3>
                
                <div class="relative z-10 mb-6">
                  <!-- Circular Progress Mock (CSS) -->
                  <div class="text-7xl md:text-8xl font-black text-white tabular-nums tracking-tighter">
                    {{ order.quantityProduced }}
                    <span class="text-3xl text-gray-600 font-normal">/ {{ order.quantityTarget }}</span>
                  </div>
                </div>

                <!-- Progress Bar -->
                <div class="w-full h-6 bg-gray-800 rounded-full overflow-hidden relative z-10 border border-gray-700">
                   <div class="h-full bg-sky-500 transition-all duration-1000 ease-out relative overflow-hidden" [style.width.%]="order.progress">
                      <div class="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite]"></div>
                   </div>
                </div>
                <div class="mt-2 text-sky-400 font-bold text-xl z-10">{{ order.progress }}% Completado</div>
              }
           </div>

           <!-- Efficiency Grid -->
           <div class="h-40 grid grid-cols-2 gap-4">
              <div class="bg-gray-900 rounded-2xl border border-gray-800 flex flex-col items-center justify-center">
                 <div class="text-gray-500 text-xs font-bold uppercase mb-1">Eficiencia (OEE)</div>
                 <div class="text-4xl font-black text-green-500">85%</div>
              </div>
              <div class="bg-gray-900 rounded-2xl border border-gray-800 flex flex-col items-center justify-center">
                 <div class="text-gray-500 text-xs font-bold uppercase mb-1">Tiempo Ciclo</div>
                 <div class="text-4xl font-black text-white">45<span class="text-lg text-gray-500">s</span></div>
              </div>
           </div>

        </div>

      </div>

      <!-- FOOTER: Recent Activity Ticker -->
      <div class="h-12 border-t border-gray-800 flex items-center gap-4 text-sm text-gray-500 overflow-hidden">
        <span class="text-xs font-bold uppercase bg-gray-800 px-2 py-1 rounded text-gray-300">Log del Sistema</span>
        <div class="flex items-center gap-8 animate-marquee whitespace-nowrap">
           <span><i class="fa-solid fa-check text-green-500 mr-2"></i> 10:45 AM - Pieza #1140 completada correctamente.</span>
           <span><i class="fa-solid fa-info-circle text-sky-500 mr-2"></i> 10:42 AM - Ajuste de parámetros de máquina realizado por Supervisor.</span>
           <span><i class="fa-solid fa-triangle-exclamation text-yellow-500 mr-2"></i> 09:15 AM - Micro-paro registrado (30s) - Alimentación.</span>
        </div>
      </div>

    </div>
  `,
  styles: [`
    @keyframes shimmer {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(100%); }
    }
  `]
})
export class LineMonitorComponent implements OnInit, OnDestroy {
  public auth = inject(AuthService);
  public prodService = inject(ProductionDataService);

  // Signal for the single active order to display
  currentOrder = signal<WorkOrderDto | null>(null);

  // Simulation Interval
  private intervalId: any;

  ngOnInit() {
    this.prodService.loadWorkOrders();
    
    // Simulate finding the "active" order for this line (mocking the first running one)
    // In a real app, this would be fetched by lineId from route params
    const checkOrder = () => {
       const running = this.prodService.activeOrders().find(o => o.status === 'Running');
       this.currentOrder.set(running || null);
    };

    // Initial check (delay slightly to allow service to load)
    setTimeout(checkOrder, 500);

    // Live update simulation
    this.intervalId = setInterval(() => {
       if (this.currentOrder()) {
          // Simulate production increase
          this.currentOrder.update(o => {
            if (!o) return null;
            if (o.quantityProduced < o.quantityTarget) {
               const newQty = o.quantityProduced + 1;
               const newProg = Math.floor((newQty / o.quantityTarget) * 100);
               return { ...o, quantityProduced: newQty, progress: newProg };
            }
            return o;
          });
       } else {
         checkOrder();
       }
    }, 5000); // Update every 5 seconds
  }

  ngOnDestroy() {
    if (this.intervalId) clearInterval(this.intervalId);
  }
}
