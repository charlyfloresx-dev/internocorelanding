# Sprint 2 — GOD MODE Angular: Plan de Implementación

> **Estado:** ✅ COMPLETADO — 2026-05-19 (Phase 115)  
> **Prerequisito:** Phase 113 completada (backend `/elevate` + `/security-logs` operativos)  
> **Implementado en:** ~2.5 horas

---

## Contexto

El backend del GOD MODE está 100% implementado y testeado. El frontend necesita 4 piezas que no existen aún:

| Pieza | Tipo | Ruta destino |
|---|---|---|
| `GodModeStore` | Signal Store (servicio) | `core/stores/god-mode.store.ts` |
| `god-mode.interceptor.ts` | HTTP Interceptor | `core/interceptors/` |
| `SystemControlComponent` | Standalone Component | `/admin/system-control` |
| Extensión `ForensicDashboardComponent` | Tab nuevo en componente existente | `/admin/audit` (ya existe) |

**Decisión arquitectónica:** El `AuditAlertsDashboard` NO es un componente nuevo — se implementa como un **tab de GOD MODE** dentro del `forensic-dashboard.component.ts` existente, que ya tiene el look & feel de audit logs con animaciones rojo/rose. Esto evita duplicar la lógica de polling y el estilo visual.

---

## Pieza 1 — `GodModeStore`

**Archivo:** `frontend/src/app/core/stores/god-mode.store.ts`

```typescript
import { Injectable, signal, computed } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class GodModeStore {
  // Estado en memoria — NO persiste en localStorage ni sessionStorage
  readonly token    = signal<string | null>(null);
  readonly jti      = signal<string | null>(null);
  readonly expiresAt = signal<number | null>(null);
  readonly attempts  = signal<number>(0);

  readonly isActive = computed(() => {
    const exp = this.expiresAt();
    return this.token() !== null && exp !== null && Date.now() < exp;
  });

  readonly isLocked = computed(() => this.attempts() >= 3);

  readonly secondsRemaining = computed(() => {
    const exp = this.expiresAt();
    if (!exp || !this.isActive()) return 0;
    return Math.max(0, Math.ceil((exp - Date.now()) / 1000));
  });

  activate(token: string, jti: string, expiresIn: number): void {
    this.token.set(token);
    this.jti.set(jti);
    this.expiresAt.set(Date.now() + expiresIn * 1000);
    this.attempts.set(0);
    // Auto-destruir al expirar — garantiza limpieza aunque el usuario no cierre el panel
    setTimeout(() => this.clear(), expiresIn * 1000);
  }

  recordFailedAttempt(): void {
    this.attempts.update(n => n + 1);
  }

  clear(): void {
    this.token.set(null);
    this.jti.set(null);
    this.expiresAt.set(null);
  }
}
```

**Criterios de aceptación:**
- `isActive` retorna `false` tras 300s aunque el componente no se destruya
- `isLocked` bloquea después de exactamente 3 intentos fallidos
- `clear()` elimina todos los valores — inspección de heap no debe mostrar el JWT

---

## Pieza 2 — `god-mode.interceptor.ts`

**Archivo:** `frontend/src/app/core/interceptors/god-mode.interceptor.ts`

```typescript
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { GodModeStore } from '../stores/god-mode.store';

export const godModeInterceptor: HttpInterceptorFn = (req, next) => {
  const store = inject(GodModeStore);

  // Solo inyecta si la sesión GOD MODE está activa
  if (!store.isActive() || !store.token()) {
    return next(req);
  }

  // Reemplaza el Bearer token normal por el token de emergencia
  const godReq = req.clone({
    setHeaders: { Authorization: `Bearer ${store.token()}` },
  });
  return next(godReq);
};
```

**Registro en `app.config.ts`:**
```typescript
// DEBE ir AL FINAL — no al principio.
// El multiTenantInterceptor SIEMPRE sobreescribe Authorization con el token de sesión.
// Si god-mode fuera primero, multi-tenant borraría el token de emergencia.
// Al ir último, god-mode tiene la última palabra sobre el header Authorization.
provideHttpClient(
  withInterceptors([
    multiTenantInterceptor,
    resilienceInterceptor,
    errorInterceptor,
    imageInterceptor,
    godModeInterceptor,   // ← siempre al final
  ])
)
```

