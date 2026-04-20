# 🏗️ Phase 33.5: Price Evolution and Fiscal Catalogs (SAT/HTS)

## 📋 Auditoría del Estado Actual
Tras la revisión de la arquitectura industrial y los requerimientos operativos (Areli), se identifican los siguientes pilares para la evolución del maestro de productos y precios:

### 1. Gestión Fiscal Transfronteriza (México & US)
El sistema debe actuar como un traductor fiscal entre regiones:
- **SAT (México)**: Cada producto debe estar mapeado a la clave de producto/servicio (8 dígitos) y unidad (Clave SAT).
- **HTS (EE. UU.)**: Inclusión del campo `hts_code` (10 dígitos) para clasificación arancelaria en transferencias internacionales.
- **IA Semántica**: Integración de búsqueda vectorial para sugerir claves basadas en el nombre del producto (ej. "Regla de metal" -> 41111604).

### 2. Arquitectura de Precios Multitenant
- **Inmutabilidad vs. Flexibilidad**: Los precios maestros son sugeridos, pero se permite el **Manual Override** en la transacción.
- **Estructura de 10 Listas**: Implementación de tablas `ProductPrice` que soporten 10 índices de listas por empresa.
- **Impuestos Desacoplados**: Los precios en DB son **NETOS**. El IVA (8%/16%) o Sales Tax se calcula en el "checkout" del documento.

### 3. Logística "Espejo" (Simplicidad Areli)
- **Transferencia Atómica**: Al confirmar una salida en Empresa A (México), se genera automáticamente un **Draft de Entrada** en Empresa B (USA).
- **Apertura Express**: El alta de producto permite capturar existencias iniciales, disparando un movimiento de apertura automático.

---

## 🛠️ Especificaciones Técnicas

### Modelo `Product` (SQLAlchemy)
```python
class Product(MultiTenantBase):
    # Identificadores Legados e Industriales
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    
    # Fiscal México/EE. UU.
    sat_product_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    hts_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Control Operativo
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    allow_price_override: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Gestión de Inventario
    min_order_qty: Mapped[float] = mapped_column(Numeric(12, 4), default=0.0)
    max_order_qty: Mapped[float] = mapped_column(Numeric(12, 4), default=0.0)
    safety_stock: Mapped[float] = mapped_column(Numeric(12, 4), default=0.0)
```

### Modelo `ProductPrice`
```python
class ProductPrice(MultiTenantBase):
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    price_list_index: Mapped[int] = mapped_column(Integer) # Listas 1 a 10
    amount: Mapped[float] = mapped_column(Numeric(12, 4))   # Neto
    currency: Mapped[str] = mapped_column(String(3))       # MXN / USD
    unit_type: Mapped[str] = mapped_column(String(20))     # BASE / SALE
```

---

## 🚀 Prompt de Ejecución para Antigravity (VSC Agent)

> [!TIP]
> Utiliza este prompt para que el agente local genere el código alineado con esta especificación:

```markdown
"Antigravity: Ejecuta la Fase 33.5 - Evolución de Precios y Catálogos Fiscales.
1. Actualiza el modelo 'Product' con campos sat_product_code, hts_code, is_taxable y allow_price_override.
2. Crea la entidad 'ProductPrice' con soporte para 10 listas de precios y currency_code.
3. Implementa el Handler 'InterCompanyTransfer' para automatizar el flujo espejo: Salida en Company A = Entrada Draft en Company B.
4. Asegura que el company_id se inyecte vía MultiTenantBase en todas las operaciones."
```
