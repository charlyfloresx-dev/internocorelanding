# Master Implementation History - 2026-03-29

## Viatra Service Stabilization & Multi-Tenant Login Handshake

### 🎯 Objective
Stabilize the backend microservices (`viatra-service` and `auth-service`) and their integration with the `viatra-frontend`. Fix multi-tenant seeding errors, correct repository method queries, implement standard global error handling, and refine the social login handshake across services.

### 🛠️ Technical Decisions & Actions Taken
1. **Docker Compose & Viatra Startup**: Fixed startup issues by properly configuring the `PYTHONPATH` and standardizing `docker-compose.yml` build contexts, ensuring all internal microservices map to `/common` correctly.
2. **Auth Service Seeding & Idempotency**: Fixed a bug where dynamic OAuth users (like Google Logins) duplicated `user_company_roles` records upon container restarts due to missing explicit DB sweeps.
3. **Viatra Service Middleware**: Injected `InternoCoreGlobalMiddleware` into `viatra_service`'s `main.py` to intercept HTTP exceptions and wrap them in the standard API response schema `{"status": "error", "message": "...", "meta": {...}}`.
4. **Viatra Repositories**: Fixed a critical 500 error where `GroupRepository` and `PaymentRepository` were incorrectly invoked with `.get_all()` instead of the standard `BaseRepository.list_all()`.
5. **Selection Token Lifespan & Persistence**:
   - **Problem**: The OAuth `/social-login` handshake issued a 5-minute `selection_token` that expired while the user was idling on the select company screen. Furthermore, the frontend cleared the token after selection, preventing seamless company switching.
   - **Solution**: Extended `SELECTION_TOKEN_EXPIRE_MINUTES` to 1440 (24h) in `docker-compose.yml`, configured the frontend to retain the token in `sessionStorage`, and restarted the auth service.

### 🛑 Blockers Resolved
- `Multiple rows were found when one or none was required` in Auth Service -> Resolved via DB deduplication script and strict `ON CONFLICT DO NOTHING` during seeds.
- `Critical Middleware Error: 'GroupRepository' object has no attribute 'get_all'` -> Replaced with injected `.list_all()`.
- `401 Unauthorized: Could not validate selection token` -> Token expiration fixed by moving from 5m to 24h lifespan.
- 21. **Dashboard Locked (PENDING status)** -> Fixed by updating backend logic to trust Group `CONFIRMED` status during demo seeding, unlocking the UI for social users without needing immediate Stripe payment.
- 22. **UI High-Fidelity HUD Design**:
    - **Problem**: The dashboard was a basic list of text, failing to meet the "Mission Control" aesthetic.
    - **Solution**: Implemented a glassmorphic vertical timeline ("Expedición Islandia 2026"), a financial ledger, and neon pulse animations.
- 23. **Tailwind CSS & SVG Scaling**:
    - **Problem**: Injected Tailwind classes in a project without Tailwind, causing SVGs to scale to 100% viewport and breaking the layout.
    - **Solution**: Installed `tailwindcss@^3.4`, `postcss`, and `autoprefixer`. Configured `tailwind.config.js` and reordered `styles.scss` to fix Sass compilation errors.
