# 🚀 INTERNO CORE

Plataforma empresarial multi-módulo de última generación, diseñada con arquitectura de microservicios, seguridad Zero-Trust y despliegue híbrido.

## 📡 Estatus del Sistema
> **Estado Actual:** 🟢 **Interno Production Ready (Licensing & Auth)**
> 
> El **Motor de Licencias Dinámicas** (Subscription Service + Auth Handshake + Common Guards) y el **Code Knowledge Graph** (v1.0) están ya operativos. El sistema posee ahora auto-conciencia de sus dependencias multitenant.

## 🏛️ Arquitectura
InternoCore se rige por los principios de **Clean Architecture** y **CQRS**, asegurando un desacoplamiento total entre dominios.

- **Frontend:** Angular 19 (Signals & Reactive UI).
- **Backend:** FastAPI (Python 3.12) con SQLAlchemy Asíncrono.
- **Seguridad:** JWT enriquecido con Claims de Suscripción y RBAC.
- **Infrasestructura:** Híbrida (Docker / AWS LocalStack / Cloud).

## 🌍 Gobernanza e Integración
- **SSOT de Identidad:** `auth_service` gestiona la autenticación OIDC y el handshake de selección de empresa.
- **Gestión de Cuentas:** `subscription_service` controla los planes, módulos habilitados y periodos de gracia (God Mode).
- **Guardia Transversal:** `common.security.subscription_guard` protege todos los endpoints de negocio basándose en la suscripción activa.

---
Para más detalles sobre el rastro de cambios, consulte [REPO_LOG.md](file:///c:/API/interno/REPO_LOG.md) o el [MANIFEST.md](file:///c:/API/interno/MANIFEST.md) para el mapa de archivos.
