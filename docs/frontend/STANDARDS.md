# 🎨 Estándares de Desarrollo Frontend - Interno Core

> SSOT para el desarrollo de la interfaz de usuario en Angular 19+.

## 1. Reactividad con Angular Signals
Toda la gestión de estado local y comunicación entre componentes debe realizarse mediante **Signals**. 
- Usar `signal()` para estado mutable.
- Usar `computed()` para derivar valores de forma eficiente.
- Evitar `BehaviorSubject` a menos que sea estrictamente necesario para interoperabilidad con librerías legacy.

## 2. Búsquedas y Typeahead (Protocolo Industrial)
Para prevenir el "parpadeo" de la UI y el desperdicio de recursos del backend, todo componente de búsqueda (Search/Autocomplete) debe implementar obligatoriamente operadores de RxJS:

```typescript
// Patrón Obligatorio en Services/Components
this.searchSubject.pipe(
  debounceTime(300),          // Espera a que el usuario deje de escribir
  distinctUntilChanged(),     // No repite búsquedas idénticas
  switchMap(query => {
    if (query.length < 3) return of([]);
    return this.apiService.search(query); // Cancela la petición anterior automáticamente
  })
).subscribe(results => this.results.set(results));
```

- **Debounce:** Mínimo 300ms.
- **SwitchMap:** Obligatorio para cancelar peticiones en vuelo si el usuario sigue tecleando.

## 3. Carga Resiliente de Catálogos
Cuando una vista depende de múltiples catálogos (ej: Categorías, Marcas, Unidades), usar `forkJoin` para sincronizar la carga y evitar estados de UI inconsistentes.

```typescript
forkJoin({
  categories: this.masterData.getCategories(),
  brands: this.masterData.getBrands(),
  uoms: this.masterData.getUoms()
}).pipe(
  catchError(err => {
    this.toast.error('Error cargando catálogos críticos');
    return throwError(() => err);
  })
).subscribe(data => {
  this.categories.set(data.categories);
  // ...
});
```

Todos los interceptores deben asegurar la propagación del `X-Correlation-ID` (UUID v4) generado en el cliente hacia el backend. Este ID debe ser mostrado en los tooltips de error o auditoría para facilitar el debugging en producción.

## 5. Respuestas de API (ApiResponse Wrapping & Double Wrapping)
El middleware global de Python empaqueta transacciones exitosas y errores usando la clase `ApiResponse`:
```json
{
  "status": "success",
  "data": [...],
  "message": "Operación completada",
  "meta": { "trace_id": "...", "latency": "0.012s" }
}
```

**Problema del Doble Empaquetamiento:**
A veces el backend ya devuelve un `ApiResponse` y el middleware lo envuelve *de nuevo* si detecta un JSON puro. O a veces los microservicios se comunican y ocurre un doble `.data.data`.

**Solución (Directriz Obligatoria):**
Todo método HTTP GET/POST en el FrontEnd que consuma listados **DEBE usar una sanitización defensiva recursiva** antes de asignarlo a un Array o Signal, para evitar fallas silenciosas donde la tabla desaparece porque el `data` esperaba un Array y recibió otro Objeto con una propiedad `data`.

```typescript
// ✅ Patrón Correcto de Desenvoltura Defensiva:
private async safeGet<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await lastValueFrom(this.http.get<ApiResponse<T>>(url));
    
    // 1er Nivel (Wrapper del Http Client)
    if (res?.status === 'success' && res?.data != null) {
      // 2do Nivel (Doble wrapper ocasional del Middleware)
      let items = Array.isArray(res.data) ? res.data : ((res.data as any)?.data || res.data);
      return Array.isArray(items) ? items : fallback;
    }
    
    // Fallback recursivo...
    if (res && typeof res === 'object' && 'data' in (res as any)) {
      let extract = (res as any).data;
      return Array.isArray(extract) ? extract : (extract?.data || fallback);
    }
    
    return fallback;
  } catch (e: any) {
    console.error(`[HTTP] Error en ${url}:`, e);
    return fallback;
  }
}
```
