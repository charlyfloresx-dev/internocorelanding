# 📋 Reporte de Estado - InternoCore GIS Pipeline
**Fecha:** 23 de Abril de 2026
**Estatus:** ⚠️ Bloqueo por Consistencia de Datos / Infraestructura Operativa

## 🎯 Objetivo del Día
Industrializar el flujo de validación legal de predios en Tijuana, permitiendo que a partir de una coordenada GPS se obtenga: Clave Catastral, Superficie, Dirección Oficial y Nombre del Propietario Legal.

## 🛠️ Avances Técnicos (Lo "Bueno")
- **Infraestructura de Conexión**: Se implementó con éxito el bypass de seguridad SSL (`DEFAULT@SECLEVEL=1`) para conectar con los servidores obsoletos del Gobierno de B.C.
- **Proxy GeoServer**: Implementación de `ArcGisTijuanaProvider` con proyección de coordenadas EPSG:3857 y cálculo de BBOX dinámico.
- **Orquestación de Datos**: Creación del endpoint `/v1/master-data/gis/full-report` que unifica la respuesta de cartografía y registro público.
- **Análisis HAR**: Se capturó la estructura exacta de los payloads (`obtenerLotes`) y los headers necesarios (`X-Requested-With`, `Origin`) para simular peticiones legítimas.

## 🚧 Bloqueos y Fracasos (Lo "No Tan Bueno")
- **Opacidad del API RPPC**: A pesar de enviar el payload correcto identificado en el HAR, el endpoint `obtenerLotes` devuelve consistentemente `Datos: []` para claves válidas (ej. `PK020119`). Se sospecha de un requerimiento de sesión activa o tokens dinámicos no visibles en el JSON.
- **Inconsistencia de Cartografía (WMS)**: 
    *   El predio del recibo (**6319-C**) no aparece como polígono independiente en el WMS; el mapa devuelve claves colindantes (`PK020027` para el 6315 y `PK020028` para el 6317).
    *   Esto confirma que las unidades individuales (incisos) son "hijos" administrativos que no siempre tienen representación geométrica en la capa pública de IMPLAN.
- **Búsqueda por Nombre**: Las pruebas automatizadas por nombre (`MONTOYA LOPEZ HUMBERTO`) fallaron en el API directo, aunque el Sub-Agente encontró resultados parciales en la UI, indicando que el portal usa servicios distintos para la búsqueda por titular.

## 💡 Próximos Pasos (Pivot)
1. **Sesión Persistente**: Si se desea seguir con el API de `obtenerLotes`, el backend deberá implementar un flujo de login completo para obtener una cookie de sesión válida.
2. **Fallback a Portal de Pagos**: El portal de Predial Municipal suele ser más "amigable" para scraping rápido que el RPPC para obtener el nombre del dueño.
3. **Scan de Sub-cuentas**: Desarrollar un "brute-forcer" controlado que pruebe variantes de clave (ej. 029, 030, 119) cuando el WMS no sea preciso.

> [!WARNING]
> **Conclusión**: La tubería técnica (el código) es sólida y cumple con los estándares industriales, pero la **fuente de datos** (RPPC) es un "agujero negro" que requiere una llave de sesión o un método de acceso menos directo para ser 100% confiable.
