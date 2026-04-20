import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '@services/auth.service';

export const multiTenantInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);
    const context = authService.currentContext();
    const companyId = context?.companyId || authService.activeCompanyId();

    // Exclude login and select-company routes
    const isExcluded = req.url.includes('/auth/login') || req.url.includes('/auth/select-company');

    let headersConfig: { [header: string]: string } = {};

    if (companyId && !isExcluded) {
        headersConfig['x-company-id'] = companyId.toString().toLowerCase();
    }

    const tenantReq = req.clone({ setHeaders: headersConfig });

    return next(tenantReq);
};
