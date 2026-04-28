# Master Implementation History: 2026-04-28

## Phase 72: Industrial WhatsApp Architecture

### 1. Technical Design
*   **Provider**: Twilio Business API (Sandbox mode for initial dev).
*   **Authentication**: Basic Auth (AccountSID:AuthToken).
*   **Payload Format**: `application/x-www-form-urlencoded` (as required by Twilio).
*   **Concurrency**: Uses `httpx.AsyncClient` for non-blocking broadcasts.

### 2. Broadcasting Strategy (Virtual Groups)
*   **Problem**: Twilio Sandbox prohibits adding the sandbox number to native WhatsApp groups.
*   **Solution**: "Virtual Grouping" at the service level.
*   **Mechanism**: 
    - The `WhatsAppGroupMapping` model allows multiple rows for the same `group_name`.
    - `NotificationService` retrieves the list of target numbers and iterates the send command.
    - Status is tracked per recipient in the `Notification` payload.

### 3. Security & Webhooks
*   **Endpoint**: `POST /api/v1/whatsapp/webhook`.
*   **Bypass**: Added to `PUBLIC_PATHS` in `InternoCoreGlobalMiddleware` to allow Twilio's unsigned/unauthenticated (by company header) POST requests.
*   **Logic**: 
    - Parses Twilio Form data.
    - Implements `/getid` command for easy discovery of Group/User IDs by non-technical plant managers.

### 4. Database Schema
```sql
CREATE TABLE whatsapp_group_mappings (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL,
    group_name VARCHAR(100) NOT NULL,
    whatsapp_group_id VARCHAR(255) NOT NULL,
    display_name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

### 5. AWS Transition Roadmap
*   Move secrets to **AWS Secrets Manager**.
*   Expose webhook via **ALB/SSL**.
*   Scale to multiple containers for high availability.
