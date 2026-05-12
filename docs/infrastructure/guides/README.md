# Infraestructura de Interno Core

## Estado Actual: Local-First (Fase 97+)
Desde el 21 de abril de 2026, la infraestructura de AWS ha sido desmantelada para optimizar costos. El sistema opera como un **Monolito Unificado** en entornos locales/on-premise.

## Directorios
- `/backup_configs`: Contiene el ADN técnico (VPC, IAM, S3 Config) extraído antes del cierre de AWS.
- `/scripts`: Herramientas de automatización para limpieza y eventual redespacho.

## Seguridad
- No se permiten archivos de credenciales (`.csv`, `.pem`) en esta carpeta.
- Todo secreto debe gestionarse mediante variables de entorno locales.
