# 📦 Microservicio: Interno.Inventory (WMS & ERP Core)

## 1. Propósito y Alcance
El microservicio de Inventarios es el responsable de gestionar el ciclo de vida físico y financiero de los materiales y productos [cite: 2026-01-20]. Su función principal es garantizar la integridad del stock mediante un modelo de Libro Mayor (Ledger), donde cada cambio en la existencia debe estar respaldado por un documento auditable e inmutable una vez confirmado [cite: 2026-01-20].

## 2. Pilares de Arquitectura
- **Clean Architecture & CQRS:** Separación estricta entre la lógica de comandos (escritura) y las proyecciones de stock (lectura) para garantizar escalabilidad en AWS [cite: 2026-01-20].
- **Multitenancy Enterprise:** Aislamiento profundo de datos por company_id mediante el mixin `MultiTenantBase` [cite: 2026-01-20]. Soporta visibilidad y transferencias inter-empresa para grupos corporativos mediante permisos cruzados del `auth_service` [cite: 2026-01-10].
- **Inmutabilidad y Auditoría:** Los documentos confirmados no se borran ni editan [cite: 2026-01-20]. La cancelación genera un estado que invalida el documento para cálculos de stock, pero mantiene el registro y folio para cumplimiento fiscal (Anexo 24) [cite: 2026-01-20].
- **Tecnología:** Implementación en Python 3.10+ con SQLAlchemy, siguiendo la paridad con el directorio `common` (`BaseEntity`, `AuditBase`) [cite: 2026-01-19, 2026-01-20].
- **Concurrencia:** Implementación de Optimistic Locking mediante `version_id` en entidades críticas (Stock) para evitar condiciones de carrera.

## 3. Estrategia de Implementación (MVP Scope)
**Objetivo:** MVP funcional de gestión de stock físico y valoración básica en 60 minutos.
- **Stock:** Físico Simple (Cantidades) + Valoración por Almacén.
- **Precios:** Implementación obligatoria de ProductPrice granular por company_id y warehouse_id.
- **Costo Promedio (CPP):** Se integra al MVP. Cada confirmación de entrada (InventoryDocument) debe recalcular el costo promedio del snapshot para ese almacén específico.
- **Exclusiones:** Transferencias Inter-Company (Fase 2). Solo movimientos internos (Entrada, Salida, Ajuste).
- **Entidades Core (Fase 1):**
  - `Warehouse`: Gestión de bodegas por empresa.
  - `InventoryDocument`: Cabecera con estados (DRAFT, CONFIRMED, CANCELLED) y folios por tenant.
  - `InventoryMovement`: Detalle del movimiento con producto, cantidad y precio.
  - `InventorySnapshot`: Tabla de saldos actuales para consultas rápidas del Frontend.
  - `ProductPrice`: Histórico y actual de costos/precios por almacén.

## 4. Componentes del Dominio
### A. Documentos y Conceptos
- **Documento (Aggregate Root):** Define la operación (Compra, Venta, Ajuste, Transferencia).
- **Concepto:** Define si el movimiento suma o resta y si afecta stock físico.
- **Folios Custom:** Cada empresa gestiona su propia serie de folios operativos (ej. "FAC-001"), independiente del GUID interno de la base de datos.

### B. Gestión de Almacenes (WMS)
- **Estructura Jerárquica:** Rastreo por Almacén (Warehouse) y ubicaciones específicas (Location) [cite: 2026-01-20].
- **Stock Snapshot:** Tabla de alto rendimiento (Materialized View/Snapshot) para balances actuales, evitando cálculos costosos sobre millones de movimientos en tiempo real.

### C. Conversión y Valuación
- **Motor de Unidades (UM):** Conversiones dinámicas entre unidades de compra (Caja) y consumo (Gramos) basadas en la tabla maestra de `common` [cite: 2026-01-20].
- **Multimoneda:** Gestión de costos en diversas divisas con integración a un microservicio de tipos de cambio para valuación contable.

