# Consolidated Tasks - 2026-04-12

## Current Phase: Generalization (Kiosk Engine)

### Backend (Kiosk Service)
- [x] Refactor `Event` model (add `required_approvals`).
- [x] Refactor `EventPhoto` model (add `approval_count`, remove bride/groom fields).
- [x] Create `PhotoApproval` model for audit and device tracking.
- [x] Update `review_photo` logic with Integrity Filter (`device_id`).
- [x] Implement `reset-approvals` endpoint for Staff.
- [x] Update `onboarding` to generate $N$ unique approver links/QRs.
- [x] Stress Test passed (3-approver scenario validated).

### Frontend (Event Kiosk PWA)
- [x] Setup: Add "Número de Aprobadores" configuration.
- [x] Setup: Display dynamic list of Aprobador QRs.
- [x] KioskService: Implement `device_id` persistence and N-approver review calls.
- [x] Approval Page: Dynamic role detection from URL.
- [x] Swipe Component: Dynamic quórum progress dots + "Decisive Vote" hint.
- [x] Staff Dashboard: Integration with KioskService gallery.
- [x] Staff Dashboard: "Reset Quórum" button implementation.

### Pending Tasks
- [ ] Branding Config: Move `primary_color` to `Event` model and apply dynamically to PWA.
- [ ] Dynamic Logo: Ensure watermark logo is also used as the PWA favicon/header logo.
- [ ] Multi-Language Support: Generalize strings (remove "Novios" references from all components).
- [ ] Deployment Strategy: Verify MinIO connectivity in cloud environment.
