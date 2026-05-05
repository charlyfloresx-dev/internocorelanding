# InternoCore Forensic Manifest
> **Source of Truth for Deterministic Infrastructure UUIDs**

This document serves as the master registry for deterministic UUIDs used across the InternoCore monolith and cloud environments. 

By enforcing fixed UUIDs for core infrastructure elements (Tenants, Plans, Superadmins), we guarantee that:
1. **Foreign Key Integrity** is preserved across local resets, staging, and production.
2. **Cloud Re-deployments** do not orphan relational data (like Webhooks, S3 buckets, or Stripe Customers).
3. **Forensic Audit Trails** maintain consistent identifiers for tracing cross-service events.

---

## 1. Corporate Hierarchy (Tenants)

| Entity Type | Name | Fixed UUID | Description |
| :--- | :--- | :--- | :--- |
| `BusinessGroup` | **Global Industries** | `eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e` | Root organization node holding all companies. |
| `Company` | **NexoCorp Manufacturing** | `9cd9986b-89da-48b7-8733-26a2a1225b01` | Flagship manufacturing enterprise (ENTERPRISE_ID). |
| `Company` | **NexoCorp Logistics MX** | `ad6cc8a6-34f9-42df-8f29-28254e0ad242` | Primary logistics hub in Mexico (LOGISTICS_MX_ID). |
| `Company` | **NexoCorp Logistics US** | `777cc8a6-34f9-42df-8f29-28254e0ad277` | US logistics operation (LOGISTICS_US_ID). |

---

## 2. Security & Access (Principals)

| Entity Type | Name | Fixed UUID | Description |
| :--- | :--- | :--- | :--- |
| `User` | **Charly (Admin)** | `69aa5ddc-bbaa-46e6-a7f0-aeb4b92b6d38` | Master administrator account (CHARLY_ID). |
| `User` | **Tech 01** | `11111111-bbaa-46e6-a7f0-aeb4b92b6d38` | Seed technician for triage validation. |
| `User` | **Tech 02** | `22222222-bbaa-46e6-a7f0-aeb4b92b6d38` | Seed technician for triage validation. |
| `User` | **Demo Operator** | `d3d3d3d3-bbaa-46e6-a7f0-aeb4b92b6d38` | Operator for demonstration purposes. |

---

## 3. Subscription & Billing (SaaS)

| Entity Type | Name | Fixed UUID | Description |
| :--- | :--- | :--- | :--- |
| `Plan` | **Enterprise Complete** | `aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee` | Full suite plan granting access to auth_core, inventory_core, mes_core, tickets_core, wms_core. |
| `Subscription` | **Sub - NexoCorp** | `11111111-2222-3333-4444-555555555555` | ACTIVE Enterprise subscription for NexoCorp Manufacturing. |
| `Subscription` | **Sub - Logistics MX** | `11111111-2222-3333-4444-666666666666` | ACTIVE Enterprise subscription for Logistics MX. |
| `Subscription` | **Sub - Logistics US** | `11111111-2222-3333-4444-777777777777` | ACTIVE Enterprise subscription for Logistics US. |

---

## 4. Master Data Core (Products)

| Entity Type | SKU | Fixed UUID | Description |
| :--- | :--- | :--- | :--- |
| `Product` | **ECM-600** | `e0e0e0e0-e0e0-40e0-a0e0-000000000001` | Engine Control Module. |
| `Product` | **TRB-700** | `e0e0e0e0-e0e0-40e0-a0e0-000000000002` | Turbocharger Assembly. |
| `Product` | **BRK-800** | `e0e0e0e0-e0e0-40e0-a0e0-000000000003` | Brake Disc Rotor. |
| `Product` | **FLI-900** | `e0e0e0e0-e0e0-40e0-a0e0-000000000004` | Fuel Injector Set. |
| `Product` | **CLT-100** | `e0e0e0e0-e0e0-40e0-a0e0-000000000005` | Clutch Kit Assembly. |

---

## Recovery Protocol (In Case of DB Reset)
If the database volume is destroyed, use these UUIDs to synchronize state with external services:
1. **Stripe:** Re-link Stripe `customer_id` using the mapped `Company` UUID.
2. **S3/CloudFront:** Reference the tenant's exact UUID folder for media and user uploads.
3. **IAM/Cognito (if adopted):** Map user sub claims directly to the `User` UUIDs above.
