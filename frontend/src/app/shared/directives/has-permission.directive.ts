import {Directive, inject, Input, TemplateRef, ViewContainerRef, effect} from '@angular/core';
import {AuthService} from '../../core/services/auth.service';

@Directive({
  selector: '[appHasPermission]',
  standalone: true
})
export class HasPermissionDirective {
  private authService = inject(AuthService);
  private templateRef = inject(TemplateRef<unknown>);
  private viewContainer = inject(ViewContainerRef);

  @Input('appHasPermission') permission!: string;

  constructor() {
    effect(() => {
      const permissions = this.authService.permissions();
      const roles = this.authService.roles();
      
      // Check if user has the specific permission or is an Admin
      const hasAccess = permissions.includes(this.permission) || 
                        roles.includes('Admin') || 
                        roles.includes('admin');

      this.viewContainer.clear();
      if (hasAccess) {
        this.viewContainer.createEmbeddedView(this.templateRef);
      }
    });
  }
}
