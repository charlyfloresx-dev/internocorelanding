/**
 * Wrapper genérico para respuestas de la API.
 * Estandariza el formato de respuesta del backend Interno Core.
 */
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta?: {
    traceId: string;
    latency: number;
  };
}

/**
 * Estados permitidos para el ciclo de vida de un documento de producción.
 * DRAFT: Editable.
 * CONFIRMED: Inmutable, afecta inventario.
 * CANCELLED: Solo lectura, sin efecto.
 */
export type ProductionDocumentStatus = 'DRAFT' | 'CONFIRMED' | 'CANCELLED';

/**
 * DTO que representa un documento de producción (Orden de Trabajo, Lote, etc.).
 * Los campos siguen la convención camelCase en el frontend, mapeados desde snake_case del backend.
 */
export interface ProductionDocumentDto {
  /** Identificador único técnico (UUID) para ruteo y API */
  id: string;

  /** Número secuencial para auditoría y ordenamiento interno */
  sequenceNumber: number;

  /** Folio comercial legible para el usuario (ej: OP-2026-001) */
  folio: string;

  /** Estado actual del documento */
  status: ProductionDocumentStatus;

  /** Fecha de creación del registro (ISO 8601) */
  createdAt: string;

  /** Identificador del usuario que realizó la última actualización */
  updatedBy: string;
}