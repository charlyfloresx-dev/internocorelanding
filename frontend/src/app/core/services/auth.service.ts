import { Injectable, signal, inject, computed, effect } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { User, SessionContext, UserCompanyAccess, ApiResponse, LoginResponse, SelectCompanyResponse } from '@models/api.types';
import { NavigationService } from './navigation.service';
import { tap, catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = 'http://localhost:8001/api';
  private http = inject(HttpClient);
  private router = inject(Router);
  private navService = inject(NavigationService);

  // === SIGNALS ===
  currentUser = signal<User | null>(null);
  availableAccesses = signal<UserCompanyAccess[]>([]);
  currentContext = signal<SessionContext | null>(null);
  authStep = signal<'guest' | 'handshake' | 'authenticated'>('guest');
  isLoading = signal<boolean>(false);

  // Temporal storage for selection_token (T1)
  selectionToken = signal<string | null>(null);

  // === COMPUTED SIGNALS ===
  isAuthenticated = computed(() => this.authStep() === 'authenticated');
  selectedCompanyId = computed(() => this.currentContext()?.companyId || null);
  activeRole = computed(() => this.currentContext()?.role || null);
  activeCompany = computed(() => {
    const ctx = this.currentContext();
    return this.availableAccesses().find(a => String(a.company.id) === String(ctx?.companyId))?.company;
  });

  // Alias para compatibilidad con interceptores
  token = computed(() => this.currentContext()?.access_token || null);
  activeCompanyId = computed(() => this.currentContext()?.companyId || null);
  isNewUser = computed(() => this.availableAccesses().some(a => a.company.is_new));

  constructor() {
    // The effect was removed to favor imperative persistence inside login/selectCompany methods,
    // preventing race conditions with the Router and AuthGuard.
    // Session restoration is now handled by the AuthGuard on navigation.
  }

  async restoreSessionWithValidation(): Promise<boolean> {
    try {
      const savedCtx = localStorage.getItem('interno_auth_ctx');
      const savedUser = localStorage.getItem('interno_auth_user');
      const savedAccesses = localStorage.getItem('interno_auth_accesses');

      if (savedCtx && savedUser) {
        this.currentContext.set(JSON.parse(savedCtx));
        this.currentUser.set(JSON.parse(savedUser));
        this.availableAccesses.set(JSON.parse(savedAccesses || '[]'));

        // Zero Trust: Validar token con backend
        await lastValueFrom(this.http.get(`${this.apiUrl}/v1/auth/me`));

        this.authStep.set('authenticated');
        return true;
      }
    } catch (e) {
      console.warn('[AuthService] Validación de sesión fallida:', e);
    }
    this.logoutQuiet();
    return false;
  }

  private restoreSession() {
    try {
      const savedCtx = localStorage.getItem('interno_auth_ctx');
      const savedUser = localStorage.getItem('interno_auth_user');
      const savedAccesses = localStorage.getItem('interno_auth_accesses');

      // Si hay datos guardados, restaurar directamente sin validar
      if (savedCtx && savedUser) {
        this.currentContext.set(JSON.parse(savedCtx));
        this.currentUser.set(JSON.parse(savedUser));
        this.availableAccesses.set(JSON.parse(savedAccesses || '[]'));
        this.authStep.set('authenticated');
        console.log('[AuthService] ✅ Sesión restaurada desde localStorage.');
      } else {
        // Sin datos guardados = login nuevo
        this.authStep.set('guest');
      }
    } catch (e) {
      console.error('[AuthService] Error al restaurar sesión:', e);
      this.logout();
    }
  }

  /**
   * PASO 1: Login - Solo recibe selection_token y companies, sin redirigir
   * No marca como 'authenticated', solo como 'handshake'
   */
  login(credentials: { email?: string; password?: string }) {
    this.isLoading.set(true);
    return this.http.post<ApiResponse<LoginResponse>>(`${this.apiUrl}/v1/auth/login`, credentials)
      .pipe(
        tap({
          next: (response: ApiResponse<LoginResponse>) => {
            // CORRECCIÓN: La respuesta viene envuelta en ApiResponse { status, data, ... }
            const data = response.data;

            if (!data || !data.selection_token) {
              console.error('[AuthService] ❌ selection_token ausente. Estructura:', response);
              this.isLoading.set(false);
              return;
            }

            console.log('[AuthService] 📥 Respuesta recibida:', { has_token: !!data.selection_token, companies: data.companies?.length });

            // === GUARDAR PRIMERO: T1 TOKEN ===
            sessionStorage.setItem('selection_token', data.selection_token);
            this.selectionToken.set(data.selection_token);

            // === USER PROFILE ===
            // Backend v2.1 devuelve user_id
            this.currentUser.set({
              id: data.user_id,
              email: credentials.email || '',
              firstName: credentials.email?.split('@')[0] || 'User',
              lastName: '',
              avatar: `https://ui-avatars.com/api/?name=${data.user_id}`,
              status: 'Active'
            });

            // === AVAILABLE ACCESSES ===
            // Backend v2.1 envía companies como array de CompanySelection
            const formattedAccesses: UserCompanyAccess[] = (data.companies || []).map((c: any) => ({
              company: {
                id: c.company_id,
                name: c.company_name,
                logo: c.logo,
                is_new: c.is_new || false, // Normalized to snake_case
                registrationNumber: '',
                contactEmail: '',
                status: 'Active',
                plan: 'Standard'
              },
              role: {
                id: 'role-placeholder',
                name: (c.role_names && c.role_names[0]) || 'viewer',
                description: '',
                permissions: []
              }
            }));

            this.availableAccesses.set(formattedAccesses);

            // === STATE TRANSITION ===
            // Cambiar a 'handshake': Usuario autenticado pero sin acceso a dashboard aún
            // El LoginComponent renderizará tenant-selection cuando detecte authStep === 'handshake'
            this.authStep.set('handshake');
            this.isLoading.set(false);

            console.log('[AuthService] ✅ Login exitoso. Estado = "handshake". Selector debe renderizarse en LoginComponent.');
            console.log('[AuthService] selection_token guardado:', sessionStorage.getItem('selection_token') ? '✅ SÍ' : '❌ NO');
            console.log('[AuthService] availableAccesses:', this.availableAccesses().length, 'empresas');
          },
          error: (err) => {
            console.error('Login Failed:', err);
            this.isLoading.set(false);
          }
        })
      );
  }

  /**
   * PASO 2: Select Company - Recibe access_token y marca como 'authenticated'
   * Redirige a /dashboard o /onboarding según isNew
   */
  selectCompany(companyId: string) {
    console.log('[CACHE-CHECK] v2-' + Date.now());
    this.isLoading.set(true);
    const selectionToken = this.selectionToken() || sessionStorage.getItem('selection_token');

    if (!selectionToken) {
      console.error('[AuthService] ❌ No selection_token available');
      this.logout();
      return;
    }

    console.log('[AuthService] 📤 Enviando select-company request', { companyId, hasToken: !!selectionToken });

    // === ENVIAR SELECTION TOKEN EN HEADER ===
    const headers = {
      'Authorization': `Bearer ${selectionToken}`,
      'X-Selection-Token': selectionToken,
      'X-Company-Id': companyId
    };

    this.http.post<ApiResponse<SelectCompanyResponse>>(
      `${this.apiUrl}/v1/auth/select-company`,
      { company_id: companyId },
      { headers }
    ).pipe(
      catchError(err => {
        if (err.status === 401) {
          console.warn('[AuthService] ⚠️ 401 Unauthorized en selectCompany. Limpiando sesión.');
          localStorage.clear();
          this.router.navigate(['/login']);
        }
        throw err;
      })
    ).subscribe({
      next: (response: ApiResponse<SelectCompanyResponse>) => {
        // CORRECCIÓN: La respuesta viene envuelta en ApiResponse { status, data, ... }
        const data = response.data as any; // Cast para acceder a propiedades dinámicas (scopes)
        const access = this.availableAccesses().find(a => String(a.company.id) === String(companyId));

        console.log('[AuthService] 📊 Buscando empresa:', { companyId, foundAccess: !!access });
        if (access) {
          console.log('[AuthService] 📊 Company data:', { id: access.company.id, name: access.company.name, is_new: access.company.is_new });
        }

        // === PERMISSIONS LOGIC ===
        // Prioridad: Scopes (Backend v1.1) > Roles (Legacy) > Local Permissions
        const scopes = data?.scopes || [];
        const effectivePermissions = scopes.length > 0 ? scopes : (data?.roles || access?.role.permissions.map(p => p.name) || []);

        console.log('[AuthService] 🔐 Permisos efectivos calculados (Scopes/Roles):', effectivePermissions);

        // === T2 TOKEN: Final Access Token ===
        const context: SessionContext = {
          access_token: data.access_token,
          companyId: data.company_id, // Usar ID confirmado por backend
          role: access?.role || { id: '0', name: 'user', description: '', permissions: [] },
          permissions: effectivePermissions
        };

        // 1. FORCE SYNC SAVE: Guardar inmediatamente en disco para evitar Race Condition con AuthGuard
        // Cumplimiento de Regla de Oro: Claves explícitas para AuthGuard
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('company_id', data.company_id);

        localStorage.setItem('interno_auth_ctx', JSON.stringify(context));
        if (this.currentUser()) {
          localStorage.setItem('interno_auth_user', JSON.stringify(this.currentUser()));
        }
        localStorage.setItem('interno_auth_accesses', JSON.stringify(this.availableAccesses()));

        // 3. UPDATE SIGNALS & STATE TRANSITION
        this.currentContext.set(context);
        // Ahora sí: usuario completamente autenticado
        this.authStep.set('authenticated');
        this.isLoading.set(false);
        
        // 4. UPDATE NAVIGATION: Regenerar menú con los nuevos permisos
        console.log('[AuthService] 🔄 Invocando regeneración de menú...');
        this.navService.generateMenu(effectivePermissions);

        console.log('[AuthService] ✅ Empresa seleccionada. Estado en "authenticated".', { companyId });

        // 4. NAVIGATION: Redirigir forzosamente con delay para digest cycle
        // Basarse en isNew del backend para decidir ruta
        const isNew = access?.company.is_new;
        console.log('[AuthService] 🔍 is_new value:', isNew);

        // Usar setTimeout (150ms) para asegurar que los Signals se propaguen y localStorage esté listo
        setTimeout(() => {
          // HARD RESET: Asegurar estado autenticado justo antes de navegar
          this.authStep.set('authenticated');

          if (isNew) {
            console.log('[AuthService] 🚀 Empresa nueva. Navegando a /setup-wizard');
            this.router.navigate(['/setup-wizard']);
          } else {
            console.log('[AuthService] 🚀 Empresa existente. Navegando a /dashboard');
            this.router.navigate(['/dashboard']);
          }
        }, 150);
      },
      error: (err) => {
        console.error('[AuthService] ❌ select-company FAILED', err);
        this.isLoading.set(false);

        // === ERROR HANDLING ===
        if (err.status === 401) {
          console.warn('[AuthService] ⚠️ 401 Unauthorized. Token expirado. Limpiando sesión.');
          localStorage.clear();
          this.router.navigate(['/login']);
        }
      }
    });
  }

  /**
   * Vuelve al estado 'handshake' para cambiar de empresa
   * - Limpia el access_token (currentContext) de la empresa anterior
   * - Mantiene el selection_token (T1) en sessionStorage para seleccionar otra empresa
   * - Mantiene la lista de empresas disponibles para que el selector funcione
   */
  switchCompany() {
    console.log('[AuthService] 🔄 Cambiando de empresa...');

    // === LIMPIAR CONTEXTO DE ACCESO (T2) ===
    // Ya no estamos autenticados en ninguna empresa específica
    this.currentContext.set(null);
    localStorage.removeItem('interno_auth_ctx');
    localStorage.removeItem('access_token');
    localStorage.removeItem('company_id');

    // === MANTENER SELECTION TOKEN ===
    // El selection_token sigue válido y está en sessionStorage
    // La corrección en `selectCompany` asegura que este token no se borre.
    const currentToken = sessionStorage.getItem('selection_token');
    console.log('[AuthService] selection_token persistido:', currentToken ? '✅ SÍ' : '❌ NO');

    // === MANTENER EMPRESAS DISPONIBLES ===
    // availableAccesses sigue poblado para que el selector funcione

    // === STATE TRANSITION ===
    this.authStep.set('handshake');
    console.log('[AuthService] ✅ Estado = "handshake". Selector debe aparecer en LoginComponent.');

    // === NAVEGACIÓN ===
    // Navegar a /login dispara el LoginComponent que detectará authStep === 'handshake'
    this.router.navigate(['/login']);
  }

  /**
   * Cierra sesión silenciosamente (sin redirigir)
   * Usado en APP_INITIALIZER cuando no hay token
   */
  logoutQuiet() {
    localStorage.clear();
    sessionStorage.clear();
    this.authStep.set('guest');
    this.currentContext.set(null);
    this.currentUser.set(null);
    this.availableAccesses.set([]);
    this.selectionToken.set(null);
    console.log('[AuthService] 🔒 logoutQuiet: Sesión limpiada (sin redirigir)');
  }

  /**
   * Restaura sesión SOLO desde localStorage (sin peticiones HTTP)
   * Usado en APP_INITIALIZER para boot seguro
   */
  restoreSessionFromStorage() {
    try {
      const savedCtx = localStorage.getItem('interno_auth_ctx');
      const savedUser = localStorage.getItem('interno_auth_user');
      const savedAccesses = localStorage.getItem('interno_auth_accesses');

      if (savedCtx && savedUser) {
        this.currentContext.set(JSON.parse(savedCtx));
        this.currentUser.set(JSON.parse(savedUser));
        this.availableAccesses.set(JSON.parse(savedAccesses || '[]'));
        this.authStep.set('authenticated');
        console.log('[AuthService] ✅ restoreSessionFromStorage: Sesión restaurada desde localStorage');
      } else {
        console.warn('[AuthService] ⚠️ restoreSessionFromStorage: Sin datos guardados');
        this.logoutQuiet();
      }
    } catch (e) {
      console.error('[AuthService] ❌ restoreSessionFromStorage: Error al restaurar', e);
      this.logoutQuiet();
    }
  }

  /**
   * Cierra la sesión completamente
   */
  logout() {
    localStorage.clear();
    sessionStorage.clear();
    this.authStep.set('guest');
    this.currentContext.set(null);
    this.currentUser.set(null);
    this.availableAccesses.set([]);
    this.selectionToken.set(null);
    this.router.navigate(['/login']);
  }
}