## 5. Lógica de Negocio Avanzada
### Valuación y Precios (Logic-First)
- **Triada de Identidad Financiera:** Todo precio/costo se rige por la relación: Producto + Empresa + Almacén.
- **Diferenciación de Valores:** El sistema debe distinguir y registrar:
  - **Landed Cost:** Costo de entrada (Compra + Gastos).
  - **CPP (Costo Promedio Ponderado):** Valor contable actual del stock en el almacén.
  - **Transfer Price:** Precio pactado para movimientos intercompany.
  - **Kitting Cost:** Al ensamblar kits en el WMS, el costo del producto resultante es la suma de los costos promedio de sus componentes más el costo de manipulación.

### Transferencias Inter-Company
- **Flujo Espejo:** Una transferencia entre empresas autorizadas genera automáticamente una salida en la empresa origen y una entrada en la destino [cite: 2026-01-10].
- **Dualidad de Precios:** Soporta un precio de venta para el remitente y un costo de compra para el receptor (TransferPrice).

### Manufactura (BOM y Lotes)
- **BOM Versionado:** Las recetas de producción mantienen historial de versiones. Las órdenes de trabajo "congelan" la versión del BOM activa al iniciar el proceso.
- **Rastreo de Lotes:** La trazabilidad se confirma en cada paso de la orden de trabajo (Steps), asegurando precisión sin saturar el modelo base del BOM.

## 6. Reglas de Configuración por Tenant (Settings)
- **Stock Negativo:** Interruptor configurable por empresa para permitir o bloquear transacciones sin existencia.
- **Flujo de Aprobación:** Define si un DRAFT requiere autorización de un Supervisor o puede ser confirmado por cualquier usuario operativo.
- **Series de Folios:** Definición de prefijos y secuencias numéricas por tipo de documento.

## 7. Estado de Sincronización (09-Feb-2026)
### 1. Auditoría y Paridad de Common (Fase 1 - Completada ✅)
- **Gap Analysis:** Se realizó el análisis frente al Legacy .NET. Se agregaron los campos `deleted_at` (Auditoría Forense) y `transaction_id` (Trazabilidad de Ledger) al `MultiTenantBase`.
- **Identidad:** Se confirmó el uso de UUID v4 en todo el sistema, manteniendo compatibilidad lógica con los códigos de cadena (string) del legacy.

### 2. Modelado del WMS (Fase 2 - Completada ✅)
- **Entidades:** Se han mapeado desde C# a SQLAlchemy los modelos `Warehouse`, `InventoryDocument`, `InventoryMovement` y `Concept`.
- **Lógica de Conceptos:** Se respeta la bandera `affect_stock: bool` y el enum `ConceptType` (Entry/Output) para determinar la dirección del movimiento físico.
- **Snapshot Layer:** Se implementó la tabla `InventorySnapshot` para balances de stock en tiempo real, protegida por Optimistic Locking (`version_id`).

### 3. Motor de Ledger (Lógica de Negocio)
- **Inmutabilidad:** El flujo de estado es DRAFT -> CONFIRMED. Una vez en CONFIRMED, el documento es de solo lectura.
- **Atomicidad:** La función `confirm_document` procesa todas las líneas, actualiza el snapshot y cierra el documento en una única transacción de base de datos usando el `transaction_id`.

### 4. Gestión de Precios y Costos (Fase 2 - Iniciada 🔄)
- **Modelo ProductPrice:** Definido con herencia de MultiTenantBase. Incluye soporte para múltiples tipos de precio (PriceType Enum).
- **Paridad Warehouse-Price:** Se ha establecido que el costo no es global de la empresa, sino específico por warehouse_id para reflejar gastos logísticos locales.
- **JSON Contracts:** Se definió el estándar de respuesta para el Frontend que incluye valuation contextualmente al almacén seleccionado.

### 5. Tarea para la Siguiente Sesión
- Implementar el **Folio Generator** (Servicio para secuencias por `company_id`).
- Configurar **Alembic** para la primera migración hacia AWS RDS (PostgreSQL).
- Exponer los endpoints de consulta de stock para el Frontend en Flutter.

