# Master Implementation History - 2026-04-11

## Phase: Event Kiosk Industrialization & Hardware Pipeline

### Accomplishments
1. **Hardware & Spooling Engine**:
   - Integrated `pycups` for native CUPS printer communication.
   - Built a Pillow-based image processing pipeline:
     - 3:2 Proportional cropping (optimized for DNP 4x6 dye-sublimation printers).
     - Alpha-channel watermark fusion (Event Logo + Wedding Branding).
     - Automatic 300 DPI PDF generation for professional print quality.
   - Implemented a background `print_worker` daemon that polls for `PURCHASED` status.

2. **Frontend UX (Bridalova Style)**:
   - Finalized `ApprovalPageComponent` with "Tinder Swipe" mechanics and dual-reviewer logic (Novio/Novia).
   - Added real-time feedback with `canvas-confetti` for "Matches".
   - Implemented `StaffDashboardPageComponent` for event monitoring and metrics.
   - Fixed MinIO URL resolution for development using a public URL proxy.

3. **Multi-Tenancy & Financial Flow**:
   - Refactored `KioskService` to handle dynamic `eventId` resolution via localStorage.
   - Completed the Hybrid Checkout: Stripe (CC), Cash (Staff validated), and Wallet (Paparazzi credits).
   - Finalized "Paparazzi 10 to 1" credit rewards: Automatic 10% credit to photographer upon photo sale.

### Technical Decisions
- **URL Rewriting**: Decisions was made to keep internal Docker networking (`minio:9000`) for backend storage and use a rewrite layer in binary stream handlers (Presigned URLs) for `localhost:9000` to allow browser-side PWA interaction without complex DNS.
- **Mock Print Mode**: Implemented a fallback that saves to `/app/spool/` if CUPS is unavailable (e.g., during Windows local development).

### Blockers Resolved
- **Unicode Error**: Resolved Windows `cp1252` encoding issues in simulation scripts by forced ASCII normalization.
- **MinIO 403**: Fixed bucket policies to allow public read/write for guest content.
- **Event Mapping**: Fixed loose coupling between setup UI and approval UI by persisting event session in localStorage.
