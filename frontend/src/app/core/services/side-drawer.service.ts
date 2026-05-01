import { Injectable, signal, Type } from '@angular/core';
import { Subject } from 'rxjs';

export interface DrawerOptions {
  title: string;
  subtitle?: string;
  icon?: string;
  width?: string; // e.g. 'w-96' or 'w-[500px]'
}

@Injectable({
  providedIn: 'root'
})
export class SideDrawerService {
  isOpen = signal(false);
  component = signal<Type<any> | null>(null);
  data = signal<any>(null);
  options = signal<DrawerOptions>({ title: 'Detalles' });

  private refreshSubject = new Subject<any>();
  refresh$ = this.refreshSubject.asObservable();

  /**
   * Notifica que se debe refrescar la data.
   */
  notifyRefresh(payload?: any) {
    this.refreshSubject.next(payload);
  }

  /**
   * Abre el drawer con un componente específico y datos opcionales.
   */
  open<T>(component: Type<T>, options: DrawerOptions, data?: any) {
    this.component.set(component);
    this.options.set(options);
    this.data.set(data);
    this.isOpen.set(true);
  }

  /**
   * Cierra el drawer y limpia el estado.
   */
  close() {
    this.isOpen.set(false);
    // Delay clearing component to allow animation to finish
    setTimeout(() => {
      this.component.set(null);
      this.data.set(null);
    }, 500);
  }
}
