# Interno Assets (Asset Opportunity Manager)

Módulo especializado de InternoCore para la Inteligencia Inmobiliaria y Gestión de Activos en Problemas (Distressed Real Estate Assets). Este CRM no es un simple gestor de contactos, sino un motor de **Análisis Geográfico y Legal** diseñado bajo Clean Architecture.

## ¿Qué es lo que ya tenemos?

Actualmente, InternoCore ya cuenta con la base técnica para este motor dentro del **Master Data Service** (`gis_validator.py` y `ArcGisTijuanaProvider`):
- **Motor GIS (WMS)**: Capacidad para consultar al FeatureServer de IMPLAN mediante coordenadas (Lat/Lng) y extraer polígonos, Clave Catastral, Lote y Manzana.
- **Consultas a RPPC y Predial**: Lógica establecida (o en proceso de finalización en el plan de Catastro v2) para hacer bypass y extraer el nombre del Titular y consultar adeudos usando la Clave Catastral y Fallback por Dirección (Unidad C).
- **Endpoint `/full-report`**: Una ruta que unifica los datos espaciales y de propiedad (`clave`, `propietario`, `superficie`, `direccion_catastral`).

## Definición del MVP (Minimum Viable Product)

El MVP de **Interno Assets** se enfocará en transformar los datos crudos del mapa en métricas financieras accionables para el usuario (Indiana).

### Funcionalidad Principal (El Pipeline "Sourcing -> Financial Analysis")
1. **Extensión del Modelo de Datos**: Creación de la entidad `InvestmentOpportunity` vinculada a una Clave Catastral, añadiendo métricas: `adeudo_total`, `valor_mercado_estimado`, `gastos_legales`, y `propietario_rppc`.
2. **Motor Financiero (Financial Engine)**: Un servicio (`OpportunityEvaluator`) que tome los datos de adeudo y el valor de mercado base de la zona, para calcular automáticamente el **ROI proyectado**.
3. **Filtro de Inversión Automático**: Un sistema de *flags* que marque una propiedad como `is_investment_opportunity = true` si el adeudo representa más del 20% del valor del terreno, o si la cuenta tiene más de 5 años sin pagos.
4. **Dashboard API**: Endpoint `GET /v1/opportunities` que devuelva una lista de predios analizados, ordenados por mayor margen de utilidad o por el "Score de Oportunidad" precalculado.

## Fases de Implementación

### Fase 1: Estructuración del Dominio y Modelo de Datos (Data Schema)
- [ ] Inicializar la estructura base de Clean Architecture en `asset_manager_service` (`api`, `core`, `domain`, `infrastructure`).
- [ ] Crear los modelos de base de datos SQLAlchemy para `InvestmentOpportunity`.
- [ ] Definir los esquemas Pydantic para ingesta y exposición de datos.

### Fase 2: Construcción del Motor Financiero (Financial Engine)
- [ ] Implementar el servicio `OpportunityEvaluator` en la capa de aplicación.
- [ ] Desarrollar la fórmula del **Score de Oportunidad**: `Score = (VM - (AD + PA)) * FactorTiempo`.
- [ ] Conectar el Evaluador para que escuche/reaccione a la creación de nuevos reportes provenientes del `master_data_service` (Endpoint `/full-report`).

### Fase 3: Integración de API y Dashboard CRM
- [ ] Crear el router y endpoints de la API (`POST /opportunities`, `GET /opportunities`).
- [ ] Integrar un Kanban básico (Pipeline Manager) a nivel de base de datos (Estatus: Scouting -> Due Diligence -> Negociación -> Cierre).

### Fase 4: Sincronización y Testing
- [ ] Escribir tests unitarios para verificar el cálculo correcto del ROI en el Financial Engine.
- [ ] Orquestar Docker Compose para incluir el nuevo microservicio `asset_manager_service`.
