
import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ErrorStateService {
  hasError = signal(false);
  errorMessage = signal('');

  triggerError(msg: string) {
    if (!this.hasError()) {
      this.hasError.set(true);
      const cleanMsg = msg.replace('Uncaught (in promise):', '').trim();
      this.errorMessage.set(cleanMsg);
    }
  }

  reset() {
    this.hasError.set(false);
    this.errorMessage.set('');
    // Clear potentially corrupted storage before reload
    localStorage.removeItem('interno_core_db');
    localStorage.removeItem('interno_session');
    window.location.href = window.location.pathname; 
  }
}
