# Consolidated Tasks - 2026-04-11

## ✅ COMPLETED
### Backend (Kiosk Service)
- [x] Integrate `pycups` for CUPS communication.
- [x] Implement `print_worker.py` daemon with 5s polling.
- [x] Pillow image pipeline: 3:2 Crop, Watermark fusion, 300 DPI PDF.
- [x] Fix database initialization (`kiosk_db` and tables auto-create).
- [x] Handle MinIO public URL rewriting for browser preview.
- [x] Implement "Paparazzi 10 to 1" credit rewards loop.

### Frontend (Event Kiosk PWA)
- [x] Setup Page: Event config + QR Master generation.
- [x] Approval Page: Tinder Swipe + Dual reviewer toggle.
- [x] Confetti integration for matches.
- [x] Staff Dashboard: Metric cards + Approved feed.
- [x] Checkout: Shopping cart + Method selection (Stripe/Cash/Wallet).

## 🚧 IN PROGRESS
- [ ] Refactoring `/gallery` to show approved photos (currently same as approval state).
- [ ] Finishing Stripe Elements integration UI details.

## 📅 PENDING (Backlog)
- [ ] **Hardwaare Prod**: Install DNP/Hiti drivers on Mini PC (Host).
- [ ] **Reporting**: "Cierre de Caja" report (Cash vs Stripe totals).
- [ ] **Analytics**: Export event guest activity as CSV.
- [ ] **Cleanup**: Renaming directory `eventKiosk` to `event-kiosk`.
- [ ] **Compliance**: Final security audit for presigned URL expiration.
