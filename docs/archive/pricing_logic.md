# 💰 Lógica de Precios y Valuación Técnica

Manual técnico detallado sobre el motor financiero de Interno Core, enfocado en el microservicio WMS y la integración con Inventory.

## 🏛️ La Triada de Identidad Financiera

Todo cálculo de valor en el sistema debe seguir estrictamente la relación:
> **Producto + Empresa (company_id) + Almacén (warehouse_id)**

- **Global vs Local:** 
  - Si `warehouse_id` es `NULL`, el precio aplica a toda la empresa.
  - Si `warehouse_id` tiene un ID, el precio es específico para esa ubicación (útil para reflejar costos logísticos locales).

## 📊 Tipos de Valores Financieros

El sistema debe distinguir obligatoriamente los siguientes cuatro tipos de precios/costos:

1.  **Landed Cost (Costo de Entrada):**
    - Representa el costo total de adquisición.
    - Fórmula: `Precio de Compra + Fletes + Gastos Aduanales + Maniobras`.
    - Origen: InventoryDocument de entrada.

2.  **CPP (Costo Promedio Ponderado):**
    - Es el valor contable actual del stock.
    - Recálculo: Con cada entrada confirmada, se promedia el costo del stock actual con el costo de la nueva entrada.
    - Alcance: Siempre por `warehouse_id`.

3.  **Transfer Price (Precio de Transferencia):**
    - Valor pactado para movimientos inter-company dentro de un mismo grupo corporativo.
    - Actúa como precio de salida para el remitente y costo de entrada para el receptor.

4.  **Kitting Cost (Costo de Ensamble):**
    - Costo del producto terminado (Kit) al ensamblarse en el WMS.
    - Fórmula: `Suma de CPP de Componentes + Mano de Obra/Gastos de Manipulación`.

## 🛡️ Reglas de Seguridad y Cumplimiento

- **Venta a Precio Cero:** Está estrictamente prohibida. Si al consultar `GetProductPrice` el resultado es `None`, el sistema debe:
    1. Lanzar `BusinessRuleException`.
    2. Persistir un Log de Auditoría con acción `PRICE_LOOKUP_FAILED`.
    3. Disparar una tarea en segundo plano para crear un ticket en `tickets_service` con prioridad ALTA.
- **Inmutabilidad:** Una vez que un documento de inventario se marca como `CONFIRMED`, su precio y valoración quedan congelados para auditoría forense.
