
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { ToastComponent } from '@shared/components/toast.component';
import { ErrorStateService } from '@services/error-state.service';
import { DiagnosticLogService } from '@services/diagnostic-log.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, ToastComponent],
  templateUrl: './app.component.html'
})
export class AppComponent {
  errorService = inject(ErrorStateService);
  diagService = inject(DiagnosticLogService);
}
