Seguridad.

Aquí tienes los prompts exactos para forzar esa validación, divididos en dos pasos: Auditoría Interna y Prueba de Estrés Lógica.

Paso 1: El Prompt de Auditoría de ADN
----------------------------------------
Reporte de Auditoría de Código Senior: Microservicio Auth-Service
Auditor: Senior Code Auditor
Fecha: [Fecha Actual]
Proyecto: InternoCore MES
Resumen Ejecutivo:
El código base es robusto y sigue gran parte de las directivas. Se detectaron 2 no conformidades críticas relacionadas con la estandarización de la respuesta de la API y la separación de responsabilidades (Clean Architecture), las cuales han sido corregidas en la versión final adjunta. El resto de los puntos cumplen con las especificaciones de alta fidelidad.
Análisis Detallado por Punto:
Async (CUMPLE): Positivo. La cadena de ejecución es completamente asíncrona. Desde los endpoints (async def) hasta las dependencias (get_db) y las llamadas a la base de datos (await db.execute(...)), se utiliza correctamente el paradigma async/await.
Multi-tenancy (CUMPLE): Positivo. El company_id se aplica correctamente a nivel de modelo mediante TenantBase y declared_attr. En las operaciones de escritura (ej: create_role), el company_id se obtiene del token del usuario autenticado, lo cual es seguro y previene la escritura de datos en un tenant incorrecto. La protección es efectiva a nivel de aplicación.
SQLAlchemy 2.0 (CUMPLE): Positivo. Se utiliza consistentemente la sintaxis select(...) de SQLAlchemy 2.0 para todas las consultas, abandonando por completo el API obsoleto de query(...).
Pydantic v2 (CUMPLE): Positivo. Los esquemas utilizan sintaxis moderna de Pydantic v2, específicamente from_attributes = True (en lugar de orm_mode) y la función Field para validaciones. No hay uso de métodos obsoletos.
Passwords (CUMPLE): Positivo. Se utiliza la librería passlib con el esquema bcrypt. Esta es la mejor práctica de la industria, ya que bcrypt es computacionalmente costoso y saltea las contraseñas automáticamente, ofreciendo una alta resistencia contra ataques de fuerza bruta y de diccionario.
Respuesta Estándar (FALLO CRÍTICO - CORREGIDO): No Conforme. Los endpoints de éxito retornaban el modelo Pydantic directamente, sin el wrapper estándar {status, data, message, meta}. Además, los errores de validación de FastAPI (422) no seguían el formato.
Acción Correctiva: Se implementó una función create_standard_response para encapsular todas las respuestas exitosas. Se añadió un manejador de excepciones específico para RequestValidationError (errores 422) para formatear los errores de validación de Pydantic según el estándar requerido. Ahora, el 100% de las respuestas HTTP (éxito y error) cumplen el formato.
JWT (CUMPLE): Positivo. El token JWT tiene una fecha de expiración (exp) y el payload (create_access_token en auth_handler.py) incluye correctamente los claims requeridos: sub (user_id), company_id y role.
DB Agnostic (CUMPLE): Positivo. El uso de la clase AgnosticUUID (TypeDecorator de SQLAlchemy) que se adapta al dialecto (PostgreSQL o MySQL) es una solución excelente y garantiza que los modelos funcionarán en ambos motores sin modificaciones.
Excepciones (CUMPLE): Positivo. El middleware global (global_exception_handler) captura de forma genérica cualquier excepción no controlada (ej: OperationalError si la base de datos está caída) y devuelve una respuesta JSON limpia con status 500 y el formato estándar, evitando cualquier fuga de tracebacks de Python al cliente.
Clean Architecture (FALLO - CORREGIDO): No Conforme. La lógica de consulta a la base de datos (select(...) y db.execute(...)) estaba directamente en los endpoints del router (api.py), violando la separación de capas. El router (capa de infraestructura) contenía lógica que pertenece a la capa de aplicación/servicio.
Acción Correctiva: Se creó un nuevo archivo app/services.py y se movió toda la lógica de negocio y acceso a datos (ej: authenticate_user, get_user_by_email, create_role) a esa capa. Los endpoints en api.py ahora son más limpios, delegando toda la operación a las funciones del servicio. La arquitectura ahora es más pura.
Conclusión:
Las no conformidades han sido resueltas. El código adjunto representa la versión final y auditada del microservicio Auth-Service, listo para su despliegue en el entorno de producción de InternoCore.
Procedo a entregar el artefacto corregido.
-------------------------------------------------------

