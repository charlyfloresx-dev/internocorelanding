/**
 * Standard ApiResponse wrapper for Interno Core Viatra Service.
 * Ensures consistent data unwrapping in all Angular services.
 */
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta?: {
    trace_id?: string;
    latency?: string;
    [key: string]: any;
  };
  code?: string | null;
}
