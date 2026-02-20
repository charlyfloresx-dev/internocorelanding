markdown
# 📜 AUTH SERVICE - CHANGELOG

> **Status:** Active
> **Last Updated:** 2026-02-10

Todos los cambios notables en este microservicio serán documentados en este archivo.

## [Unreleased]
### Added
- Implementación del middleware `InternoCoreGlobalMiddleware` para estandarización de respuestas JSON.
- Sincronización de modelos `UserCompanyRole` con `MultiTenantBase`.
- Configuración de despliegue para AWS ECS y Docker Compose híbrido.
### Changed
- Se separó la validación de tokens en dos dependencias (`get_selection_payload`, `get_current_user_payload`) para manejar el flujo de autenticación en 2 fases.
- Se estandarizó la respuesta del endpoint `/select-company` para usar `ApiResponse`.
### Fixed
- Casting explícito a UUID en endpoints de autenticación para resolver conflictos de tipos.
- Normalización de llamadas a `UnauthorizedException` eliminando parámetros no soportados.

## [1.0.0] - 2026-02-10
### Initialized
- Creación inicial del servicio bajo la arquitectura Interno Core.
- Definición de modelos Core (`User`, `Company`, `Role`).
- Implementación de flujo de autenticación OAuth2 con JWT.