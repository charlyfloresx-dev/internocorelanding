# 💰 Motor de Precios y Contratos (Pricing System)
**Status:** ✅ IMPLEMENTED (Phase 44) - Industrial Ready


Especificación técnica del motor financiero y la lógica comercial de **Interno Core**, enfocada en la gestión de listas de precios, contratos comerciales (Vendor/Customer agreements), valuación en el WMS y seguridad transaccional.

---

## 1. 🏛️ La Jerarquía de Precios (¿Quién manda?)
Para un sistema de grado industrial, el motor de valuación de inventarios y facturación sigue este **orden de precedencia (Prioridad Máxima a Mínima):**

1. **Contrato/Acuerdo Específico (PriceAgreement):**
   * *Prioridad Máxima.* Si el "Cliente A" tiene un contrato firmado para el "Producto X" a $50 USD, el sistema impone este precio e ignora todas las listas generales.
2. **Lista de Precios Asignada:**
   * Si no hay contrato, el sistema verifica si la entidad (Cliente/Proveedor) tiene pre-asignada una lista (ej. "Lista 2: Mayoreo").
3. **Precio Maestro (Lista 1 / Base):**
   * Si no hay contrato ni lista predeterminada, se utiliza por defecto el precio público o base del catálogo maestro.

---

## 2. 🤝 Implementación Técnica: Contratos (Price Agreements)

Para soportar las transacciones por contrato, el modelo de datos de la Fase 33.5 se extiende con la entidad **`PriceAgreement`**.

* **Vínculo Directo:** Relaciona estrictamente un `product_id` con un `customer_id` (o `vendor_id`).
* **Vigencia (Inmutabilidad Temporal):** El contrato tiene obligatoriamente campos `start_date` y `end_date`. Fuera de esta ventana, el contrato comercial es nulo para el motor.
* **Respaldo Legal:** Incluye un campo `document_reference` (o `file_uuid`) para adjuntar el PDF del contrato o el folio interno. Esto sirve de auditoría por si el usuario cuestiona "¿por qué le vendemos tan barato?".
* **Herencia Multi-Tenant:** `PriceAgreement` hereda de `MultiTenantBase` para garantizar el aislamiento por `company_id`.

---

## 3. 🏭 El Flujo de Compra (Proveedores y Costo WAC)

Cuando se negocia un contrato con un proveedor, el precio definido impacta directamente el **Costo Promedio Ponderado de la Empresa:**

1. Al capturar la Orden de Compra/Entrada, el sistema detecta que existe un contrato de suministro vigente para el producto.
2. El sistema **bloquea o advierte** si el comprobante logístico intenta sobrepasar el monto pactado del contrato (evitando sobrecostos al WAC).
3. Esto garantiza que el porcentaje de *Margen de Utilidad (MarkUp)* proyectado en el Wizard de creación de productos se mantenga como una variable real y no ficticia.

### 📊 Tipos de Valores Complementarios (Valuación Técnica)
Todo precio interactúa con el flujo logístico a través de cuatro indicadores:
* **Landed Cost (Adquisición Total):** Precio pactado + Fletes + Gastos Aduanales + Maniobras.
* **CPP (Costo Promedio Ponderado):** Valor contable perpetuo. Se ajusta con cada confirmación de entrada basándose en precios de adquisición.
* **Transfer Pricing:** Margen pactado interno para movimientos "Inter-Company".
* **Kitting Cost:** Suma de CPPs de los componentes + gastos operativos directos de ensamble.

---

## 4. 💻 Especificaciones para el Agente Cognitivo

Para instrumentar este comportamiento en los flujos principales (Wizard y Catálogos), deben seguirse las siguientes métricas:

### Base de Datos y Servicios (`auth_db` / `master_db`)
1. **Modelado:** `PriceAgreement` hereda de `MultiTenantBase`.
2. **Consultas (Look-Ups Rápidos):**
   ```sql
   SELECT price FROM price_agreements 
   WHERE entity_id = :id AND product_id = :prod AND current_date BETWEEN start_date AND end_date
   ```

### Frontend UI (`ProductPriceListComponent` y Wizard)
1. **Gestor de Precios:** El componente `ProductPriceListComponent` agregará una nueva pestaña superior de "Contratos Vigentes" (`Price Agreements`), permitiendo a usuarios auditar qué entidades tienen tratos cerrados que anulan el nivel de la tabla visual (Tabla de Nivel #1 al #10).
2. **Product Wizard (Paso 4):** Se agregará un botón o atajo ("Añadir Acuerdo Especial / Contrato") al final del paso de captura de Precios. De esta manera, el usuario podrá vincular inmediatamente el contrato comercial recién cerrado sin salir del flujo de creación de producto.

---

## 5. 🛡️ Reglas de Seguridad Irrompibles

1. **La Triada de Identidad:** Todo cálculo de valor sigue la relación `Producto + Empresa (company_id) + Almacén (warehouse_id)`. `warehouse_id = NULL` denota una cotización de la empresa completa.
2. **Venta a Precio Cero:** Estrictamente prohibida en producción. Si `GetProductPrice` (luego de buscar contratos y listas) falla y resulta en nulo o cero:
   * Lanzar `BusinessRuleException(409)`.
   * Registrar acción en `AuditLog` como `PRICE_LOOKUP_FAILED`.
   * (Futuro) Crear ticket automático urgente en `tickets_service`.
3. **Inmutabilidad Transaccional:** Al marcar un `InventoryDocument` como `CONFIRMED`, el cálculo derivado del contrato para ese instante en el tiempo queda **congelado** independientemente de si el contrato expira un segundo después.
