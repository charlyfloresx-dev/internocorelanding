# Plan de Implementación: Auditoría de Resiliencia del Frontend (Sentinel)

Este plan aborda la "Paridad de Errores Semánticos" y el "Blindaje de Conectividad" para garantizar que el Frontend (Angular/Flutter) funcione como un centinela altamente resiliente.

## Hallazgo Crítico Inicial (Backend)
Durante la inspección del `InternoCoreGlobalMiddleware` (`backend/common/middleware.py`), se descubrió que las `DomainException` se están serializando **sin la propiedad `code`**. 
Actualmente el payload envía:
```json
"meta": {
    "trace_id": "uuid",
    "details": {}
}
```
Para que el frontend pueda interceptar errores como `INSUFFICIENT_STOCK` o `QUOTA_EXCEEDED`, necesitamos modificar el middleware para inyectar `code` en el objeto `meta`:
```python
"meta": {
    "trace_id": transaction_id,
    "code": getattr(e, 'code', None),
    "details": getattr(e, 'details', {})
}
```

---

## Fase 1: Paridad de Errores Semánticos (El Frontend Centinela)

### 1. Actualización de la Interfaz del Error (`domain.types.ts`)
Debemos extender el modelo del interceptor para reconocer el estándar estructurado del backend:
```typescript
export interface BackendErrorResponse {
  status: 'error';
  message: string;
  meta: {
    trace_id: string;
    code?: string;
    details?: any;
    latency?: string;
  }
}
```

### 2. Refactor del `ErrorMapper` (`error-mapper.ts`)
Actualmente `ErrorMapper` solo reacciona a HTTP Status Codes. Debe evolucionar para analizar la semántica del negocio usando el `code` provisto en el `meta` de la respuesta:
*   **`INSUFFICIENT_STOCK`**: Sugerir flujo de "Ajuste de Inventario" en base a `meta.details.missing`.
*   **`QUOTA_EXCEEDED`**: Inyectar directiva visual de Upgrade Plan (Integration con `SubscriptionService`).
*   **Fallback Semántico**: Mapeo estándar de `DomainException` o `BusinessRuleException` usando el `message` original provisto por el backend.

### 3. Intervención en el Interceptor Global (`error.interceptor.ts`)
El interceptor debe inyectar la lógica de negocio (por ejemplo, levantar el modal de subscripción) antes de emitir un simple Toast de error. Además, la persistencia del `trace_id` debe ser visible en el Toast de UI para facilitar el reporte del operador al equipo de soporte.

---

## Fase 2: Blindaje de Conectividad (Idempotencia y Degradación)

### 1. Inyección de Cabecera de Idempotencia
Crearemos el interceptor `idempotency.interceptor.ts`. Este componente detectará mutaciones críticas (HTTP POST, PUT, DELETE) hacia rutas de alto riesgo (ej. `/checkout`, `/transfer`) y automáticamente generará y adjuntará la cabecera `Idempotency-Key: UUIDv4`. 
Esto prevendrá la duplicación de inserciones en Kardex si el operador presiona dos veces un botón o si experimenta un pico de latencia del NAT Gateway.

### 2. Circuit Breaker (Degradación Elegante)
Para microservicios satélite (como el `notification_service`), integraremos un estado de Fallback Reactivo.
Si el frontend detecta un fallo de red o un 500 sostenido al intentar consultar notificaciones (vía Polling o WebSocket):
*   Se deshabilitará visualmente el ícono de notificaciones (estado Offline) en lugar de lanzar Pop-ups constantes.
*   El flujo principal del WMS (Escaneo de código de barras) nunca se verá interrumpido.

---

## Fase 3: Chaos Testing Local

Se propone el siguiente script de validación simulando un colapso en el entorno `docker-compose`:

1.  **Simular Latencia Extrema**: Inyectar sleep delays de 5 segundos en el contenedor del Monolito para validar la Idempotencia (doble click del operador) y la protección contra Timeouts del Frontend.
2.  **Muerte del Base de Datos (Kill Switch)**: Ejecutar `docker stop internocore-postgres-db` en medio de una operación de recepción de inventario y verificar si el Frontend muestra el "Fallo de Conectividad" o si redirige a una vista "Offline".
3.  **Agotamiento de Cuota Ficticia**: Forzar un status `RESTRICTED` y enviar un POST para detonar el `QUOTA_EXCEEDED` del Muro de Hierro y visualizar si el "Banner de Upgrade" se activa exitosamente en la UI.

---

## Fase 4: Auto-Recuperación de Base de Datos (Muro de Hierro)

Tras validar la caída y recuperación segura de la UI (Kill Switch), es crítico asegurar que los microservicios reconecten limpiamente al restaurar el contenedor de Postgres, en lugar de quedarse congelados (Stale Connections) lanzando "Connection refused" indefinidamente.

### 1. Inyección Universal de `pool_pre_ping=True`
Se inyectará globalmente `pool_pre_ping=True` en todos los `create_async_engine` a lo largo de los 14 microservicios (incluyendo `inventory_service`, `master_data_service`, `tickets_service`, etc.).
Esto delega en SQLAlchemy la responsabilidad de validar la conexión del pool antes de usarla, reciclando la conexión asíncrona automáticamente si la base de datos se reinicia de manera forzada.
