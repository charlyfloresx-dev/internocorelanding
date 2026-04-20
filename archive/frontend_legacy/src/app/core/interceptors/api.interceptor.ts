import { HttpInterceptorFn, HttpResponse, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { tap } from 'rxjs';


export const apiInterceptor: HttpInterceptorFn = (req, next) => {
    // If you don't have a ToastService, you can use console.error or similar mechanism
    // For this generic template, we will assume a basic structure.

    return next(req).pipe(
        tap({
            next: (event) => {
                if (event instanceof HttpResponse) {
                    // Validation Only Strategy
                    // Check if the backend responded with a 200 OK but with status: "error" in the envelope
                    const body = event.body as any;
                    if (body && body.status === 'error') {
                        const errorMessage = body.message || 'Error occurred during API request';
                        console.error('[ApiInterceptor] Backend returned logic error:', errorMessage);
                        // You might want to show a toast here
                        throw new HttpErrorResponse({
                            error: body,
                            headers: event.headers,
                            status: event.status,
                            statusText: event.statusText,
                            url: event.url || req.url
                        });
                    }
                }
            },
            error: (error) => {
                // Here you can centralize error handling (e.g., showing generic toasts for 500 errors)
                console.error('[ApiInterceptor] HTTP Error:', error);
            }
        })
    );
};
