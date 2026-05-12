import { Injectable, signal, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

declare var google: any;

export interface UserProfile {
  name: string;
  email: string;
  picture: string;
  token?: string;
}

@Injectable({ providedIn: 'root' })
export class GoogleAuthService {
  private platformId = inject(PLATFORM_ID);
  
  readonly user = signal<UserProfile | null>(null);
  readonly isAuthenticated = signal<boolean>(false);
  
  // Client ID proporcionado por Carlos
  private clientId = '865711103072-o4gj37pbf6o7umphbv0fti6l9d4i0a6r.apps.googleusercontent.com';

  constructor() {
    if (isPlatformBrowser(this.platformId)) {
      this.restoreSession();
      this.initGoogleAuth();
    }
  }

  private restoreSession() {
    const token = localStorage.getItem('google_auth_token');
    if (token) {
      try {
        const payload = this.decodeJwt(token);
        // Validar que el token no haya expirado
        if (payload.exp * 1000 > Date.now()) {
          this.user.set({
            name: payload.name,
            email: payload.email,
            picture: payload.picture,
            token: token
          });
          this.isAuthenticated.set(true);
          console.log('Sesión restaurada desde LocalStorage para:', payload.name);
        } else {
          localStorage.removeItem('google_auth_token');
        }
      } catch (e) {
        localStorage.removeItem('google_auth_token');
      }
    }
  }

  private initGoogleAuth() {
    const checkInterval = setInterval(() => {
      if (typeof google !== 'undefined') {
        clearInterval(checkInterval);
        google.accounts.id.initialize({
          client_id: this.clientId,
          callback: (response: any) => this.handleCredentialResponse(response),
          auto_select: false,
          cancel_on_tap_outside: true
        });
      }
    }, 100);
  }

  renderButton(elementId: string) {
    if (isPlatformBrowser(this.platformId)) {
      const checkInterval = setInterval(() => {
        if (typeof google !== 'undefined' && document.getElementById(elementId)) {
          clearInterval(checkInterval);
          google.accounts.id.renderButton(
            document.getElementById(elementId),
            { theme: 'filled_black', size: 'large', type: 'standard', shape: 'pill' }
          );
        }
      }, 100);
    }
  }

  private handleCredentialResponse(response: any) {
    const payload = this.decodeJwt(response.credential);
    localStorage.setItem('google_auth_token', response.credential);
    this.user.set({
      name: payload.name,
      email: payload.email,
      picture: payload.picture,
      token: response.credential
    });
    this.isAuthenticated.set(true);
    console.log('Login Exitoso:', this.user());
  }

  private decodeJwt(token: string) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  }

  logout() {
    localStorage.removeItem('google_auth_token');
    this.user.set(null);
    this.isAuthenticated.set(false);
    if (typeof google !== 'undefined') {
      google.accounts.id.disableAutoSelect();
    }
  }
}
