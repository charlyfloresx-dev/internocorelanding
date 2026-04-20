import { Injectable, signal, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ApiSimulationService } from './api-simulation.service';
import { AuthService } from './auth.service';
import { ToastService } from './toast.service';

export interface OnboardingState {
  step: number;
  companyName: string;
  industry: string;
  employeesCount: string;
  modules: string[];
}

@Injectable({
  providedIn: 'root'
})
export class OnboardingService {
  private api = inject(ApiSimulationService);
  private auth = inject(AuthService);
  private router: Router = inject(Router);
  private toast = inject(ToastService);

  private initialState: OnboardingState = {
    step: 1,
    companyName: '',
    industry: '',
    employeesCount: '',
    modules: []
  };

  state = signal<OnboardingState>({ ...this.initialState });
  loading = signal(false);

  updateState(partial: Partial<OnboardingState>) {
    this.state.update(current => ({ ...current, ...partial }));
  }

  nextStep() {
    this.state.update(s => ({ ...s, step: s.step + 1 }));
  }

  prevStep() {
    this.state.update(s => ({ ...s, step: Math.max(1, s.step - 1) }));
  }

  reset() {
    this.state.set({ ...this.initialState });
  }

  // Final commit to backend
  submitOnboarding() {
    const companyId = this.auth.currentContext()?.companyId;
    if (!companyId) return;

    this.loading.set(true);

    this.api.completeOnboarding(companyId, this.state()).subscribe({
      next: (res) => {
        this.toast.success('Entorno configurado correctamente', 'Bienvenido');

        // Update local auth state to reflect is_new = false
        const currentAccesses = this.auth.availableAccesses();
        const updatedAccesses = currentAccesses.map(a => {
          if (String(a.company.id) === String(companyId)) {
            return { ...a, company: { ...a.company, is_new: false } };
          }
          return a;
        });

        this.auth.availableAccesses.set(updatedAccesses);

        this.loading.set(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.toast.error('No se pudo finalizar la configuración');
        this.loading.set(false);
      }
    });
  }
}