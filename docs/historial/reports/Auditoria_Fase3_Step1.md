# Auditoría Fase 3 - Step 1: Paridad de Dominio (Cimientos)

## 1. La Precisión de `Money` (Decimal vs Float)
**Estado:** ⚠️ HARDENED (con Hallazgos Críticos P0 en otros servicios)

He auditado `common/value_objects.py`. `Money` efectivamente usaba `Decimal` de Python de manera básica, pero carecía del contexto estricto de C#. 
**Acciones correctivas implementadas:**
- Se inyectó `ROUND_HALF_UP` (Estándar Bancario y .NET) mediante el método `__post_init__` forzando la conversión y redondeo automático a 2 decimales (`0.01`).
- Se sobreescribieron las operaciones `__add__` y `__sub__` con **Domain Exceptions (BusinessRuleException)** si hay discrepancia de moneda (`USD` + `MXN` = ERROR).

🚨 **HALLAZGO CRÍTICO (VIOLACIÓN DE DOMINIO):**
Mi escaneo paralelo de contratos (`grep_search`) reveló que los microservicios NO están usando `Money` o `Decimal` en varios schemas, cometiendo el pecado de usar **tipos primitivos float**:
- `subscription_service/subscription_app/models/subscription.py: price: Mapped[float] = mapped_column(default=0.0)`
- `master_data_service/master_app/schemas/product.py: last_price: Optional[float] = None`
- `inventory_service/inventory_app/schemas/pos.py: unit_price: float = Field(...)`

Esto provocará que el Frontend serialice números en formato coma flotante (`0.1 + 0.2 = 0.30000000000000004`), desincronizando la capa transaccional de .NET.
**Plan:** Iniciar un Refactor P0 sobre estos schemas para usar `Decimal` o el modelo `Money`.

---

## 2. Address y Geo-Coordenadas
**Estado:** ✅ HARDENED

**Acciones correctivas implementadas:**
- `Address` ya utilizaba `@dataclass(frozen=True)` haciéndolo inmutable en Python.
- Hemos inyectado validación estricta de Regex (`^\d{5}(-\d{4})?$`) en el `__post_init__` para homologar las restricciones de códigos postales con el Backend en .NET. Si la entrada no coincide, levanta una `ValidationException`.

---

## 3. El Mapa de Excepciones (Domain Exceptions)
**Estado:** ✅ HARDENED

He auditado `common/exceptions.py` y `common/error_handlers.py`.
**Problema previo:** El contrato del error solo regresaba el HTTP status code, pero carecía del identificador de string (`code`), dificultando la traducción en el Frontend de Angular.
**Acciones correctivas implementadas:**
- Hemos reestructurado `DomainException` y todas sus herencias para aceptar y requerir un parámetro `code`.
- `BusinessRuleException` ahora levanta el código `"BUSINESS_RULE_VIOLATION"` por defecto, o el código inyectado desde el Dominio (Ej. `"INSUFFICIENT_STOCK"`).
- Esto asegura que el `error_handlers.py` devuelva un JSON simétrico: `{ "status": "error", "code": "INSUFFICIENT_STOCK", "message": "...", "meta": {...} }`.

---

## 4. Serialización de Enums (Contratos API)
**Estado:** ✅ CONFIRMADO

Audité `common/enums.py`. Todo el modelo en Python (e.g. `UserStatus`, `StatusType`, `MovementType`) ya hereda explícitamente de `(str, Enum)`.
Esto asegura que FastAPI/Pydantic serialice el valor de cadena (Ej. `"ENTRY"`) y no su equivalente de índice (`0`). El Frontend siempre recibirá strings descriptivos, blindando la comunicación contra alteraciones de índice.

---

### Próximos Pasos (CQRS & Refactor Crítico)
Tengo los cimientos alineados, pero he detectado el **Pecado Capital** del Float.
¿Me autorizas iniciar el refactor P0 masivo sobre los schemas de Master Data, Subscriptions e Inventory para erradicar el tipo primitivo `float` y migrar estrictamente a `Decimal`/`Money` antes de que procedamos a auditar la segregación de Comandos y Consultas (CQRS)?
