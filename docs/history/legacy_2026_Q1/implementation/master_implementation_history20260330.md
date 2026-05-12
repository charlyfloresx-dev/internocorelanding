# Master Implementation History - 2026-03-30

## Architectonic Resurgence: Binational Routing & Industrial Hierarchy

La sesión del 30 de marzo se enfocó en consolidar el **Core Operativo** de Interno para dominar la logística binacional (MX-US) y el rastreo granular de inventario en ubicaciones físicas (Bin/Rack).

### Core Decisions & Achievements

#### 1. Zero-Trust Contexting
El rediseño del flujo de trabajo desplazó la visión de "Elijo de dónde sale el stock" por un **"Defino donde estoy parado físicamente"**. El selector global de Tenant y Almacén (Contexto de Operación) gobierna ahora todas las interacciones, blindando el rol `OPERATOR` frente a envíos equivocados de naves industriales cruzadas.

#### 2. Binational Inter-Company Routing
Se resolvió un fallo de diseño crítico donde los usuarios de la Compañía `INTERNO-MX` no podían iniciar transferencias hacia `INTERNO-US` porque los almacenes meta, por naturaleza multi-tenant, eran invisibles para su sesión.
- **Implementación**: Se relajó el `select(Warehouse)` en Master Data, desestimando la restricción de grupo `company_id`.
- **Efecto de red**: El dropdown de Front-End ahora bifurca de manera inteligente. Si la compañía destino difiere del contexto de inicio, dispara la macro de `initiateInterCompanyTransfer` enviándola al Bridge (tránsito SHIPPED), de lo contrario usa `dispatchInternalTransfer`.

#### 3. Industrial Infrastructure & WIP
Extendimos el catálogo de `Location` (Rack/Bin/Zone) para modelar explícitamente contenedores anidados (Parent-Child) y capacidades (Max y Current). Esto transformó el concepto de "Nave de Manufactura" para permitir declarar Máquinas (Fresadoras/CNC) como almacenes tipo `RECURSO / WIP` a fin de poder empujar stock directamente a la línea. El frontend ahora adorna estas rutas con insignias azules (`WIP RESOURCE`) previniendo extravíos operacionales.

#### 4. The Path to "Golden Source"
Iniciando la fase 40 para implementar verdaderamente el **Inventory Layer 2 / Smart Storage**. Transicionaremos del esquema simple de SKU a la estructura `SKU + Lote + Pedimento + Location_ID`, posibilitando el estricto cumplimiento LIFO/FIFO para cumplimiento aduanero norteamericano.

### Technical Debt / Backlog Resolved
- `TypeError` de UoM IDs. Corrección defensiva anti-cadena-vacía sobre identificadores UUID.
- Cacheo Fantasma Front-End. Botón de recarga y adaptadores Promise.allSettled integrados.
- Purgado asíncrono sobre `scripts/seed.py` garantizando un reinicio a-cero transparente sobre bases dev.
