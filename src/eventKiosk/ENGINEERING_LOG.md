# Interno Core - eventKiosk
## Engineering & Architecture Log

### [2026-04-11] Project Scaffold
- **Event**: Initialized `eventKiosk` as an independent Angular 19 Standalone application.
- **Goal**: Serve as a high-performance, edge-cache Progressive Web App (PWA) on Mini PCs and local guest devices (via local WLAN / routing) for live events.
- **Features Planned:**
  - `browser-image-compression` for immediate upload shrink.
  - Tinder-like swiping gesture module for bride/groom photo approvals.
  - Angular Signals for dynamic "Paparazzi Wallet" progress tracking.
  - Canvas Confetti for gamification rewards.
  - Integrates locally into `kiosk-service` and Stripe Elements via Localhost proxying.

### [2026-04-11] UI Framework & Upload Logic
- **Architecture**: Established Tailwind CSS 3.4 for maximum Angular 19 compilation stability. Created core components (KioskLayout, Header, Swipe UI).
- **Core Signal**: Built `WalletService` utilizing Angular Signals for completely reactive and atomic balance state management without RxJS overhead.
- **Upload Optimization**: Deployed `browser-image-compression` on the client. Converts native 12MB photos to <1.5MB immediately. Allowed both video and photo multiselect uploads straight from the guest's device/gallery.
- **Dual Approval (Tinder Match)**: Implemented dual role context (`GROOM` / `BRIDE`). Swiping right verifies against backend state; if both approve, it's a Match (`status=APPROVED`) rewarding the user with native Canvas Confetti. Video `mime_types` automatically bypass approval natively to `DONE` state for direct USB export.
- **Smart Checkout Flow**: Built `CheckoutPageComponent` enabling hybrid payments. Uses Angular Signals to auto-evaluate the Cart. If Paparazzi Wallet credits cover the balance, it instantly delegates payment to credits. If debt remains, it seamlessly renders Stripe Payment Elements (PWA). Includes auto-handling of interpolation JS string literals (`$ {{ }}`).
- **Event Onboarding (Setup Module)**: Created a "Bridalova Style" setup console (`SetupPageComponent`) to upload Watermarks (PNG/SVG) and configure the session. Added a purely local HTML5 `<canvas>` fallback for auto-generating typographical transparent watermarks. Generates dynamic QRs base64 securely encoded for three core audiences: Matches, Guests, and Managers.
- **E2E Validation & Staff Dashboard Metrics:** Validada la integración completa del Dashboard de Staff (Bridalova Style) con métricas en vivo. Ejecutada prueba manual de "Tinder Swipe" con confetti de victoria; el sistema ahora vincula dinámicamente el `event_id` desde el servicio para permitir transiciones Setup -> Approval sin configuraciones manuales adicionales.
