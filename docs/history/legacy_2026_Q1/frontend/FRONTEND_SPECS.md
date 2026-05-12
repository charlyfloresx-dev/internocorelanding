# 💻 InternoCore: Especificaciones Técnicas (Frontend)

## 1. Patrones de Desarrollo y Performance

### Uso Obligatorio de RxJS para Typeahead (Live Search)
Queda estrictamente establecido el uso de **RxJS (`debounceTime`, `switchMap`, `distinctUntilChanged`)** para cualquier componente de búsqueda en vivo, autocompletado, o escáner que dispare peticiones al backend (ej. `ItemSearchComponent`).

**Motivo:**
1. Prevenir la saturación de los microservicios de backend disparando queries por cada pulsación de tecla.
2. Evitar "Race Conditions" donde la respuesta de una consulta vieja sobreescribe en la UI a una más reciente.

**Implementación Estándar:**
Se debe utilizar un `Subject<string>` alimentado por el signal de Angular. Las peticiones a servicios (`InventoryService`, `MasterDataService`) deben envolverse en llamadas reactivas y manejar los errores internamente para no romper la suscripción.
