# mes_service - Manufacturing Execution System

Este microservicio se encarga de la captura de datos de piso, registro de labor, gestión de paros (downtime) y generación de KPIs de producción (OEE) en tiempo real.

## 🏗️ Arquitectura
Sigue el estándar de Clean Architecture y Multitenancy de Interno Core.

## 🚀 Inicio Rápido
1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar con uvicorn: `uvicorn app.main:app --reload --port 8003`

## 📚 Documentación
- `MES_CORE.md`: Blueprint de construcción y reglas de negocio.
- `CONTEXTO.md`: Visión del negocio.
- `ARCHITECTURAL_LOG.md`: Bitácora de decisiones técnicas.
