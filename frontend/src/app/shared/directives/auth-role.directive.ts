// temp_future/src/app/shared/directives/auth-role.directive.ts
import { Directive, Input, TemplateRef, ViewContainerRef, inject, effect } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';

/**
 * Usage: <div *authRole="['ADMIN', 'OPERATOR']">...</div>
 */
@Directive({
  selector: '[authRole]',
  standalone: true
})
export class AuthRoleDirective {
  private auth = inject(AuthService);
  private templateRef = inject(TemplateRef<any>);
  private viewContainer = inject(ViewContainerRef);

  @Input('authRole') requiredRoles: string[] = [];

  constructor() {
    // React to session changes using signals
    effect(() => {
      const userRoles = this.auth.session()?.roles || [];
      const hasPermission = this.requiredRoles.length === 0 || 
                          this.requiredRoles.some(role => userRoles.includes(role));

      this.viewContainer.clear();
      if (hasPermission) {
        this.viewContainer.createEmbeddedView(this.templateRef);
      }
    });
  }
}