## 8. Estrategia de Folios Personalizables (Implementation Detail)
Para un SaaS Multitenant, los prefijos personalizados por empresa son una necesidad operativa. Se implementará una tabla de configuración de series para permitir flexibilidad (ej. ALM-001 vs ENT-A-001).

### 1. Nuevo Modelo: DocumentSeries
Permite a cada empresa definir sus prefijos y numeración actual.

```python
class DocumentSeries(MultiTenantBase):
    __tablename__ = "document_series"

    # Ej: 'ENT', 'SAL', 'TRF', 'AJU'
    concept_code: Mapped[str] = mapped_column(String(10), index=True)
    
    # El prefijo que el usuario quiera: 'ALM-A', 'INV-', etc.
    prefix: Mapped[str] = mapped_column(String(10))
    
    current_number: Mapped[int] = mapped_column(Integer, default=0)
    
    # Opcional: Para resetear folios cada año
    year_reset: Mapped[int] = mapped_column(Integer, default=2026) 
```

### 2. Lógica del Generador Dinámico (FolioService)
El servicio busca el prefijo de la empresa (con bloqueo pesimista `with_for_update` para evitar duplicados) y si no existe, crea uno por defecto.

```python
class FolioService:
    @staticmethod
    def get_next_folio(db: Session, company_id: uuid.UUID, concept_code: str) -> str:
        # 1. Buscar la configuración de la serie para ESTA empresa
        stmt = select(DocumentSeries).where(
            DocumentSeries.company_id == company_id,
            DocumentSeries.concept_code == concept_code
        ).with_for_update()
        
        series = db.execute(stmt).scalar_one_or_none()
        
        # 2. Si no tiene serie personalizada, creamos una por defecto
        if not series:
            series = DocumentSeries(
                company_id=company_id,
                concept_code=concept_code,
                prefix=concept_code, # Ej: 'ENT'
                current_number=0
            )
            db.add(series)

        # 3. Incrementar y formatear
        series.current_number += 1
        
        # Resultado: "ALM-A-2026-0001"
        return f"{series.prefix}-{series.year_reset}-{series.current_number:05d}"
```

### 3. Beneficios
- **Aislamiento:** La numeración es independiente por empresa.
- **Flexibilidad:** Permite migrar numeraciones existentes actualizando `current_number`.
- **Auditabilidad:** El `transaction_id` del `MultiTenantBase` queda ligado a este folio único.

## 9. Reglas de Oro del Inventory Service (Logic-First)
Definidas para garantizar la integridad del Ledger ante la ausencia de reglas claras en el legacy.

1.  **Validación Atómica de Existencias:** Antes de confirmar una salida, el sistema verifica que la suma de `InventorySnapshot` sea suficiente. No se permite stock negativo a menos que `TenantSetting` lo autorice.
2.  **Snapshot como Verdad Única:** `InventorySnapshot` es la caché de alto rendimiento y fuente de verdad. Cada confirmación de documento debe actualizarlo obligatoriamente.
3.  **Inmutabilidad por Estado:** Una vez que un documento pasa de `DRAFT` a `CONFIRMED`, se bloquea cualquier intento de UPDATE en las líneas.
4.  **Generación de Folios por Transacción:** El folio se asigna en el momento de la creación del borrador, asegurando la secuencia.

## 10. Identidad Triple del Documento (Crucial)
Cada documento de inventario implementa tres identificadores para trazabilidad total:
1.  **id (UUID v4):** Identificador técnico inmutable para API y AWS.
2.  **sequence_number (Integer):** ID secuencial interno por empresa (1, 2, 3...). Es la "Verdad Única" para auditoría.
3.  **folio (String):** Identificador comercial personalizable (ej: `MEX-ENT-001`). Basado en `DocumentSeries`.

## 11. Lógica de Motor Ledger (Fase 2)
- **Atomicidad:** Uso de `with_for_update` en `InventorySnapshot` durante la confirmación.
- **Afectación Condicional:** Los movimientos solo afectan el stock físico si el `Concept` asociado tiene la bandera `affect_stock: True`.

