import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class SessionService {
  // Normally initialized by a login/QR scanner or localStorage
  private _guestSessionId = signal<string>(
     localStorage.getItem('guest_id') || `guest-${Math.random().toString(16).slice(2, 8)}`
  );

  guestSessionId = this._guestSessionId.asReadonly();

  constructor() {
    localStorage.setItem('guest_id', this._guestSessionId());
  }
}
