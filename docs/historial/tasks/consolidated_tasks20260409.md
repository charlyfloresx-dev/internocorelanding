# Consolidated Tasks — 2026-04-09

## ✅ Completed Today
- [x] **Review Inventory Flows**: Audited `flow_1` to `flow_5` for schema and logic consistency.
- [x] **Fix Flow 2**: Corrected discharge quantity polarity.
- [x] **Fix Flow 3**: Added second user to bypass self-receipt validation.
- [x] **Execute Flows**: Successfully ran all 6 flows and verified successful database entries via logs.
- [x] **Part Number Seeding**: Created and ran `seed_variants.py` with 5 industrial parts and 15 total variants.
- [x] **Bulk Purchase**: Executed `flow_6_purchase_variants.py` to seed 1,500 total units across all 15 variants.

## 🏗️ In Progress
- [ ] **Inventory Dashboard Integration**: Verifying that the seeded movements and variants reflect correctly in the forensic telemetry views.

## 📋 Backlog / Next Steps
- [ ] **Multi-Currency Validation**: Test Flow 5 with different exchange rates to verify WAC revaluation in USD.
- [ ] **Warehouse Transfer Edge Cases**: Test transfers with "Damaged" quantities in `CompleteTransferCommand`.
- [ ] **Customs Pedimento Linkage**: Verify that FIFO discharge correctly links the `customs_pedimento_id` to the new `Movement` record.
