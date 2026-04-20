# Consolidated Tasks - 2026-03-29

## ✅ Completed Today
- [x] Configure and stabilize Docker container for `viatra-service`.
- [x] Unify `CORE_SECRET_KEY` between `auth-service` and `viatra-service` for JWT validation.
- [x] Fix data duplication upon container restarts in `auth-service` (`seed.py`).
- [x] Standardize global exception handler for `viatra-service` to match frontend interceptor specifications.
- [x] Fix `get_all` repo query methods across `viatra-service` routers (`booking.py`, `payments.py`).
- [x] Extend `selection_token` lifespan to 24 hours to support subsequent company switching within the same session.
- [x] Refactor `viatra-frontend`'s `AuthService` to persist `selection_token` after successful company selection.
- [x] Implement High-Fidelity HUD "Expedición Islandia 2026" in `viatra-frontend`.
- [x] Integrate Tailwind CSS v3.4 and fix PostCSS compilation errors in `viatra-frontend`.
- [x] Standardize `ApiResponse<T>` handling in `PaymentService` and `AuthService`.
- [x] Migrate `viatra-service` to port 8012 for local stability.

## 🚧 In Progress
- [ ] End-to-end testing of `viatra-service` Dashboard load with fresh auth tokens.

## 📋 Pending (Backlog)
- [ ] Implement AWS static deployment for `viatra-frontend` (S3 + CloudFront).
- [ ] Configure AWS VPC and Security Groups for the `interno-auth-service` and `interno-viatra-service` ECS microservices.
- [ ] Set up auto-deployment pipelines via GitHub Actions.
