# Documentación del Issue
## Consumo inesperado de Google Cloud Billing por uso de agentes (Gemini API)

---

## 1. Resumen ejecutivo

Durante el desarrollo del proyecto **InternoCore**, se detectó un consumo inesperado en la cuenta de facturación de **Google Cloud**, asociado al uso de la **Generative Language API (Gemini)** desde entornos de desarrollo (Visual Studio Code con agentes de IA). El consumo no fue provocado por usuarios finales ni por lógica productiva del sistema, sino por **llamadas automáticas realizadas por agentes de desarrollo**, principalmente mediante funciones de *auto-complete* y ejecución en segundo plano.

El incidente generó un cargo aproximado de **MX$20.82**, lo cual motivó una revisión completa de la arquitectura, configuración de credenciales y prácticas de uso de IA durante el desarrollo.

---

## 2. Contexto del sistema

- **Proyecto**: InternoCore
- **Tipo**: Sistema SaaS para control de inventarios, manufactura y procesos operativos
- **Fase**: Desarrollo (DEV)
- **Tecnología involucrada**:
  - Google Cloud Platform (GCP)
  - Generative Language API (Gemini)
  - Visual Studio Code con extensiones de agentes de IA

El sistema aún **no se encontraba en producción**, y no existía tráfico de usuarios finales.

---

## 3. Descripción del incidente

### 3.1 Qué ocurrió

- Se observó un incremento inesperado en el **Billing Report** de Google Cloud.
- El reporte mostró **82 requests** a la *Generative Language API* en un periodo corto.
- El consumo ocurrió sin interacción directa consciente del desarrollador.

### 3.2 Evidencia

- Servicio afectado: **Generative Language API**
- Requests: 82
- Errores: ~7% (reintentos automáticos)
- Costo total: **MX$20.82**
- Periodo: Enero 2026

---

## 4. Causa raíz (Root Cause Analysis)

### 4.1 Causa principal

El consumo fue provocado por **agentes de IA activos en Visual Studio Code**, los cuales:

- Ejecutaban llamadas automáticas a la API para:
  - Autocompletado
  - Sugerencias en línea (*inline suggestions*)
  - Análisis de contexto del proyecto
- Operaban en **background**, incluso sin prompts explícitos
- Reenviaban contexto amplio (archivos, historial, system prompts)

### 4.2 Qué NO fue la causa

- ❌ No fue tráfico de usuarios finales
- ❌ No fue lógica productiva del backend
- ❌ No fue una fuga de seguridad
- ❌ No fue un error de facturación de Google

---

## 5. Concepto clave aprendido

### "Los agentes ayudan a escribir código, NO a correr lógica productiva"

Esto significa que:

- Los **agentes de IA en el IDE** deben usarse únicamente como:
  - Asistentes de programación
  - Generadores de código
  - Apoyo en diseño o documentación

- **No deben**:
  - Ejecutar flujos de negocio
  - Estar conectados directamente al entorno productivo
  - Consumir APIs pagadas de forma permanente

La lógica productiva (IA usada por el sistema) debe ejecutarse **únicamente desde el backend**, bajo control estricto de autenticación, rate limiting y monitoreo.

---

## 6. Impacto

### 6.1 Impacto técnico

- Consumo innecesario de recursos
- Falta de visibilidad inicial del origen del tráfico

### 6.2 Impacto económico

- Cargo menor (MX$20.82), pero con alto valor educativo
- Riesgo potencial alto si no se detecta a tiempo en proyectos más grandes

---

## 7. Acciones correctivas inmediatas

- Cierre de la cuenta de facturación
- Deshabilitación de la Generative Language API
- Eliminación de API Keys
- Desactivación de extensiones de IA en VS Code
- Limpieza de variables de entorno

---

## 8. Acciones preventivas implementadas

### 8.1 Arquitectura

- Separación estricta entre:
  - **Entorno de desarrollo (DEV)**
  - **Entorno productivo (PROD)**

### 8.2 Seguridad

- API Keys restringidas por IP y servicio
- Uso exclusivo de IA desde backend

### 8.3 Control de costos

- Presupuestos (Budgets) con alertas
- Límite de tokens por request
- Kill switch para IA (`AI_ENABLED=false`)

---

## 9. Lecciones aprendidas (para tesis)

1. El uso de IA en desarrollo puede generar costos reales, incluso sin despliegue productivo.
2. Los agentes de programación deben tratarse como **herramientas temporales**, no como servicios persistentes.
3. La ausencia de límites explícitos (tokens, rate, budget) es un riesgo financiero.
4. La arquitectura segura no solo protege datos, también protege costos.
5. Un incidente pequeño en DEV puede prevenir fallas críticas en PROD.

---

## 10. Conclusión

El incidente de billing en Google Cloud no representó una falla grave, sino un **evento formativo clave** que permitió establecer una arquitectura más robusta, segura y controlada para el uso de inteligencia artificial en InternoCore. Esta experiencia refuerza la importancia de diseñar sistemas considerando no solo funcionalidad, sino también **gobernanza de costos y uso responsable de IA**.

---

**Documento preparado para fines académicos y técnicos (tesis / memoria de proyecto).**

