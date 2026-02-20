# 📂 INTERNO CORE - MASTER INDEX (SSOT)

> **Version:** 1.0.0
> **Last Updated:** 2026-02-10
> **Status:** Active

## 1. Identidad del Proyecto
**Interno Core** (anteriormente referenciado como *NexoSuite*) es un sistema de ejecución de manufactura (MES) híbrido, diseñado para operar tanto en la nube (SaaS Multi-tenant) como en servidores locales (On-Premise Single-tenant) utilizando una única base de código unificada.

---

## 2. Mapa de Documentación (Documentation Map)

### 🏛️ Arquitectura & Principios
*   **01_ARCHITECTURE.md**: (Consolidado) Constitución Técnica, Stack (FastAPI/Angular), Estrategia Híbrida y Patrones de Diseño.

### 💻 Frontend (Angular 19 Zoneless)
*   **FRONTEND_CONTEXT.md**: Guía para el desarrollador frontend. Reglas de "Identidad Triple", inmutabilidad y manejo de señales.
*   **ENGINEERING_LOG.md**: Bitácora de ingeniería, changelog y decisiones técnicas del cliente web.

### 🔙 Backend Microservices
*   **02_BACKEND_DEPLOYMENT.md**: (Consolidado) Especificaciones de despliegue AWS, configuración de Auth Service y Disaster Recovery.
*   **Auth Service:** `backend/auth_service/` - Gestión de identidad, OIDC y Multi-tenancy.
*   **Common:** `backend/common/` - Librería compartida (Modelos base, Respuestas estándar, Middlewares).
*   **Inventory:** `backend/wms_service/` *(En desarrollo)*
*   **Production:** `backend/mes_service/` *(En desarrollo)*

### 📜 Histórico & Legado
*   **docs/archive/Profile.txt**: Contexto histórico y evolución del negocio (SMK -> Zodiac -> Interno Core).
*   **docs/archive/INTERNAL_CLEANUP_LOG.md**: Registro de limpieza y normalización del repositorio.

---

## 3. Glosario de Términos Clave
*   **SSOT (Single Source of Truth):** Este índice y los archivos que referencia.
*   **Hybrid Core:** La capacidad del sistema de comportarse como SaaS o On-Premise basándose únicamente en variables de entorno (`.env`).
*   **Zoneless:** Arquitectura frontend sin `zone.js`, utilizando Angular Signals.
*   **Zero Trust:** Modelo de seguridad donde no se confía en la persistencia local sin validación contra el backend.

---

## 4. Estado del Sistema
*   **Fase Actual:** Fase 1 - Identificación y Rebranding.
*   **Próximo Hito:** Migración completa a AWS y estandarización de `backend/common`.