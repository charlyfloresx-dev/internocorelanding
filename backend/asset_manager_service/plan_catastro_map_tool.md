# Plan de Auditoría y Habilitación de Map-Tool (Catastro Tijuana)

Este plan de implementación está diseñado para verificar y habilitar la infraestructura backend existente en InternoCore, asegurando que la nueva aplicación "Map-Tool" en Vercel pueda consumir exitosamente los datos catastrales para la agente Indiana.

## Notas sobre tu feedback
* Has mencionado que `viatra-frontend` ya está en Vercel, por lo que usaremos esa configuración (`vercel.json`, dominios) como referencia para los CORS del backend.
* Mencionas `english-interview-trainer` y su Google Login. Si deseas que protejamos el endpoint de GIS usando Firebase/Google Auth en lugar de hacerlo público, por favor confírmalo para ajustar la auditoría de seguridad.

---

## 1. Auditoría del Endpoint (`GetPropertyDataByCoordinatesQuery`)
*   **Verificación**: Asegurar que el handler `GetPropertyDataByCoordinatesQuery` esté correctamente expuesto y conectado al router del `master_data_service` (`/v1/master-data/gis/identify` u otro).
*   **Contrato de Datos**: Validar que la respuesta JSON incluya los campos necesarios (Lote, Manzana, Nombre de Propietario).
*   **Seguridad**: (Pregunta abierta) ¿El endpoint debe requerir el token de Google (como en `english-interview-trainer`) o será público por ahora?

## 2. Validación de Extracción de Datos (`ArcGisTijuanaProvider`)
*   **FeatureServer Mapping**: Confirmar que los campos extraídos del payload de ArcGIS ('LOTE', 'MANZANA', 'CLAVE') sigan correspondiendo a la versión actual del servicio cartográfico del IMPLAN.
*   **Prueba de Fuego Predial**: Ejecutar un test usando la clave de prueba (ej. Venustiano Carranza 6319-C) para confirmar que `BeautifulSoup` y la lógica de `__VIEWSTATE` sigan logrando hacer bypass a la página del Ayuntamiento para obtener el nombre del propietario.

## 3. Habilitación de CORS para Vercel
*   **Modificar Configuración**: Agregar los orígenes permitidos. Basándonos en `viatra-frontend`, agregaremos `https://*.vercel.app` a la configuración base del backend (`int_backend_cors_origins`).
*   **Despliegue**: Asegurar que esta configuración de CORS sea funcional en la infraestructura de AWS.

## 4. Prueba End-to-End Local
*   **Petición cruda**: Lanzar una petición HTTP local simulando la que enviará el Map-Tool desde Vercel (inyectando Latitud y Longitud de Tijuana).
*   **Validación visual**: Inspeccionar el Payload JSON para confirmar que esté listo para consumirse en el frontend.
