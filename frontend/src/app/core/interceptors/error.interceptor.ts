// temp_future/src/app/core/interceptors/error.interceptor.ts
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { ToastService } from '../services/toast.service';
import { catchError, throwError } from 'rxjs';
import { ErrorMapper } from '../utils/error-mapper';
import { TranslationService } from '../services/translation.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const toast = inject(ToastService);
  const translate = inject(TranslationService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Ignore silence-intended requests
      if (req.headers.has('X-Silent-Error')) {
        return throwError(() => error);
      }

      const mapped = ErrorMapper.map(error);
      const translatedTitle = translate.translate(mapped.title, mapped.title);
      const translatedMessage = translate.translate(mapped.message, mapped.message);

      // Append trace_id to the UI if available for support
      let finalMessage = translatedMessage;
      if (mapped.trace_id) {
        finalMessage += ` (Trace: ${mapped.trace_id.split('-')[0]})`;
      }

      toast.show(finalMessage, mapped.type, translatedTitle);

      return throwError(() => error);
    })
  );
};
