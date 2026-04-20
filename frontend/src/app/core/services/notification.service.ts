import {Injectable, signal} from '@angular/core';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  notifications = signal<Notification[]>([]);

  show(type: NotificationType, title: string, message: string, duration = 5000) {
    const id = Math.random().toString(36).substring(2, 9);
    const notification: Notification = { id, type, title, message, duration };
    
    this.notifications.update(prev => [...prev, notification]);

    if (duration > 0) {
      setTimeout(() => {
        this.remove(id);
      }, duration);
    }
  }

  success(title: string, message: string) {
    this.show('success', title, message);
  }

  error(title: string, message: string) {
    this.show('error', title, message);
  }

  warning(title: string, message: string) {
    this.show('warning', title, message);
  }

  info(title: string, message: string) {
    this.show('info', title, message);
  }

  remove(id: string) {
    this.notifications.update(prev => prev.filter(n => n.id !== id));
  }
}
