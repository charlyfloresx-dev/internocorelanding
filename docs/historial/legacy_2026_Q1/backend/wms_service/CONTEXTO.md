# 📦 WMS SERVICE - CONTEXTO DEL MICROSERVICIO

> **Status:** In Development
> **Last Updated:** 2026-02-10
> **Type:** Domain Service (Warehouse Management)

## 1. Responsabilidad
Gestionar las operaciones de almacén, incluyendo inventario, ubicaciones (bines), movimientos de stock, recepción y despacho de materiales. Garantiza la trazabilidad física de los activos.

## 2. Arquitectura & Stack
*   **Lenguaje:** Python 3.11+
*   **Framework:** FastAPI (Async).
*   **Base de Datos:** PostgreSQL (Schema dedicado o compartido según configuración).
*   **ORM:** SQLAlchemy 2.0.

## 3. Conceptos Clave
*   **Inventario Multi-tenant:** El stock es propiedad exclusiva de una `company_id`.
*   **Ubicaciones:** Gestión jerárquica de almacenes, zonas y bines.
*   **Movimientos:** Registro inmutable de transacciones de entrada/salida.

## 4. Dependencias
*   **Internas:** `backend/common`, `auth_service` (para validación de tokens).
*   **Externas:** PostgreSQL.