**Nota:** El interceptor solo actúa cuando `store.isActive() === true`. El multi-tenant interceptor agrega `X-Company-ID` normalmente — el god-mode interceptor solo reemplaza el `Authorization`.

---

## Pieza 3 — `SystemControlComponent`

**Archivo:** `frontend/src/app/modules/admin/system-control.component.ts`

Componente standalone con dos secciones:

### 3A — Panel de activación (`GodModeTrigger`)

```
┌─────────────────────────────────────────────────────────┐
│  ⚡ CONSOLA DE EMERGENCIA                     [CRÍTICO] │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Esta acción eleva tus privilegios globalmente.         │
│  Cada uso queda registrado permanentemente.             │
│                                                         │
│  Clave maestra:  [••••••••••••••••••]  [👁]            │
│                                                         │
│  [ACTIVAR SESIÓN DE EMERGENCIA]  ← botón rojo           │
│                                                         │
│  ⚠ 3 intentos máximos por sesión                       │
│  ⚠ Sesión dura 5 minutos exactos                       │
└─────────────────────────────────────────────────────────┘
```

**Estado activo (banner):**
```
┌─────────────────────────────────────────────────────────┐
│  🔴 SESIÓN DE EMERGENCIA ACTIVA          4:47 restantes │
│  JTI: 6858faaf-407b...                                  │
│  Tienes acceso completo a todas las empresas            │
│                       [CERRAR SESIÓN DE EMERGENCIA]     │
└─────────────────────────────────────────────────────────┘
```

**Lógica clave del componente:**
```typescript
@Component({ standalone: true, ... })
export class SystemControlComponent implements OnDestroy {
  protected store = inject(GodModeStore);
  private http = inject(HttpClient);
  private authService = inject(AuthService);

  // JAMÁS persistir en un signal con localStorage
  masterKeyInput = signal('');
  isConfirming = signal(false);
  isLoading = signal(false);

  async activateGodMode() {
    if (this.store.isLocked()) return;

    // Confirmación doble
    if (!this.isConfirming()) {
      this.isConfirming.set(true);
      return;
    }
    this.isConfirming.set(false);
    this.isLoading.set(true);

    try {
      const response = await firstValueFrom(
        this.http.post<any>(`${environment.apiUrl}/api/v1/admin/elevate`, {}, {
          headers: { 'X-Admin-Master-Key': this.masterKeyInput() }
        })
      );
      this.store.activate(
        response.data.access_token,
        response.data.metadata.jti,
        response.data.expires_in,
      );
      // Limpiar el input inmediatamente — no queda en memoria del campo
      this.masterKeyInput.set('');
    } catch {
      this.store.recordFailedAttempt();
    } finally {
      this.isLoading.set(false);
    }
  }

  ngOnDestroy() {
    // NO llamar store.clear() aquí — la sesión debe sobrevivir la navegación
    // (el operador puede ir a /admin/users y volver sin perder la sesión)
    // La limpieza la hace el setTimeout() interno del store
  }
}
```

**Cuenta regresiva reactiva:**
```typescript
// Usando interval de RxJS o un signal con toObservable + takeUntilDestroyed
countdown = toSignal(
  interval(1000).pipe(
    map(() => this.store.secondsRemaining()),
    takeUntilDestroyed()
  ),
  { initialValue: 0 }
);
```

---

## Pieza 4 — Extensión de `ForensicDashboardComponent`

**Archivo:** `frontend/src/app/modules/admin/forensic-dashboard.component.ts` *(modificar existente)*

Agregar una nueva pestaña **"Alertas de Seguridad"** que consume `GET /api/v1/admin/security-logs`.