Paso 2: El Prompt de "Prueba de Concepto Industrial"
Este es para validar que el sistema realmente sirve para la planta y no es solo una "app web" genérica:

"Ahora, simula una operación real en planta para validar la robustez:

Un operario intenta loguearse en una instalación On-Premise sin internet. ¿El Auth-Service funcionará localmente con MySQL?

Se intenta registrar un usuario con un correo que ya existe en OTRA empresa. Según el ADN de InternoCore, esto debe permitirse porque el usuario puede pertenecer a varias empresas. ¿Tu código lo permite o lanzará un error de 'Unique Constraint'?

El servidor de 12GB RAM recibe 50 peticiones simultáneas de escaneo de etiquetas. ¿Cómo maneja tu código el pool de conexiones para no saturar la base de datos?

Analiza estos escenarios y ajusta el código si es necesario."
----------------------------------------------
Análisis de Simulación de Operaciones en Planta
Escenario 1: Operación On-Premise (MySQL Offline)
Análisis: El sistema está preparado para este escenario. El diseño DB-agnóstico con el driver PyMySQL en requirements.txt y la configuración dinámica en database.py permite que el servicio funcione sin conexión a internet, siempre que la DATABASE_URL en el archivo .env apunte a la instancia local de MySQL.
Veredicto: CUMPLE. El ADN de InternoCore para instalaciones locales está intacto. No se requieren cambios.
Escenario 2: Email duplicado en diferentes empresas
Análisis: Ha detectado una no conformidad crítica. El modelo User actual tiene una restricción unique=True en la columna email. Esto impone una unicidad a nivel de toda la tabla, lo cual impediría que un operario (ej: operario@proveedor.com) pueda ser registrado en la Company_A y en la Company_B. Esto viola el requisito de negocio.
Veredicto: FALLO CRÍTICO. La restricción debe ser a nivel de (email, company_id).
Acción Correctiva: Se modificará el modelo User en app/models.py. Se eliminará el unique=True del campo email y se añadirá una UniqueConstraint a nivel de tabla para el par ('email', 'company_id'). Esto asegura que un email solo puede existir una vez por empresa.
Escenario 3: Concurrencia y Pool de Conexiones (50 peticiones)
Análisis: El código actual tiene valores fijos para el pool de conexiones (pool_size=20, max_overflow=10), permitiendo un máximo de 30 conexiones simultáneas. Al recibir 50 peticiones, las 20 peticiones restantes serían encoladas por SQLAlchemy, esperando que una conexión se libere. Esto es seguro (no satura la base de datos) pero no es óptimo y generará latencia. Un servidor de 12GB de RAM puede y debe manejar más conexiones. Para cumplir con el "ADN de Planta", estos parámetros deben ser tuneables por el ingeniero de despliegue.
Veredicto: FALLO DE OPTIMIZACIÓN. El sistema es resiliente pero no configurable para el hardware específico.
Acción Correctiva: Se parametrizarán el pool_size y max_overflow a través de variables de entorno. Se añadirán DB_POOL_SIZE y DB_MAX_OVERFLOW a app/core/config.py y .env.example, y app/database.py los leerá para configurar el motor de SQLAlchemy.
Conclusión de la Simulación:
Los escenarios de planta han revelado debilidades críticas en la lógica de negocio y en la configuración de rendimiento. Procedo a implementar las correcciones para alinear el Auth-Service con la realidad operativa de InternoCore.
-------------------------------------------------------
