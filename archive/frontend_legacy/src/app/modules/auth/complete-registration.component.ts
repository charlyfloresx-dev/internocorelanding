import { Component, inject, signal, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { CompleteRegistrationPayload } from '@models/api.types';

@Component({
  selector: 'app-complete-registration',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="flex items-center justify-center min-h-screen bg-gray-100">
      <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <h2 class="text-2xl font-bold text-center text-gray-800">Completa tu Registro</h2>
        <p class="text-center text-gray-600">¡Bienvenido! Solo un paso más.</p>
        <form [formGroup]="completeForm" (ngSubmit)="onSubmit()" novalidate>
          <div class="space-y-4">
            <input formControlName="full_name" placeholder="Nombre Completo" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('full_name') }">
            <input formControlName="password" type="password" placeholder="Elige una Contraseña" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('password') }">
          </div>
          <button type="submit" [disabled]="loading()" class="w-full mt-6 btn-primary">
            <span class="indicator-label" *ngIf="!loading()">Completar Registro</span>
            <span class="indicator-progress" *ngIf="loading()">
                Finalizando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
            </span>
          </button>
        </form>
      </div>
    </div>
  `,
  styles: ['.input-field { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 0.375rem; }', '.btn-primary { background-color: #0A4F70; color: white; padding: 0.75rem; border-radius: 0.375rem; }']
})
export default class CompleteRegistrationComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private toast = inject(ToastService);

  loading = signal(false);
  registrationCode = signal<string | null>(null);

  completeForm: FormGroup = this.fb.group({
    full_name: ['', Validators.required],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  isControlInvalid(controlName: string): boolean {
    const control = this.completeForm.get(controlName);
    return !!control && control.invalid && (control.touched || control.dirty);
  }

  ngOnInit() {
    this.registrationCode.set(this.route.snapshot.queryParamMap.get('code'));
    if (!this.registrationCode()) {
      this.toast.error('Código de invitación no encontrado.');
      this.router.navigate(['/login']);
    }
  }

  onSubmit() {
    if (this.completeForm.invalid || !this.registrationCode()) { this.completeForm.markAllAsTouched(); return; }

    this.loading.set(true);
    const payload: CompleteRegistrationPayload = {
      code: this.registrationCode()!,
      full_name: this.completeForm.value.full_name!,
      password: this.completeForm.value.password!,
    };

    this.authService.completeRegistration(payload)?.subscribe({
      next: () => {
        this.toast.success('¡Registro completado! Bienvenido a Interno Core.');
        this.router.navigate(['/dashboard']);
      },
      error: (err: any) => {
        this.toast.error(err.error?.message || 'El código de invitación es inválido o ha expirado.');
        this.loading.set(false);
      }
    });
  }
}