```typescript
// Nuevo signal en el componente existente
securityEvents = signal<SecurityEvent[]>([]);
activeTab = signal<'audit' | 'security'>('audit');

// Nuevo método de carga
async loadSecurityLogs() {
  const res = await firstValueFrom(
    this.http.get<any>(`${environment.apiUrl}/api/v1/admin/security-logs?limit=50`)
  );
  this.securityEvents.set(res.data ?? []);
}

isRecentAlert(event: SecurityEvent): boolean {
  const ts = new Date(event.timestamp).getTime();
  return Date.now() - ts < 24 * 60 * 60 * 1000; // < 24h → fila roja
}
```

**Vista de la tabla de alertas:**
```html
<!-- Fila de alerta — rojo parpadeante si < 24h -->
<div
  class="rounded-2xl p-6 border"
  [class.border-red-300]="isRecentAlert(ev)"
  [class.animate-pulse]="isRecentAlert(ev)"
  [class.bg-red-50]="isRecentAlert(ev)"
>
  <div class="flex justify-between items-center">
    <span class="font-black text-red-700 uppercase text-xs tracking-widest">
      🔴 {{ ev.message }}
    </span>
    <span class="text-xs font-mono text-slate-400">{{ ev.timestamp | date:'short' }}</span>
  </div>
  <div class="mt-2 grid grid-cols-3 gap-4 text-xs font-mono text-slate-600">
    <span>IP: {{ ev.ip_address }}</span>
    <span>JTI: {{ ev.metadata?.jti | slice:0:8 }}...</span>
    <span>UA: {{ ev.user_agent | slice:0:40 }}...</span>
  </div>
</div>
```

---

## Pieza 5 — Routing

**Archivo:** `frontend/src/app/app.routes.ts` *(modificar existente)*

```typescript
// Dentro del children[] del parent 'admin':
{
  path: 'system-control',
  loadComponent: () =>
    import('./modules/admin/system-control.component')
      .then(m => m.SystemControlComponent),
  canActivate: [permissionGuard],
  data: { requiredPermission: 'admin.user.manage' },
},
```

---

## Orden de Implementación

```
1. GodModeStore          (~20 min) — sin dependencias, se puede testear aislado
2. god-mode.interceptor  (~15 min) — depende de GodModeStore
3. Registro en app.config.ts (~5 min)
4. SystemControlComponent (~60 min) — depende de store + interceptor
5. Extensión ForensicDashboard (~40 min) — depende de security-logs endpoint
6. Route /admin/system-control (~10 min)
7. Smoke test manual E2E (~20 min)
```

---

## Smoke Test Plan (manual)

| Paso | Acción | Resultado esperado |
|---|---|---|
| 1 | Iniciar sesión como `admin` | JWT normal en sessionStorage |
| 2 | Navegar a `/admin/system-control` | Panel visible ✅ |
| 3 | Ingresar clave incorrecta | Counter de intentos: 1/3 |
| 4 | Repetir 2 veces más | Botón deshabilitado (isLocked = true) |
| 5 | Recargar página | Counter reset a 0 (era signal en memoria) |
| 6 | Ingresar clave correcta | Banner rojo con cuenta regresiva 4:59 |
| 7 | Navegar a `/admin/users` y volver | Sesión sigue activa (store sobrevive nav) |
| 8 | Esperar 300s | Banner desaparece, token limpiado |
| 9 | Ir a `/admin/audit` → tab "Alertas" | Eventos GOD_MODE_ACTIVATED con IP/JTI |
| 10 | Verificar fila roja parpadeante | Activación < 24h → animate-pulse rojo |

---

## Archivos a Crear / Modificar

| Archivo | Acción |
|---|---|
| `frontend/src/app/core/stores/god-mode.store.ts` | **CREAR** |
| `frontend/src/app/core/interceptors/god-mode.interceptor.ts` | **CREAR** |
| `frontend/src/app/modules/admin/system-control.component.ts` | **CREAR** |
| `frontend/src/app/modules/admin/forensic-dashboard.component.ts` | **MODIFICAR** (agregar tab) |
| `frontend/src/app/app.config.ts` | **MODIFICAR** (registrar interceptor) |
| `frontend/src/app/app.routes.ts` | **MODIFICAR** (agregar ruta `/admin/system-control`) |