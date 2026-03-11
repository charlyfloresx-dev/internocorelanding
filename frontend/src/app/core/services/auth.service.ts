import { Injectable, signal, inject, computed, effect } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { lastValueFrom, Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User, SessionContext, UserCompanyAccess, ApiResponse, LoginResponse, SelectCompanyResponse, RegisterCompanyPayload, RegisterResponse, CompleteRegistrationPayload, ForgotPasswordPayload, ResetPasswordPayload } from '@models/api.types';
import { NavigationService } from './navigation.service';
import { tap, catchError } from 'rxjs/operators';
import { SystemHealthService } from './system-health.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private apiUrl = environment.authUrl;
  private http = inject(HttpClient);
  private router = inject(Router);
  private navService = inject(NavigationService);
  private health = inject(SystemHealthService);

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
        await lastValueFrom(this.http.get(`${this.apiUrl}/auth/me`));
        this.health.updateStatus('auth', true);

        this.authStep.set('authenticated');
        return true;
      }
    } catch (e) {
      console.warn('[AuthService] Validación de sesión fallida:', e);
    }
    // No marcamos auth: false aquí porque puede ser solo expiración de token, no caída del servicio
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
    console.group('Auth Handshake Trace');
    this.isLoading.set(true);
    return this.http.post<ApiResponse<LoginResponse>>(`${this.apiUrl}/auth/login`, credentials)
      .pipe(
        tap({
          next: (response: ApiResponse<LoginResponse>) => {
            this.health.updateStatus('auth', true);
            // CORRECCIÓN: La respuesta viene envuelta en ApiResponse { status, data, ... }
            const data = response.data;

            if (!data || !data.selection_token) {
              console.error('[AuthService] ❌ selection_token ausente. Estructura:', response);
              this.isLoading.set(false);
              return;
            }

            console.log('[AuthService] 📥 Respuesta recibida:', { has_token: !!data.selection_token, companies: data.companies?.length });
            console.log(`%c[AuthService] 1. Status del selection_token: ${data.selection_token ? 'RECIBIDO' : 'AUSENTE'}`, 'color: #22d3ee');

            // === GUARDAR PRIMERO: T1 TOKEN ===
            sessionStorage.setItem('selection_token', data.selection_token);
            this.selectionToken.set(data.selection_token);

            // === USER PROFILE ===
            // Per Swagger v2.1.0, user_id is not provided at this stage.
            // A partial profile is created. The full profile will be available after T2.
            this.currentUser.set({
              id: 'temp-user', // ID will be confirmed after selectCompany
              email: credentials.email || '',
              firstName: credentials.email?.split('@')[0] || 'User',
              lastName: '',
              avatar: `https://ui-avatars.com/api/?name=${credentials.email?.charAt(0)}`,
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
                group_id: c.group_id,
                group_name: c.group_name,
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

            // === STATE TRANSITION & AUTO-SELECT LOGIC ===
            if (formattedAccesses.length === 1) {
              console.log('[AuthService] 🚀 Una sola empresa detectada. Iniciando selección automática...');
              this.selectCompany(formattedAccesses[0].company.id);
            } else {
              this.authStep.set('handshake');
              this.isLoading.set(false);
              console.log('[AuthService] ✅ Login exitoso. Estado = "handshake". Selector debe renderizarse en LoginComponent.');
            }
            console.log('[AuthService] selection_token guardado:', sessionStorage.getItem('selection_token') ? '✅ SÍ' : '❌ NO');
            console.log('[AuthService] availableAccesses:', this.availableAccesses().length, 'empresas');
          },
          error: (err) => {
            console.error('Login Failed:', err);
            if (err.status === 0) this.health.updateStatus('auth', false);
            console.groupEnd(); // Cerrar grupo en caso de error
            this.isLoading.set(false);
          }
        })
      );
  }

  /**
   * Registra una nueva empresa y su usuario administrador, y luego inicia sesión directamente.
   * Corresponde a: POST /v2/public/register-company
   */
  registerCompany(payload: RegisterCompanyPayload) {
    this.isLoading.set(true);
    return this.http.post<ApiResponse<RegisterResponse>>(
      `${this.apiUrl}/v2/public/register-company`,
      payload
    ).pipe(
      tap({
        next: (response: ApiResponse<RegisterResponse>) => {
          this.health.updateStatus('auth', true);
          const data = response.data;

          if (!data || !data.access_token || !data.company_id || !data.user_id) {
            console.error('[AuthService] ❌ Datos de registro incompletos:', response);
            this.isLoading.set(false);
            throw new Error('Datos de registro incompletos.');
          }

          const permissionNames = data.role.permissions.map((p: any) => p.name || p);

          // 1. Establecer el usuario actual
          this.currentUser.set({
            id: data.user_id,
            email: payload.admin_email, // Usar el email proporcionado en el registro
            firstName: payload.admin_email.split('@')[0] || 'Admin',
            lastName: '',
            avatar: `https://ui-avatars.com/api/?name=${data.user_id}`,
            status: 'Active'
          });

          // 2. Establecer los accesos disponibles (solo la empresa recién creada)
          const newCompanyAccess: UserCompanyAccess = {
            company: { ...data.company, id: data.company_id }, // Asegurar que el ID de la compañía coincida
            role: data.role
          };
          this.availableAccesses.set([newCompanyAccess]);

          // 3. Establecer el contexto de la sesión
          const context: SessionContext = {
            access_token: data.access_token,
            companyId: data.company_id,
            role: data.role,
            permissions: permissionNames,
            group_id: data.company.group_id || '',
            group_name: data.company.group_name || ''
          };
          this.currentContext.set(context);

          // 4. Persistir la sesión
          localStorage.setItem('interno_auth_ctx', JSON.stringify(context));
          localStorage.setItem('interno_auth_user', JSON.stringify(this.currentUser()));
          localStorage.setItem('interno_auth_accesses', JSON.stringify(this.availableAccesses()));

          // 5. Transición de estado
          this.authStep.set('authenticated');
          this.isLoading.set(false);
          this.navService.generateMenu(permissionNames); // Generar menú con los permisos del nuevo rol
        },
        error: (err: HttpErrorResponse) => {
          console.error('Register Company Failed:', err);
          if (err.status === 0) this.health.updateStatus('auth', false);
          this.isLoading.set(false);
          throw err; // Re-throw para que el componente pueda manejarlo
        }
      })
    );
  }

  /**
   * Completa el registro de un usuario invitado y realiza auto-login.
   * Corresponde a: POST /v2/public/complete-registration
   */
  completeRegistration(payload: CompleteRegistrationPayload) {
    this.isLoading.set(true);
    // Asumimos que el backend devuelve el mismo tipo de respuesta que registerCompany para el auto-login
    return this.http.post<ApiResponse<RegisterResponse>>(
      `${this.apiUrl}/v2/public/complete-registration`,
      payload
    ).pipe(
      tap({
        next: (response: ApiResponse<RegisterResponse>) => {
          this.health.updateStatus('auth', true);
          const data = response.data;

          if (!data || !data.access_token || !data.company_id || !data.user_id) {
            console.error('[AuthService] ❌ Datos de registro (invitación) incompletos:', response);
            this.isLoading.set(false);
            throw new Error('Datos de registro (invitación) incompletos.');
          }

          const permissionNames = data.role.permissions.map((p: any) => p.name || p);

          // 1. Establecer el usuario actual
          this.currentUser.set({
            id: data.user_id,
            email: 'invited.user@interno.com', // El backend debería proveer el email
            firstName: payload.full_name.split(' ')[0],
            lastName: payload.full_name.split(' ').slice(1).join(' '),
            avatar: `https://ui-avatars.com/api/?name=${data.user_id}`,
            status: 'Active'
          });

          // 2. Establecer los accesos disponibles
          const newCompanyAccess: UserCompanyAccess = {
            company: { ...data.company, id: data.company_id },
            role: data.role
          };
          this.availableAccesses.set([newCompanyAccess]);

          // 3. Establecer el contexto de la sesión
          const context: SessionContext = {
            access_token: data.access_token,
            companyId: data.company_id,
            role: data.role,
            permissions: permissionNames,
            group_id: data.company.group_id || '',
            group_name: data.company.group_name || ''
          };
          this.currentContext.set(context);

          // 4. Persistir la sesión
          localStorage.setItem('interno_auth_ctx', JSON.stringify(context));
          localStorage.setItem('interno_auth_user', JSON.stringify(this.currentUser()));
          localStorage.setItem('interno_auth_accesses', JSON.stringify(this.availableAccesses()));

          // 5. Transición de estado
          this.authStep.set('authenticated');
          this.isLoading.set(false);
          this.navService.generateMenu(permissionNames);
        },
        error: (err: HttpErrorResponse) => {
          console.error('Complete Registration Failed:', err);
          if (err.status === 0) this.health.updateStatus('auth', false);
          this.isLoading.set(false);
          throw err;
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
    console.log(`%c[AuthService] 2. Headers enviados en T2: Authorization: Bearer ${selectionToken ? '***' : 'null'}`, 'color: #22d3ee');

    // Per Swagger v2.1.0, the select-company endpoint is secured with OAuth2PasswordBearer.
    // The selection_token must be sent as a Bearer token.
    const headers = new HttpHeaders({
      'Authorization': `Bearer ${selectionToken}`,
      'Content-Type': 'application/json'
    });

    this.http.post<ApiResponse<SelectCompanyResponse>>(
      `${this.apiUrl}/auth/select-company`,
      { company_id: companyId },
      { headers }
    ).pipe(
      catchError(err => {
        if (err.status === 401) {
          console.warn('[AuthService] ⚠️ 401 Unauthorized en selectCompany. Limpiando sesión.');
          console.groupEnd();
          // 401 significa que el servicio responde, así que auth está true
          localStorage.clear();
          this.router.navigate(['/login']);
        }
        throw err;
      })
    ).subscribe({
      next: (response: ApiResponse<SelectCompanyResponse>) => {
        this.health.updateStatus('auth', true);
        // CORRECCIÓN: La respuesta viene envuelta en ApiResponse { status, data, ... }
        const data = response.data as any; // Cast para acceder a propiedades dinámicas (scopes)
        const access = this.availableAccesses().find(a => String(a.company.id) === String(companyId));

        console.log('[AuthService] 📊 Buscando empresa:', { companyId, foundAccess: !!access });
        if (access) {
          console.log('[AuthService] 📊 Company data:', { id: access.company.id, name: access.company.name, is_new: access.company.is_new });
        }

        // === PERMISSIONS LOGIC ===
        // Prioridad: Scopes (Backend v1.1) > Roles (Legacy) > Local Permissions
        let effectivePermissions: string[] = [];
        if (data?.scopes && data.scopes.length > 0) {
          effectivePermissions = data.scopes;
        } else if (data?.roles) {
          effectivePermissions = data.roles.map((p: any) => p.name || p);
        } else if (access?.role?.permissions) {
          effectivePermissions = access.role.permissions.map((p: any) => p.name);
        }
        console.log(`%c[AuthService] 3. Confirmación de JWT final: ${data.access_token ? 'RECIBIDO' : 'FALLIDO'}`, 'color: #22d3ee');

        console.log('[AuthService] 🔐 Permisos efectivos calculados (Scopes/Roles):', effectivePermissions);

        // === T2 TOKEN: Final Access Token ===
        const context: SessionContext = {
          access_token: data.access_token,
          companyId: data.company_id, // Usar ID confirmado por backend
          role: access?.role || { id: '0', name: 'user', description: '', permissions: [] },
          permissions: effectivePermissions,
          group_id: access?.company.group_id || '',
          group_name: access?.company.group_name || ''
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
          console.groupEnd();
        }, 150);
      },
      error: (err) => {
        console.error('[AuthService] ❌ select-company FAILED', err);
        if (err.status === 0) this.health.updateStatus('auth', false);
        this.isLoading.set(false);
        console.groupEnd();

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
   * Notifies the backend that the initial setup for a company is complete.
   * Corresponds to: PATCH /auth/complete-onboarding
   */
  completeOnboarding(): Observable<ApiResponse<void>> {
    return this.http.patch<ApiResponse<void>>(`${this.apiUrl}/auth/complete-onboarding`, {});
  }

  /**
   * Updates the 'is_new' status for the currently active company in the local state.
   * This should be called only after a successful onboarding completion.
   * @param isNew The new status to set.
   */
  updateCompanyIsNewStatus(isNew: boolean) {
    const companyId = this.selectedCompanyId();
    if (!companyId) {
      console.warn('[AuthService] Cannot update is_new status without a selected company.');
      return;
    }

    this.availableAccesses.update(accesses => {
      return accesses.map(access => {
        if (String(access.company.id) === String(companyId)) {
          // Create new objects for immutability to ensure signal propagation
          const updatedCompany = { ...access.company, is_new: isNew };
          return { ...access, company: updatedCompany };
        }
        return access;
      });
    });

    // Also update the current context if it's holding onto a stale company object
    const access = this.availableAccesses().find(a => String(a.company.id) === String(companyId));
    if (this.currentContext() && access) {
      this.currentContext.update(ctx => ctx ? ({ ...ctx, role: access.role }) : null);
    }

    console.log(`[AuthService] 🔄 Local state for company ${companyId} updated: is_new = ${isNew}`);
  }

  /**
   * Solicita el reseteo de contraseña para un email.
   * Corresponde a: POST /v1/auth/forgot-password
   */
  forgotPassword(payload: ForgotPasswordPayload): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>(`${this.apiUrl}/auth/forgot-password`, payload);
  }

  /**
   * Establece una nueva contraseña usando un token.
   * Corresponde a: POST /v1/auth/reset-password
   */
  resetPassword(payload: ResetPasswordPayload): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>(`${this.apiUrl}/auth/reset-password`, payload);
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
    if (!currentToken) {
      console.error('[AuthService] ❌ CRITICAL: No selection_token found in sessionStorage during switchCompany. Logging out.');
      this.logout();
      return;
    }
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