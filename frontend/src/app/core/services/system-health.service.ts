import { Injectable, signal, computed } from '@angular/core';

export type ServiceStatus = 'online' | 'degraded' | 'offline';

@Injectable({ providedIn: 'root' })
export class SystemHealthService {
  // Signals para rastrear cada microservicio
  status = signal<{ [key: string]: boolean }>({
    auth: true,
    masterData: true,
    wms: true
  });

  // Signal computado para el color del "foquito"
  overallStatus = computed<ServiceStatus>(() => {
    const states = this.status();
    if (!states['auth']) return 'offline'; // Rojo (Crítico)
    if (!states['masterData'] || !states['wms']) return 'degraded'; // Amarillo (Resiliente/Caché)
    return 'online'; // Verde (Todo OK)
  });

  // Signal para modo de solo lectura (Bloqueo de Escritura)
  // Centralizamos la lógica aquí para que cualquier componente pueda consumirla
  isReadOnly = computed(() => this.overallStatus() !== 'online');

  // Signal computado para el tooltip detallado
  tooltipMessage = computed(() => {
    const s = this.status();
    return `Sistemas: [Auth: ${s['auth']?'OK':'ERR'}, MasterData: ${s['masterData']?'OK':'Cache'}, WMS: ${s['wms']?'OK':'Cache'}]`;
  });

  updateStatus(service: 'auth' | 'masterData' | 'wms', isUp: boolean) {
    this.status.update(prev => ({ ...prev, [service]: isUp }));
  }
}