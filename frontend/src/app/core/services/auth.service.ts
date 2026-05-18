// temp_future/src/app/core/services/auth.service.ts
import { Injectable, signal, computed, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { lastValueFrom, Observable, BehaviorSubject, of } from 'rxjs';
import { AuthSession, AuthHandshake, ApiResponse, SubscriptionStatus } from '../models/domain.types';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  public isBrowser = isPlatformBrowser(this.platformId);
  private apiUrl = environment.authUrl;

  // === Signals ===
  public session = signal<AuthSession | null>(null);
  public handshake = signal<AuthHandshake | null>(null);
  public isLoading = signal<boolean>(false);
  public authStep = signal<'login' | 'handshake' | 'verified'>('login');

  // 🔄 Token Rotation State (for Interceptor buffering)
  public isRefreshing = signal<boolean>(false);
  public refreshTokenSubject = new BehaviorSubject<string | null>(null);

  // ⚡ Companies persistidas explícitamente (patrón legacy: sobrevive a recargas)
  private _companies = signal<any[]>([]);

  // === Computed ===
  public availableCompanies = computed(() => this._companies());
  public availableAccesses = this.availableCompanies; // Alias for tenant-selection

  public isAuthenticated = computed(() => !!this.session());
  public currentUser = computed(() => this.session()?.user ?? null);
  public roles = computed(() => this.session()?.roles ?? []);
  public permissions = computed(() => this.session()?.permissions ?? []);
  public activeCompanyId = computed(() => this.session()?.company_id || null);

  public subscriptionStatus = computed(() => this.session()?.status || SubscriptionStatus.ACTIVE);

  public isUnpaid = computed(() => this.subscriptionStatus() === SubscriptionStatus.UNPAID);

  public isSuperAdmin = computed(() => {
    const roles = this.roles();
    const permissions = this.permissions();
    return roles.some(r => r === 'admin' || r === 'owner') || permissions.includes('*');
  });

  public isReadOnly = computed(() => {
    const isRestricted = this.subscriptionStatus() === SubscriptionStatus.RESTRICTED;
    const isExplicitReadOnly = !!this.session()?.readonly;
    return isRestricted || isExplicitReadOnly || this.roles().some(r => r.toLowerCase().includes('viewer'));
  });

  public hasPermission(permission: string): boolean {
    const current = this.permissions();
    if (this.isSuperAdmin()) return true;
    return current.includes(permission) || current.includes('*');
  }

  constructor(private router: Router) {
    // Initial silent restoration from storage (optimistic UI)
    if (this.isBrowser) {
      this.restoreFromStorage();
    }
  }


  /**
   * Universal Session Injector (Backend Scopes -> Frontend Permissions)
   */
  public setSession(data: AuthSession) {
    console.group('Auth: Set Session');

    // Safety Mapping: Convert scopes (backend) to permissions (frontend)
    if ((data as any).scopes && (!data.permissions || data.permissions.length === 0)) {
      data.permissions = (data as any).scopes;
    }

    this.session.set(data);
    this.authStep.set('verified');

    if (this.isBrowser) {
      localStorage.setItem('auth_session', JSON.stringify(data));
      // Legacy Context (Used by Interceptors)
      localStorage.setItem('_ic_auth_ctx', JSON.stringify({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        company_id: data.company_id,
        user_id: data.user_id,
        roles: data.roles,
        company_name: (data as any).company_name || 'InternoCorp Enterprise'
      }));
    }
    console.log('[AuthService] ✅ Session persisted with refresh_token & permissions');
    console.groupEnd();
  }

  /**
   * Step 1: Handshake (Credential Validation -> Company List)
   */
  public async login(credentials: any): Promise<void> {
    console.group('Auth login (T1)');
    this.isLoading.set(true);
    try {
      const resp = await lastValueFrom(
        this.http.post<ApiResponse<AuthHandshake>>(`${this.apiUrl}/auth/login`, credentials)
      );

      const handshakeData = resp.data;
      if (!handshakeData) throw new Error('Handshake failed: empty response');

      this.handshake.set(handshakeData);
      this.authStep.set('handshake');

      // ✅ PERSISTIR LISTA DE EMPRESAS (patrón legacy: sobrevive recargas de página)
      if (this.isBrowser && handshakeData.companies?.length) {
        this._companies.set(handshakeData.companies);
        localStorage.setItem('_ic_companies', JSON.stringify(handshakeData.companies));
      }

      if (this.isBrowser) {
        sessionStorage.setItem('_ic_selection_token', handshakeData.selection_token);
        localStorage.setItem('_ic_handshake', JSON.stringify(handshakeData));
      }

      if (handshakeData.companies.length === 1) {
        await this.selectCompany(handshakeData.companies[0].company_id);
      } else {
        this.router.navigate(['/select-company']);
      }
    } catch (err) {
      console.error('[AuthService] ❌ T1 failed:', err);
      throw err;
    } finally {
      this.isLoading.set(false);
      console.groupEnd();
    }
  }

  /**
   * Step 2: Selection (Target Company -> Scoped JWT)
   */
  public async selectCompany(companyId: string, redirectTo: string = '/dashboard'): Promise<void> {
    console.group('Auth selectCompany (T2)');
    const t1 = this.handshake()?.selection_token || (this.isBrowser ? sessionStorage.getItem('_ic_selection_token') : null);

    if (!t1) {
      this.logout();
      throw new Error('Selection token missing');
    }

    this.isLoading.set(true);
    try {
      const resp = await lastValueFrom(
        this.http.post<ApiResponse<AuthSession>>(`${this.apiUrl}/auth/select-company`,
          { company_id: companyId },
          { headers: { 'Authorization': `Bearer ${t1}` } }
        )
      );

      const sessionData = resp.data;
      if (!sessionData) throw new Error('Selection failed: empty response');

      // Adapt multi-service naming conventions
      if (!sessionData.roles && (sessionData as any).role_names) {
        sessionData.roles = (sessionData as any).role_names;
      }

      // ✅ Entitlements & Normalization
      const rawScopes = (sessionData as any).scopes || [];
      if (rawScopes.length > 0) {
        sessionData.permissions = rawScopes;
        console.log('[AuthService] 🛡️ Scopes detected. Setting as primary permissions:', rawScopes);
      }

      // ✅ ENRIQUECER SESIÓN con company_name desde la lista persistida (T1 → T2 bridge)
      const companies = this._companies();
      const matched = companies.find(c => String(c.company_id) === String(companyId));
      if (matched) {
        (sessionData as any).company_name = matched.company_name;
      }

      this.setSession(sessionData);
      if (redirectTo) {
        this.router.navigate([redirectTo]);
      }
    } catch (err) {
      console.error('[AuthService] ❌ T2 failed:', err);
      throw err;
    } finally {
      this.isLoading.set(false);
      console.groupEnd();
    }
  }

  public logout(): void {
    console.log('[AuthService] 🔒 Logout sequence initiated.');
    this.session.set(null);
    this.handshake.set(null);
    this._companies.set([]);
    this.authStep.set('login');
    if (this.isBrowser) {
      const keys = ['auth_session', '_ic_auth_ctx', '_ic_handshake', '_ic_selection_token', '_ic_companies'];
      keys.forEach(k => localStorage.removeItem(k));
      sessionStorage.clear();
    }
    this.router.navigate(['/login']);
  }

  /**
   * SILENT REFRESH (RTR)
   * Calls the backend to rotate the session tokens.
   */
  public refreshToken(): Observable<ApiResponse<AuthSession>> {
    const session = this.session();
    let refreshToken = session?.refresh_token;

    if (!refreshToken && this.isBrowser) {
      const stored = localStorage.getItem('_ic_auth_ctx');
      if (stored) {
        try {
          refreshToken = JSON.parse(stored).refresh_token;
        } catch { }
      }
    }

    if (!refreshToken) {
      return of({ status: 'error', message: 'No refresh token available' } as any);
    }

    return this.http.post<ApiResponse<AuthSession>>(`${this.apiUrl}/auth/refresh`, {
      refresh_token: refreshToken
    });
  }

  /**
   * Fetches a delegation selection token for mobile pairing.
   */
  public async getDelegateToken(): Promise<AuthHandshake> {
    // The QR needs the API server URL that the mobile device can reach.
    // - Production: environment.apiUrl already points to the public domain (e.g. https://api.interno.com)
    // - Dev local: environment.apiUrl is http://localhost:8000, but mobile can't reach "localhost",
    //   so we swap it for the actual hostname the browser is using (e.g. 192.168.1.146)
    let serverUrl = environment.apiUrl; // e.g. http://localhost:8000 or https://api.interno.com
    if (serverUrl.includes('localhost')) {
      const hostname = window.location.hostname;
      serverUrl = serverUrl.replace('localhost', hostname);
    }

    const resp = await lastValueFrom(
      this.http.get<ApiResponse<AuthHandshake>>(`${this.apiUrl}/auth/delegate-selection`, {
        params: { api_url: serverUrl }
      })
    );
    if (!resp.data) throw new Error('Failed to fetch delegation token');
    return resp.data;
  }

  /**
   * Kiosk / Collaborator Login (RFID or PIN)
   * Calls the auth_service collaborator proxy endpoint, which validates against hr_service.
   * Stores the collaborator JWT directly — no company selection step needed (company is embedded in token).
   */
  public async collaboratorLogin(params: {
    rfid_tag?: string;
    internal_id?: string;
    pin_code?: string;
    company_id?: string;
  }, redirectTo: string = '/dashboard'): Promise<void> {
    console.group('Auth collaboratorLogin (Kiosk)');
    this.isLoading.set(true);
    try {
      // Map frontend params to backend CollaboratorLoginRequest schema
      const payload = {
        identity_identifier: params.rfid_tag || params.pin_code,
        access_method: params.rfid_tag ? 'RFID_SCAN' : 'PIN_PAD',
        internal_id: params.internal_id,
        terminal_id: 'WEB_LOGIN',
        company_id: params.company_id
      };

      const resp = await lastValueFrom(
        this.http.post<any>(
          `${this.apiUrl}/auth/collaborator-login`,
          payload
        )
      );

      // result is polymorphic (comes from CollaboratorLoginResponse)
      const data = resp.data || resp; // API interceptor might have already unwrapped it

      // CASE A: Handshake (Multiple companies found)
      if (data.selection_token && data.companies) {
        this.handshake.set(data);
        this._companies.set(data.companies);
        this.authStep.set('handshake');

        if (this.isBrowser) {
          sessionStorage.setItem('_ic_selection_token', data.selection_token);
          localStorage.setItem('_ic_companies', JSON.stringify(data.companies));
        }

        this.router.navigate(['/select-company']);
        return;
      }

      // CASE B: Direct Login (1 company found)
      if (data.access_token) {
        const backendScopes: string[] = data.scopes || data.permissions || [];
        const session: AuthSession = {
          access_token: data.access_token,
          refresh_token: null as any,
          user_id: data.user_id || (null as any),
          company_id: data.company_id || params.company_id || (data as any).cid,
          roles: data.roles || ['collaborator'],
          permissions: backendScopes,
          readonly: data.readonly ?? false,
          status: data.status,
          user: {
            email: '',
            name: data.user_full_name || 'Colaborador',
            full_name: data.user_full_name || 'Colaborador',
          } as any,
        };

        this.setSession(session);
        if (redirectTo) {
          this.router.navigate([redirectTo]);
        }
      }
    } catch (err) {
      console.error('[AuthService] ❌ Kiosk login failed:', err);
      throw err;
    } finally {
      this.isLoading.set(false);
      console.groupEnd();
    }
  }


  /**
   * Optimistic restoration from localStorage to avoid UI flickering
   */
  private restoreFromStorage(): void {
    const savedSession = localStorage.getItem('auth_session');
    if (savedSession) {
      try {
        const parsedData = JSON.parse(savedSession);
        this.session.set(parsedData);
        this.authStep.set('verified');
      } catch { }
    }

    const savedCompanies = localStorage.getItem('_ic_companies');
    if (savedCompanies) {
      try {
        this._companies.set(JSON.parse(savedCompanies));
      } catch { }
    }
  }

  /**
   * Active Zero-Trust Restoration
   * Validates the token and company context with the backend.
   * Used by APP_INITIALIZER to block app startup.
   */
  public async restoreSession(): Promise<boolean> {
    if (!this.isBrowser) return true;

    const savedSession = localStorage.getItem('auth_session');
    if (!savedSession) {
      this.logout();
      return true;
    }

    try {
      const resp = await lastValueFrom(
        this.http.get<ApiResponse<AuthSession>>(`${this.apiUrl}/auth/me`)
      );

      if (resp.status === 'success' && resp.data) {
        this.setSession(resp.data);
        return true;
      } else {
        throw new Error('Server rejected session validation');
      }
    } catch (err) {
      console.error('[AuthService] 🛡️ Zero-Trust Validation Failed:', err);
      this.logout();
      return true; // We return true to allow app to start, but redir to login is handled by logout/signals
    }
  }

}
