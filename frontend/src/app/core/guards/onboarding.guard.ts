import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '@services/auth.service';

export const onboardingGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    // 1. Must be authenticated
    if (!authService.isAuthenticated()) {
        router.navigate(['/login']);
        return false;
    }

    // 2. Must be a "new" company context
    const company = authService.activeCompany();
    if (company?.is_new) {
        return true;
    }

    // 3. If not new, send to dashboard
    router.navigate(['/dashboard']);
    return false;
};