## 12. Estrategia de Desarrollo Detallada (Fases de Ejecución)
Para transformar este diseño en un sistema Producción-Ready capaz de operar tanto On-Premise como en AWS RDS, seguiremos este cronograma técnico:

### 📍 Fase 1: Cimientos e Infraestructura (Persistencia)
**Objetivo:** Materializar el esquema de base de datos y asegurar la paridad con el ADN del sistema.
- **Implementación de models.py:** Creación de las clases SQLAlchemy integrando la Identidad Triple (UUID, sequence_number, folio).
- **Configuración de Alembic:** Inicialización del entorno de migraciones. Los scripts generados deben ser compatibles con PostgreSQL nativo para garantizar el funcionamiento en AWS.
- **Seeds de Configuración (Modo Demo):** Creación de un script `seed_wms.py` que inserte los Concepts (Entradas, Salidas, Ajustes) y las DocumentSeries iniciales para que el sistema sea funcional desde el primer despliegue.

### 📍 Fase 2: El Motor Transaccional (Business Logic)
**Objetivo:** Desarrollar el `inventory_service.py` con el rigor de un Ledger financiero.
- **Folio & Sequence Generator:** Implementación del servicio de identidad dual con bloqueo pesimista (`SELECT FOR UPDATE`) para evitar duplicados en entornos de alta concurrencia.
- **Desarrollo del LedgerProcessor:**
  - Lógica de validación de Stock Negativo consultando los `TenantSettings`.
  - Cálculo de afectación física basado en `affect_stock`.
  - Actualización atómica de la tabla `InventorySnapshot`.
- **Manejo de Excepciones de Dominio:** Implementar `StaleDataError` y `DomainException` para notificar al frontend sobre conflictos de inventario.

### 📍 Fase 3: Capa de Exposición y API (Interface)
**Objetivo:** Conectar el motor con el mundo exterior (Frontend Flutter/Angular).
- **Schemas Pydantic:** Definición de objetos de transferencia (DTOs) que expongan la identidad triple y los campos de auditoría (`created_by`, `transaction_id`).
- **Endpoints FastAPI:**
  - `POST /documents`: Crear borradores (Drafts).
  - `POST /documents/{id}/confirm`: Disparar la lógica del Ledger.
  - `GET /inventory/snapshot`: Consulta de existencias con filtros por almacén.
- **Inyección de Dependencias:** Configuración del acceso a la base de datos y el contexto del usuario actual (Tenant ID).

### 📍 Fase 4: Integración y AWS Readiness
**Objetivo:** Validar la portabilidad y preparar el despliegue.
- **Dockerización:** Ajuste de los Dockerfiles para asegurar que la carpeta `/common` se copie correctamente y el PYTHONPATH sea el adecuado [cite: 2026-01-19].
- **Pruebas de Integración:** Flujo completo: Login -> Selección de Empresa -> Creación de Documento -> Confirmación -> Validación de Snapshot.
- **Documentación OpenAPI:** Pulido de Swagger para que el equipo de frontend tenga contratos claros de los campos `sequence_number` y `folio`.

## 13. Próximo Paso Inmediato
- Construir el archivo `models.py` en el microservicio `wms_service` heredando de `common`.
- Desarrollar la lógica de bloqueo para el `FolioService`.
- Generar la primera migración de Alembic.

## 14. Modelo de Datos: ProductPrice (Nuevo Componente)
Para asegurar que el backend y el frontend hablen el mismo idioma:

```python
# Referencia de implementación en wms_service/models.py
class ProductPrice(BaseEntity, MultiTenantBase):
    __tablename__ = "product_prices"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID, index=True)
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, index=True) # Null = Global
    
    price_type: Mapped[PriceType] = mapped_column(Enum(PriceType))
    
    # Valores usando el Money Value Object
    purchase_cost: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2))
    average_cost: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2))
    selling_price: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2))
    transfer_price: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 2))
    
    currency_code: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```
