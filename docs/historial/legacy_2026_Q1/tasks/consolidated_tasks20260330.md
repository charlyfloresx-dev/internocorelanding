# Consolidated Tasks - 2026-03-30

## Completed Today [x]
- [x] **Database Purge**: Se limpió la tabla `warehouses` para eliminar registros "huerfanos" y alinear estrictamente la relación Almacén-Empresa.
- [x] **Hierarchy Expansion (Backend)**: Master Data Service Warehouse model extendido con `country_code` y bandera `is_production_resource`.
- [x] **Location Model Enhancement**: Adaptación de la tabla Locations en WMS para soportar ubicaciones Parent-Child, límites de capacidad y roles lógicos como `RECURSO` y `QUALITY`.
- [x] **Warehouse Endpoint Visibility**: Relajación del filtro local por tenant (`company_id`) a solo `is_active` para permitir a la matriz (MX) ver los almacenes destino del Partner (US) posibilitando los envíos Inter-company.
- [x] **Inter-Company Handshake Logic (Frontend)**: Actualización total de `inventory-transfer.component.ts`. Si destCo != originCo, se direcciona a `initiateInterCompanyTransfer`, dejando stock en `SHIPPED`. Si son de lo mismo, va a `dispatchInternalTransfer`.
- [x] **Frontend Badges**: Indicador de "WIP RESOURCE" embebido en los items selectores de empresa visualizando recursos máquinas vs almacenes tradicionales.
- [x] **Bug fix auth-state**: F5 refresh resolvía compañías vacías. Componentes redibujan ahora al detectar scopes amplios inter-company.

## Uncompleted / Pending for Next Phase [ ]
- [ ] Ampliar `seed.py` según sugerencia de "Golden Source" con ubicaciones (`LOC-A1-R1`) y `StockLot` estructurado con `pedimento`.
- [ ] Integrar el atributo `pedimento` en iteraciones del form (auto-fill al seleccionar Lote).
- [ ] Permitir split manual de line item cuando `requested_qty` > `earliest_lot_qty` (FIFO Support).
- [ ] Pantalla PDF/Impresión de "Hoja de Picking" ordenando por ubicación origen.
