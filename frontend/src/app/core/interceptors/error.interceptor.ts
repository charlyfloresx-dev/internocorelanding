// temp_future/src/app/core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { ToastService } from '../services/toast.service';
import { catchError, throwError } from 'rxjs';
import { ErrorMapper } from '../utils/error-mapper';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Ignore silence-intended requests
      if (req.headers.has('X-Silent-Error')) {
        return throwError(() => error);
      }

      const mapped = ErrorMapper.map(error);
      toast.show(mapped.message, mapped.type, mapped.title);

      return throwError(() => error);
    })
  );
};
