## Engineering Log - Viatra Mission Control Frontend

### [v0.6.0] - 2026-05-12 - Phase 4.2: Resilience Auditing & "Sentinel" Frontend
- **Frontend Sentinel (`resilience.interceptor.ts`)**: Implemented exponential backoff (2s, 4s, 8s) for transient network errors and semantic recovery codes.
- **Idempotency Stability**: Interceptor now guarantees the SAME `X-Idempotency-Key` is used during retries, preventing server-side duplication.
- **Error Mapping**: Refactored `error-mapper.ts` to map semantic codes (e.g., `DATABASE_RECONNECTING`) to informational UX components.
- **Status**: ✅ Phase 4.2 COMPLETED — Frontend Sentinel Active & Connection Resilience Hardened.


### [v0.5.0] - 2026-03-29 - Mission Control Dashboard Launch
- **Split-Screen UI:** Implementación de diseño industrial Slate-950/Cyan.
- **Fintech Sync:** `PaymentService` integrado con Stripe Checkout y Ledger de Historial.
- **Security:** `AuthInterceptor` para inyección de `JWT` y `X-Company-ID`.
- **Dynamic Lock:** Sistema de bloqueo visual (Glassmorphism) basado en el estatus del backend.
- **Real-Time Polling:** BehaviorSubject disparado por timer para detectar el pago exitoso.
- **PWA:** Configuración de manifest y branding Slate-950.
