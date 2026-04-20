
import { ErrorHandler, Injectable, Injector, NgZone } from '@angular/core';
import { ErrorStateService } from '@services/error-state.service';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  constructor(private injector: Injector, private zone: NgZone) {}

  handleError(error: any): void {
    console.error('CRITICAL APP ERROR:', error);
    
    // Get service lazily to avoid circular dependency during app init
    const service = this.injector.get(ErrorStateService);
    
    // Extract message
    const message = error.message ? error.message : error.toString();

    // Run inside Angular Zone to ensure UI updates
    this.zone.run(() => {
        service.triggerError(message);
    });
  }
}
