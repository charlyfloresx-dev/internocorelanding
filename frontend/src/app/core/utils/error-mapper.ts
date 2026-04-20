// temp_future/src/app/core/utils/error-mapper.ts
import { HttpErrorResponse } from '@angular/common/http';

export interface IndustrialError {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
}

export class ErrorMapper {
  static map(error: HttpErrorResponse): IndustrialError {
    const status = error.status;
    const backendMessage = error.error?.message || error.error?.detail;

    switch (status) {
      case 401:
        return {
          title: 'SESIÓN EXPIRADA',
          message: 'Su token de seguridad no es válido o ha expirado. Re-autenticación requerida.',
          type: 'error'
        };
      case 403:
        return {
          title: 'ACCESO DENEGADO',
          message: 'No tiene permisos suficientes para este tenant o recurso.',
          type: 'error'
        };
      case 404:
        return {
          title: 'RECURSO NO ENCONTRADO',
          message: 'El Ledger o catálogo solicitado no existe en este nodo.',
          type: 'warning'
        };
      case 409:
        return {
          title: 'CONFLICTO DE IDEMPOTENCIA',
          message: 'La acción ya fue procesada o el código está duplicado. Solución: Refresca la página o cambia el código para reintentar.',
          type: 'warning'
        };
      case 422:
        return {
          title: 'VIOLACIÓN DE REGLA',
          message: backendMessage || 'Los datos no cumplen con la lógica de negocio industrial.',
          type: 'error'
        };
      case 500:
        return {
          title: 'FALLO CRÍTICO DE SISTEMA',
          message: 'Error interno en el microservicio. El equipo SRE ha sido alertado.',
          type: 'error'
        };
      case 0:
        return {
          title: 'FALLO DE CONECTIVIDAD',
          message: 'No se pudo establecer conexión con el backend. Verifique su red.',
          type: 'error'
        };
      default:
        return {
          title: 'ERROR INESPERADO',
          message: backendMessage || 'Ocurrió una anomalía no catalogada en la comunicación.',
          type: 'error'
        };
    }
  }
}
