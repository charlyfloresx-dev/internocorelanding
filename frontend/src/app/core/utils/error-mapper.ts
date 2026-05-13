// temp_future/src/app/core/utils/error-mapper.ts
import { HttpErrorResponse } from '@angular/common/http';
import { ApiResponse } from '../models/domain.types';

export interface IndustrialError {
  title: string;
  message: string;
  type: 'error' | 'warning' | 'info';
  code?: string;
  details?: any;
  trace_id?: string;
}

export class ErrorMapper {
  static map(error: HttpErrorResponse): IndustrialError {
    const status = error.status;
    const backendData = error.error as ApiResponse<any> | undefined;
    const backendMessage = backendData?.message || error.error?.detail;
    const meta = backendData?.meta || {};
    const code = meta.code;
    const traceId = meta.trace_id;
    const details = meta.details;

    // 1. Semantic Error Mapping (Based on Backend 'code')
    if (code) {
      switch (code) {
        case 'INSUFFICIENT_STOCK':
        case 'QUOTA_EXCEEDED':
        case 'RESTRICTED_ACCESS':
        case 'NOT_FOUND':
        case 'VALIDATION_ERROR':
        case 'BUSINESS_RULE_VIOLATION':
          return {
            title: `errors.${code}.title`,
            message: backendMessage || `errors.${code}.message`,
            type: (code === 'INSUFFICIENT_STOCK' || code === 'VALIDATION_ERROR') ? 'error' : 'warning',
            code,
            details,
            trace_id: traceId
          };
        default:
          break; // Fallback to HTTP status mapping if not explicitly mapped above
      }
    }

    // 2. HTTP Status Fallback Mapping
    let industrialError: IndustrialError;
    const statusKey = `errors.status.${status}`;
    const defaultKey = `errors.status.default`;

    switch (status) {
      case 401:
      case 402:
      case 403:
      case 422:
      case 500:
      case 0:
        industrialError = {
          title: `${statusKey}.title`,
          message: backendMessage || `${statusKey}.message`,
          type: 'error'
        };
        break;
      case 404:
      case 409:
        industrialError = {
          title: `${statusKey}.title`,
          message: backendMessage || `${statusKey}.message`,
          type: 'warning'
        };
        break;
      default:
        industrialError = {
          title: `${defaultKey}.title`,
          message: backendMessage || `${defaultKey}.message`,
          type: 'error'
        };
    }

    // Inject backend context if available
    industrialError.code = code || industrialError.code;
    industrialError.details = details || industrialError.details;
    industrialError.trace_id = traceId || industrialError.trace_id;

    if (code && !industrialError.message.includes('0.message')) {
        industrialError.message = backendMessage || industrialError.message;
    }

    return industrialError;
  }
}
