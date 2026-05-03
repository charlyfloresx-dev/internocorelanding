import { Injectable, inject, signal, computed } from '@angular/core';
import { MasterDataService, Warehouse, ProductPrice } from './master-data.service';
import { InventoryService } from './inventory.service';
import { AuthService } from './auth.service';
import { lastValueFrom, interval } from 'rxjs';

export interface HardwareStatus {
  id: string;
  name: string;
  type: 'SCANNER' | 'SCALE' | 'RFID';
  status: 'ONLINE' | 'OFFLINE' | 'MAINTENANCE';
  lastSeen: Date;
}

export interface CompanyActivity {
  timestamp: Date;
  user: string;
  action: string;
  module: string;
}

@Injectable({
  providedIn: 'root'
})
export class TenantDashboardService {
  private masterData = inject(MasterDataService);
  private inventory = inject(InventoryService);
  private auth = inject(AuthService);

  // === Signals ===
  hardwareStatus = signal<HardwareStatus[]>([
    { id: 'SCN-001', name: 'Zebra DS3608 (Line 1)', type: 'SCANNER', status: 'ONLINE', lastSeen: new Date() },
    { id: 'SCL-002', name: 'Mettler Toledo (Dock B)', type: 'SCALE', status: 'ONLINE', lastSeen: new Date() },
    { id: 'RFID-001', name: 'Impinj R700 (Main Gate)', type: 'RFID', status: 'MAINTENANCE', lastSeen: new Date() }
  ]);

  throughput24h = signal<number>(0);
  recentActivity = signal<CompanyActivity[]>([]);
  
  // Occupancy per warehouse
  warehouses = this.masterData.warehouses;
  
  totalOccupancy = computed(() => {
    const whs = this.warehouses();
    if (whs.length === 0) return 0;
    const totalCapacity = whs.reduce((acc, w) => acc + (w.capacity || 0), 0);
    const totalOccupancy = whs.reduce((acc, w) => acc + (w.current_occupancy || 0), 0);
    return totalCapacity > 0 ? (totalOccupancy / totalCapacity) * 100 : 0;
  });

  constructor() {
    this.initData();
    // Simulate some live changes
    interval(10000).subscribe(() => this.simulateTelemetry());
  }

  private async initData() {
    // In a real scenario, we would fetch throughput and activity from backend
    this.throughput24h.set(Math.floor(Math.random() * 50000) + 10000);
    this.recentActivity.set([
      { timestamp: new Date(), user: 'Charly Flores', action: 'Login Success', module: 'Auth' },
      { timestamp: new Date(Date.now() - 500000), user: 'System', action: 'Inventory Sync', module: 'WMS' },
      { timestamp: new Date(Date.now() - 1200000), user: 'Operator A', action: 'Work Order Started', module: 'MES' }
    ]);
  }

  private simulateTelemetry() {
    this.throughput24h.update(v => v + Math.floor(Math.random() * 500));
    this.hardwareStatus.update(current => {
      return current.map(h => ({
        ...h,
        status: Math.random() > 0.95 ? (h.status === 'ONLINE' ? 'OFFLINE' : 'ONLINE') : h.status,
        lastSeen: new Date()
      }));
    });
  }
}
