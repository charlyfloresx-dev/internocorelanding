
import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: number;
  title?: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class ToastService {
  toasts = signal<Toast[]>([]);
  private counter = 0;

  // Added optional 'title' parameter for better context
  show(message: string, type: Toast['type'] = 'info', title?: string, duration: number = 4000) {
    // Simple logging as requested for debugging
    console.log(`[Toast Service] ${type.toUpperCase()}: ${message}`);
    const id = ++this.counter;
    const toast: Toast = { id, message, type, title, duration };
    
    this.toasts.update(current => [...current, toast]);

    if (duration > 0) {
      setTimeout(() => this.remove(id), duration);
    }
  }

  remove(id: number) {
    this.toasts.update(current => current.filter(t => t.id !== id));
  }

  // Helper methods with default titles based on type
  success(msg: string, title: string = 'Operación Exitosa') { this.show(msg, 'success', title); }
  error(msg: string, title: string = 'Error del Sistema') { this.show(msg, 'error', title, 6000); } // Longer duration for errors
  info(msg: string, title: string = 'Información') { this.show(msg, 'info', title); }
  warning(msg: string, title: string = 'Atención') { this.show(msg, 'warning', title); }
}
