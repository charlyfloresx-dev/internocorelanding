import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { ToastrService } from 'ngx-toastr';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

export const globalErrorInterceptor: HttpInterceptorFn = (req, next) => {
  const toastr = inject(ToastrService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An unexpected error occurred';
      
      if (error.error instanceof ErrorEvent) {
        // Client-side error
        errorMessage = `Error: ${error.error.message}`;
      } else {
        // Server-side error
        // Extract message from Interno Core standard response {status, message, data}
        if (error.error && error.error.message) {
          errorMessage = error.error.message;
        } else {
          errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
        }
      }

      // Special Handling for Middleware Errors (e.g. Header missing)
      if (error.status === 400 || error.status === 401 || error.status === 403) {
        toastr.error(errorMessage, 'Auth & Security', {
          timeOut: 5000,
          progressBar: true,
          closeButton: true,
          enableHtml: true
        });
      } else {
        toastr.error(errorMessage, 'System Error');
      }

      console.error('Global Error Interceptor:', error);
      return throwError(() => error);
    })
  );
};
