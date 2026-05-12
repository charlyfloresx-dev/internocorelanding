# 🛠️ Centro de Automatización y Diagnóstico (backend/scripts/)

Esta carpeta es el "cuarto de herramientas" del backend. Contiene scripts críticos para el mantenimiento de la integridad del sistema, sembrado de datos industriales y automatización de procesos en la nube.

## 📊 1. Auditoría y Cumplimiento (Compliance)
Scripts diseñados para validar que el sistema cumple con los invariantes arquitectónicos.
- **`generate_code_graph.py`**: El script maestro de auditoría. Genera el grafo de dependencias y valida el cumplimiento del paywall y seguridad.
- **`validate_muro_hierro.py`**: Verifica que las políticas de aislamiento multi-tenant estén activas en todos los endpoints.
- **`audit_*.py`**: Conjunto de validadores específicos para WMS, Suscripciones e Identidad.

## 🌱 2. Sembrado Industrial (Seeding)
Herramientas para poblar la base de datos con escenarios de negocio complejos.
- **`unified_industrial_seed.py`**: El sembrado atómico maestro que inicializa empresas, productos, almacenes y usuarios en una sola ejecución.
- **`master_seed.py`**: Versión orquestada para sembrado multi-servicio.
- **`seed_*.py`**: Sembrados granulares para partners, tickets y aduanas.

## 🏭 3. Simulaciones y Demos
Scripts que emulan el comportamiento de una planta industrial o un flujo de venta masivo.
- **`simulate_liquor_distro.py`**: Simulación de distribución y logística de licores.
- **`simulate_mes.py`**: Emulación de señales de máquinas en piso de producción.
- **`kiosk_demo.py`**: Guion de prueba para la interfaz de kiosco.

## ☁️ 4. Operaciones Cloud (DevOps)
Automatización para la infraestructura de AWS.
- **`aws_full_nuke.ps1`**: Script de pánico para eliminar todos los recursos cloud y llevar el costo a $0.
- **`automated-ecr-push.sh`**: Orquestador para subir imágenes de Docker a AWS ECR.
- **`redeploy_internocore_aws.ps1`**: Redespacho completo del entorno cloud.

## 🛠️ 5. Utilidades de Desarrollo
- **`gen_alembic.py`**: Automatización de migraciones de base de datos.
- **`cleanup_root_pollution.py`**: Mantenimiento de limpieza de la raíz del proyecto.
- **`check_db_monolith.py`**: Validador de consistencia de la base de datos unificada.

---
**Nota de Higiene:** Por favor, mantenga esta carpeta libre de archivos personales o binarios no relacionados con la ejecución del backend (ej. PDFs, capturas de pantalla).
