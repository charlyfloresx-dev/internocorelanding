# 🚩 Pendientes Activos: InternoCore Industrial

> [!IMPORTANT]
> **RECORDATORIO**: El usuario necesita reiniciar el ordenador. Al retomar, priorizar el mazo de **Put-away** para cerrar el ciclo operativo de almacén.

Este documento centraliza los bloqueos y tareas críticas para el núcleo industrial, ignorando el ecosistema de eventos.

## 🛠️ Microservicios & Lógica de Negocio
- [ ] **Tickets Service (CRÍTICO)**: Incrementar cobertura de tests del 0% a al menos 70%. Es el motor de escalación meso-ERP.
- [ ] **Help Desk (Tickets)**: Esqueleto presente, pero nula lógica de escalaciones.
- [x] **Logística (WMS/Inventory)**: Trasladada madurez de Catalog/Prices a Handhelds (Inbound/Picking). Implementado soporte Offline y Visibilidad Financiera.
- [ ] **WMS ICT Validation**: Pruebas de carga para transferencias atómicas entre empresas (Inter-Company Transfers) en entornos de red inestable.
- [ ] **Viatra Grace Period**: Implementar el periodo de gracia de 48h para suscripciones con pago fallido (Sync con Stripe).
- [ ] **Frontend Search Protocool**: Asegurar que todos los buscadores de productos implementen el patrón RxJS `debounceTime(300)` + `switchMap`.
- [ ] **Dashboard de Márgenes (FINANCIERO)**: Crear vista de análisis que compare Nivel 0 (Compra) vs Niveles 1-10 (Venta) para alertar sobre rentabilidad negativa.
- [ ] **Engine Point-in-Time**: Implementar helper en el backend para recuperar el precio histórico exacto basado en la fecha del documento (Inmutabilidad).
- [ ] **Handshake de Inventarios**: Validar que el flujo de venta descuente stock usando el `price_id` de la versión inmutable activa.

## 📦 WMS Inbound & Outbound Handheld (Industrial Integrity)
- [x] **Cycle Count (Spot Audit)**: Implementado flujo de conteo ciego (Blind Count) con reconciliación automática. Componente `CycleCountComponent` con 3 pasos (Scan Location → Blind Count → Discrepancy Analysis).
- [x] **Audit Sheet Export**: Generador CSV de hojas de conteo técnico con Anexo 24 (Ubicación/SKU/Pedimento/Cantidad Teórica + columna de conteo manual).
- [x] **Put-Away Handheld & Entrada Manual**: Actualizados estilos dinámicos de colores para `surface-bg`. Flujo implementado: Escaneo en Rampa -> Escaneo en Rack -> Confirmación.
- [x] **Picking & Embarques Handheld (Outbound)**: Implementado componente `inventory-shipping` para despacho. **Incluye la validación crítica de Gafete del Operador** como paso hacia HR Service (Fase 50).
- [ ] **Density Guard V2**: Extender la validación de capacidad para incluir volumen (m3) además de piezas.
- [ ] **Inter-Company Stress Test**: Validar transferencias masivas entre MX y US bajo carga de red simulada (Fase 48).

## 🏛️ Arquitectura & Documentación
- [ ] **Diagramas C4**: Actualizar diagramas de contenedores para reflejar el estándar de prefijo `CORE_`.
- [ ] **API Reference**: Generar documentación OpenAPI unificada en el portal `DOCS_INTERNOCORE.html`.
- [x] **Registry de Catálogos (Performance)**: Implementado Cache Map (SKU -> UI Metadata) en Frontend para reducción de latencia (Registry Cache).
- [ ] **Industrial UX Optimization**: Implementar CDK Virtual Scroll para listas masivas (>100 items).

## 👤 HR Service (Gestión de Colaboradores)
- [ ] **Modelo de Colaborador (hr_service)**: Crear entidad `Collaborator` con campos de identidad industrial: nombre, puesto, planta asignada, turno.
- [ ] **Cross-Border Despacho (Credenciales Binacionales)**: Integrar atributos `visa_number`, `sentry_id`, `global_entry_id`, `visa_expiry` al perfil del colaborador. Estos datos son prerequisito para autorizar embarques internacionales MX↔US. *(Hallazgo del análisis del legacy `Interno.Domain/Person.cs`)*.
- [ ] **Compliance Fiscal (RFC/CURP)**: Agregar campos `rfc` y `curp` con validación regex al modelo del colaborador para cumplimiento SAT. *(Portado del legacy `Interno.Domain/Person.cs`)*.
- [ ] **Consulta de Elegibilidad**: Endpoint que valide si un operador tiene credenciales vigentes para operar en un despacho cross-border (Visa no expirada + Sentry activo).

## 🌐 Infraestructura (Fase 44)
- [ ] **AWS Secrets Manager**: Migrar todas las variables `CORE_` desde archivos `.env` locales hacia el gestor de secretos de AWS.
- [ ] **AWS Storage**: S3/Cloudfront sigue ausente. Necesitamos decidir la ruta de despliegue en CDN pronto.
- [ ] **Cloud Connectivity**: Validar que MinIO resuelva correctamente bajo el dominio `momentos.com` en entorno Fargate.
- [ ] **Telemetría**: Configurar Prometheus/Grafana para capturar métricas de los 10 microservicios principales.

---
**SSOT - Última Actualización:** 2026-04-15
**Enfoque:** Industrial MES/ERP Only.
