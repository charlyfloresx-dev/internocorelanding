import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, forkJoin, map, of, timer, switchMap, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/domain.types';

export type HealthStatus = 'online' | 'degraded' | 'offline';

@Injectable({
  providedIn: 'root'
})
export class SystemHealthService {
  private http = inject(HttpClient);

  // --- Signals ---
  private _authStatus = signal<boolean>(true);
  private _inventoryStatus = signal<boolean>(true);
  private _masterDataStatus = signal<boolean>(true);
  private _lastCheck = signal<Date>(new Date());

  public authStatus = this._authStatus.asReadonly();
  public inventoryStatus = this._inventoryStatus.asReadonly();
  public masterDataStatus = this._masterDataStatus.asReadonly();
  public lastCheck = this._lastCheck.asReadonly();

  /**
   * Overall status of the system cluster
   */
  public overallStatus = computed<HealthStatus>(() => {
    if (!this._authStatus()) return 'offline'; // Auth is critical
    if (!this._inventoryStatus() || !this._masterDataStatus()) return 'degraded';
    return 'online';
  });

  /**
   * Write Lock Signal: Used by components to disable save/create buttons
   */
  public isReadOnly = computed(() => this.overallStatus() !== 'online');

  constructor() {
    // Start polling every 5 minutes (300,000ms)
    timer(0, 300000).pipe(
      switchMap(() => this.checkAllServices())
    ).subscribe();
  }

  /**
   * Manual heartbeat reporting from other services
   */
  public reportSuccess(service: 'auth' | 'inventory' | 'masterData') {
    this.updateStatus(service, true);
  }

  public reportFailure(service: 'auth' | 'inventory' | 'masterData') {
    this.updateStatus(service, false);
  }

  private updateStatus(service: 'auth' | 'inventory' | 'masterData', status: boolean) {
    switch (service) {
      case 'auth': this._authStatus.set(status); break;
      case 'inventory': this._inventoryStatus.set(status); break;
      case 'masterData': this._masterDataStatus.set(status); break;
    }
    this._lastCheck.set(new Date());
  }

  private checkAllServices() {
    const check = (url: string) => this.http.get<ApiResponse<any>>(url).pipe(
      map(res => res.status === 'success'),
      catchError(() => of(false))
    );

    return forkJoin({
      auth: check(`${environment.authUrl.replace('/api/v1', '')}/`), // Auth responde en '/'
      inventory: check(`${environment.inventoryUrl.replace('/api/v1', '')}/health`),
      masterData: check(`${environment.masterDataUrl.replace('/api/v1', '')}/health`)
    }).pipe(
      tap(results => {
        this._authStatus.set(results.auth);
        this._inventoryStatus.set(results.inventory);
        this._masterDataStatus.set(results.masterData);
        this._lastCheck.set(new Date());
      })
    );
  }
}
