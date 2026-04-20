# Inter-Company Transfer API - Frontend Specs
> **Status**: APPROVED
> **Endpoint Base**: `/api/v1/inventory/transfers/inter-company`
> **Authentication**: Required (`X-Selection-Token` / JWT with `company_id`)

Esta especificación detalla el contrato para los desarrolladores Frontend (Angular) que implementarán la pantalla de Traspasos Inter-Compañía en Interno Core.

---

## 🏗️ 1. Arquitectura Zero-Trust (Recordatorio Frontend)
El backend extrae `company_id` directamente del JWT autenticado en el contexto actual del usuario.
* **Empresa Origen (A):** Inicia la transferencia. El token de Empresa A se usa en `POST /initiate`.
* **Empresa Destino (B):** Recibe la transferencia. El token de Empresa B se usa en `GET /inbound/pending` y `POST /receive`.
* **Seguridad:** NUNCA envíes el ID de tu compañía en el cuerpo (body) de estos requests. Es gestionado por el JWT interceptor.

---

## ⚡ 2. Endpoints para Empresa A (Emisor)

### 2.1. Iniciar Transferencia (Dispatch)
**`POST /initiate`**

Crea la transferencia con un precio pactado ("Transfer Price"). El stock sale físicamente de Empresa A y entra al limbo digital del "Trusted Broker".

**Request Body:**
```json
{
  "destination_company_id": "d6b0bfcd-1eab-4d83-94c6-2eb969b92289", // Requerido: ID de la Empresa Destino
  "destination_warehouse_id": "a1b2c3d4-...", // Requerido: ID almacén en Empresa B
  "origin_warehouse_id": "e5f6g7h8-...",      // Requerido: ID almacén en Empresa A
  "product_id": "mati-001-...",               // Requerido: ID Producto (Capa Common)
  "uom_id": "uom-pza-...",                    // Requerido: ID Unidad de Medida
  "quantity": 50.0,                           // Requerido: > 0
  "weight": 10.0,                             // Requerido: > 0 (Forense)
  
  // Mapeo Dinámico (Opcional, pero muy recomendado)
  "origin_sku": "MAT-001",
  "destination_sku": "ENT-MAT-001",
  "destination_product_id": "mati-002-...", 
  
  // Bloque Financiero (NUEVO)
  "transfer_price": 150.00,                   // Opcional: El contrato financiero (Precio de A / Costo de B)
  
  "notes": "Traspaso urgente planta norte",
  "external_reference": "PO-12345"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid-transfer",
    "folio": "ICT-20260316-AFB2C",
    "status": "SHIPPED",
    // ... [origin, destination components]
    "unit_price_at_dispatch": 150.00,
    "wac_at_dispatch": 140.00,
    "transfer_revenue_a": 7500.00,    // 50 * 150
    "transfer_margin_a": 500.00,      // (150 - 140) * 50
    "acquisition_cost_b": null,       // nulo hasta recepción
    "price_source": "EXPLICIT",       // Enum: EXPLICIT | WAC_FALLBACK | DEFAULT_FALLBACK
    "transfer_price_warning": null
  }
}
```

> ⚠️ **Manejo en UI:** Si el usurario no manda `transfer_price`, el backend usará el WAC de A (`WAC_FALLBACK`) y devolverá un `transfer_price_warning`. Muestra ese warning como un toast amarillo en Angular si viene presente ("Transferencia despachada a precio de costo interno...").

### 2.2. Cancelar Transferencia
**`POST /{transfer_id}/cancel`**
Sólo puede hacerlo Empresa A, y sólo si el estado sigue en `SHIPPED`.

**Request Body:**
```json
{ "reason": "Error en cantidad, corrigiendo..." }
```

---

## ⚡ 3. Endpoints para Empresa B (Receptor)

### 3.1. Obtener Bandeja de Entrada (Pending Receipts)
**`GET /inbound/pending`**

Obtiene la lista de cargas "en camino" hacia el tenant actual. (El JWT filtrará automáticamente).
**Query Params:** `?limit=50&offset=0`

**Response:**
Retorna array de `PendingTransferEntity` que la UI debe mapear a una tabla "Cargas por recibir".

### 3.2. Recibir Mercancía (Complete Transfer)
**`POST /{transfer_id}/receive`**

Ejecuta el traslado del limbo digital hacia el inventario físico de Empresa B, calculando el impacto en WAC con base en el `transfer_price` que Empresa A selló en el dispatch.

**Request Body:**
```json
{
  "received_quantity": 50.0, // Permite recepción parcial (ej. si llega dañado 1, mandas 49)
  "notes": "Todo en orden. Confirmado por rampa 4."
}
```

**Response (200 OK):**
Retorna el documento completo.
```json
{
  "status": "success",
  "data": {
    "status": "DELIVERED",
    "received_quantity": 50.0,
    "acquisition_cost_b": 7500.00, // 50 * transfer_price pactado
    // ...
  }
}
```

---

## 🛠️ 4. Modelo de Estado (TransferStatusEnum)

Usa esta enumeración en TS para las etiquetas (Chips) en el Dashboard:
* `SHIPPED` (Naranja / En camino)
* `DELIVERED` (Verde / Recibido e integrado en inventario)
* `CANCELLED` (Rojo / Cancelado por origen)

---

## 🛡️ 5. Manejo de Errores Comunes (Toast/Alerts UI)

| HTTP Code | Exception Code UI | Cuándo ocurre | Acción esperada Frontend |
|---|---|---|---|
| **404** | `ERR_TRANSFER_NOT_FOUND` | URL o UUID erróneo | Redirigir a listado / 404. |
| **401** | `ERR_TRANSFER_ACCESS_DENIED` | Intentas recibir o cancelar un documento que no es para el tenant actual | Cerrar sesión por seguridad. |
| **409** | `ERR_ALREADY_DELIVERED` | Doble clic en recibir (Idempotencia) | Mostrar Toast: "Ya lo recibiste". |
| **409** | `ERR_RECEIVE_EXCEEDS_SHIPPED` | `received_quantity > quantity` | Alertar al usuario, rechazar request. |
