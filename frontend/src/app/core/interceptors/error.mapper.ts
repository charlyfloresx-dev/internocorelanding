/**
 * Mapea códigos de estado HTTP a mensajes amigables para el usuario.
 * Sincronizado con backend/common/exceptions.py
 */
export class ErrorMapper {
  static getUserMessage(status: number, backendMessage?: string): string {
    switch (status) {
      case 400: return backendMessage || 'Solicitud incorrecta. Verifique los datos enviados.';
      case 401: return 'Su sesión ha expirado. Por favor, inicie sesión nuevamente.';
      case 403: return 'Acceso denegado. No tiene permisos para realizar esta acción.';
      case 404: return 'El recurso solicitado no fue encontrado.';
      case 422: return backendMessage || 'No se pudo procesar la operación debido a una regla de negocio.';
      case 500: return 'Error interno del servidor. El equipo técnico ha sido notificado.';
      case 503: return 'El servicio no está disponible momentáneamente.';
      default: return backendMessage || 'Ocurrió un error inesperado de comunicación.';
    }
  }

  static shouldLogout(status: number): boolean {
    return status === 401;
  }
}