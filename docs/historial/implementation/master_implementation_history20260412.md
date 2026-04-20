# Master Implementation History - 2026-04-12

## Phase: Generalization and N-Approver Quórum Engine

### Architectural Decisions
- **Transition to Quórum**: Refactored the dual-approval logic (Bride/Groom) into a generic $N$ unique approvers system.
- **Integrity Filter (Device-Based Security)**: Implemented `device_id` validation in the backend. The system now prevents a single physical device from approving the same photo multiple times even if they use different approver links. This ensures that the Quórum represents different people/devices.
- **Atomic Quórum Counter**: Added `approval_count` to `EventPhoto` for high-performance reading in the gallery, while maintaining `photo_approvals` table for detailed audit trails.
- **Staff Emergency Reset**: Implemented a "Reset Quórum" endpoint and UI feature to allow staff to clear accidental approvals and restart the voting cycle for specific photos.
- **Dynamic QR Generation**: The onboarding service now generates a unique QR for each required approver part of the quórum.

### Achievements
- Refactored `Event` and `EventPhoto` models.
- Created `PhotoApproval` model with unique constraints on `(photo_id, approver_index)` and `(photo_id, device_id)`.
- Implemented `ReviewPhotoIn` schema with `approver_index` and `device_id`.
- Upgraded `onboarding_service.py` to support $N$ approvers.
- Updated Frontend `KioskService` with `device_id` persistence in `localStorage`.
- Upgraded `SetupPageComponent` with approver count selector and multi-QR display.
- Upgraded `ApprovalPageComponent` with dynamic mode detection and quórum progress dots.
- Upgraded `StaffDashboardPageComponent` with real data integration and "Reset Quórum" capability.

### Blockers & Resolutions
- **Stale Container Cache**: Changes to Python logic weren't reflecting in the running container. Resolved by restarting the container with `docker compose restart`.
- **Database Schema Mismatch**: Added `approval_count` column wasn't present in existing DB. Resolved by dropping and recreating kiosk tables in `kiosk_db`.
- **API Response Inconsistency**: Test script failed due to mismatch in JSON keys. Fixed by aligning script with the new API response structure.
