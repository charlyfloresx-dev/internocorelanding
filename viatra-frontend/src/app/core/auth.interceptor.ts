import { HttpInterceptorFn } from '@angular/common/http';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('access_token');
  const companyId = localStorage.getItem('company_id');

  let headers = req.headers;

  if (token && !req.headers.has('Authorization')) {
    headers = headers.set('Authorization', `Bearer ${token}`);
  }

  if (companyId) {
    headers = headers.set('X-Company-ID', companyId);
  }

  const authReq = req.clone({ headers });
  return next(authReq);
};
