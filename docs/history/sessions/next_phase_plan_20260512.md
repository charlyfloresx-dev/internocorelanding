# Plan de Implementación: Rate Limiting & Estrés de Inventario

Este plan detalla los próximos pasos técnicos para fortalecer la resiliencia del Monolito Unificado ante tráfico masivo y garantizar la estabilidad del motor forense.

## 🛡️ 1. Estrategia de Rate Limiting (Muro de Fuego de Aplicación)
El objetivo es proteger los microservicios de abusos y ráfagas de tráfico accidentales de dispositivos industriales.

### Componentes Técnicos
- **Algoritmo:** Token Bucket o Sliding Window.
- **Backing Store:** Redis (Local/Docker) con fallback in-memory para modo desarrollo.
- **Niveles de Limitación:**
    - **Global:** Límite por IP para prevenir ataques DoS.
    - **Por Tenant (Multi-tenant):** Cuotas de peticiones basadas en el plan de suscripción.
    - **Por Usuario:** Límites específicos para evitar scripts de extracción masiva.

### Umbrales Propuestos
- **Auth (Login/Handshake):** 10 peticiones / minuto (Protección Brute Force).
- **Inventory (Scanners):** 300 peticiones / minuto (Alta frecuencia industrial).
- **Reports:** 5 peticiones / minuto (Operaciones pesadas de CPU/DB).

## 🧪 2. Pruebas de Estrés: Inventario (1M+ Kardex)
Validación del motor forense y la capacidad de respuesta de `inventory_service`.

### Objetivos del Simulacro
1. **Población Masiva:** Inyectar 1,000,000 de registros de movimientos de inventario (`Kardex`) vinculados a 10 tenants diferentes.
2. **Latencia Forense:** Medir el tiempo de recuperación de un "Before/After" en un registro enterrado entre 1M de filas.
3. **Integridad del Ledger:** Asegurar que el `transaction_id` agrupa correctamente los movimientos sin colisiones.

### Script de Ejecución
Se desarrollará `backend/scripts/prepare_stress_inventory.py` para:
- Generar datos sintéticos realistas (SKUs, Almacenes, Colaboradores).
- Ejecutar inserciones en batches de 5,000 para no bloquear la DB.
- **Gestión de Logs:** El script operará bajo el nivel `logging.WARNING` para evitar la saturación de consola y almacenamiento durante la inyección masiva.
- Generar un reporte de tiempos de consulta post-inyección.

## ⚙️ 3. Consideraciones Técnicas de Resiliencia
- **Persistencia de Redis:** Se configurará un volumen persistente en el `docker-compose.yml` para Redis. El middleware de Rate Limit deberá manejar el "cold start" de manera elegante, permitiendo el tráfico si el servicio de Redis no está disponible momentáneamente.
- **Optimización de Pool:** Durante el estrés, se monitoreará el `overflow` del pool de conexiones de SQLAlchemy para ajustar el tamaño según la carga real de 1M de registros.

## 📅 Cronograma Sugerido (Próxima Sesión)
1. **Hito 1:** Desplegar el Middleware de Rate Limit en el core de FastAPI.
2. **Hito 2:** Ejecución del script de inyección de 1M de registros.
3. **Hito 3:** Auditoría de performance y ajuste de índices en PostgreSQL.

---
**Golden Baseline Status:** Preservado. Este plan se ejecutará sobre la base estable del 2026-05-12.
