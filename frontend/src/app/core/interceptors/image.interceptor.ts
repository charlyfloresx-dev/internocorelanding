import { HttpInterceptorFn, HttpResponse } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

/**
 * ImageInterceptor
 * Analiza las respuestas del backend buscando campos photo_path o profile_url.
 * Si la ruta es relativa, la transforma en absoluta usando environment.assetsUrl.
 */
export const imageInterceptor: HttpInterceptorFn = (req, next) => {
  return next(req).pipe(
    map(event => {
      if (event instanceof HttpResponse && event.body) {
        // Realizar una copia profunda si es necesario para mutar, 
        // o mutar directamente si el backend envía objetos planos.
        if (typeof event.body === 'object') {
            normalizeImages(event.body);
        }
      }
      return event;
    })
  );
};

function normalizeImages(obj: any): void {
  if (typeof obj !== 'object' || obj === null) return;

  if (Array.isArray(obj)) {
    obj.forEach(item => normalizeImages(item));
  } else {
    for (const key in obj) {
      // Campos a normalizar
      if (key === 'photo_path' || key === 'profile_url') {
        const val = obj[key];
        if (val && typeof val === 'string' && val.length > 0) {
            // Solo normalizar si es una ruta relativa (no empieza con http/https)
            if (!val.startsWith('http://') && !val.startsWith('https://')) {
                // Limpiar barras iniciales y concatenar
                const cleanPath = val.replace(/^\/+/, '');
                obj[key] = `${environment.assetsUrl}/${cleanPath}`;
            }
        }
      } else if (typeof obj[key] === 'object') {
        // Recursión para objetos anidados o listas de objetos
        normalizeImages(obj[key]);
      }
    }
  }
}
