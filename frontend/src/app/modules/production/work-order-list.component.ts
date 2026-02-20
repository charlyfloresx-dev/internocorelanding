import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ProductionDataService } from '@services/production-data.service';
import { ToastService } from '@services/toast.service';
import { WorkOrderDto } from '@models/api.types';

@Component({
  selector: 'app-work-order-list',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="p-6 space-y-6 animate-fade-in-up">
      
      <div class="flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-white tracking-tight">Work Orders</h1>
          <p class="text-slate-400 text-sm">Manage production schedule and execution</p>
        </div>
        <button class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-lg shadow-lg shadow-sky-900/20 transition-all flex items-center gap-2">
          <i class="fa-solid fa-plus"></i> New Order
        </button>
      </div>

      <!-- Orders Table -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
                <th class="p-4 font-bold">Order #</th>
                <th class="p-4 font-bold">Product</th>
                <th class="p-4 font-bold">Progress</th>
                <th class="p-4 font-bold">Status</th>
                <th class="p-4 font-bold">Due Date</th>
                <th class="p-4 font-bold text-right">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800">
              @for (order of data.activeOrders(); track order.id) {
                <tr class="hover:bg-slate-800/50 transition-colors group">
                  <td class="p-4">
                    <span class="font-mono text-sky-400 font-bold">{{ order.orderNumber }}</span>
                    <div class="text-xs text-slate-500">{{ order.lineId }}</div>
                  </td>
                  <td class="p-4">
                    <div class="font-bold text-white">{{ order.productName }}</div>
                    <div class="text-xs text-slate-500">{{ order.sku }}</div>
                  </td>
                  <td class="p-4 w-48">
                    <div class="flex justify-between text-xs mb-1">
                      <span class="text-slate-300">{{ order.quantityProduced }} / {{ order.quantityTarget }}</span>
                      <span class="text-sky-400 font-bold">{{ order.progress }}%</span>
                    </div>
                    <div class="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                      <div class="bg-sky-500 h-full rounded-full transition-all duration-500" [style.width.%]="order.progress"></div>
                    </div>
                  </td>
                  <td class="p-4">
                    <span class="px-2 py-1 rounded text-[10px] font-bold uppercase border"
                          [ngClass]="{
                            'bg-green-500/10 text-green-400 border-green-500/20': order.status === 'Running',
                            'bg-yellow-500/10 text-yellow-400 border-yellow-500/20': order.status === 'Pending',
                            'bg-red-500/10 text-red-400 border-red-500/20': order.status === 'Delayed' || order.status === 'Risk'
                          }">
                      {{ order.status }}
                    </span>
                  </td>
                  <td class="p-4 text-sm text-slate-300">
                    {{ order.dueDate | date:'mediumDate' }}
                  </td>
                  <td class="p-4 text-right">
                    <button class="text-slate-500 hover:text-white transition-colors p-2">
                      <i class="fa-solid fa-ellipsis-vertical"></i>
                    </button>
                  </td>
                </tr>
              }
              @if (data.activeOrders().length === 0) {
                <tr>
                  <td colspan="6" class="p-8 text-center text-slate-500">
                    No active work orders found.
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `
})
export class WorkOrderListComponent implements OnInit {
  public data = inject(ProductionDataService);

  ngOnInit() {
    this.data.loadWorkOrders();
  }
}