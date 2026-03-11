import { Component, inject, signal } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { AuthService } from '@services/auth.service';
import { ToastService } from '@services/toast.service';
import { ForgotPasswordPayload } from '@models/api.types';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <!--begin::Authentication - Password reset -->
    <div class="d-flex flex-column flex-root">
      <div class="d-flex flex-column flex-column-fluid flex-lg-row">
        <div class="d-flex flex-center w-lg-50 pt-15 pt-lg-0 px-10">
          <div class="d-flex flex-center flex-lg-start flex-column">
            <a routerLink="/" class="mb-7">
              <img alt="Logo" src="./assets/media/logos/interno-logo-dark.svg" />
            </a>
            <h2 class="text-white fw-normal m-0">Modern, Efficient & Powerful MES</h2>
          </div>
        </div>
        <div class="d-flex flex-column-fluid flex-lg-row-auto justify-content-center justify-content-lg-end p-12 p-lg-20">
          <div class="bg-body d-flex flex-column flex-center rounded-4 w-md-600px p-10">
            <div class="d-flex flex-center flex-column flex-column-fluid px-lg-10 pb-15 pb-lg-20">
              <form class="form w-100" [formGroup]="forgotPasswordForm" (ngSubmit)="onSubmit()" novalidate>
                <div class="text-center mb-10">
                  <h1 class="text-dark fw-bolder mb-3">¿Olvidaste tu Contraseña?</h1>
                  <div class="text-gray-500 fw-semibold fs-6">Ingresa tu email para resetear la contraseña.</div>
                </div>
                <div class="fv-row mb-8">
                  <input type="email" placeholder="Email" formControlName="email" class="form-control bg-transparent" [ngClass]="{ 'is-invalid': isControlInvalid('email') }" />
                </div>
                <div class="d-flex flex-wrap justify-content-center pb-lg-0">
                  <button type="submit" class="btn btn-primary me-4" [disabled]="loading() || forgotPasswordForm.invalid">
                    <span class="indicator-label" *ngIf="!loading()">Enviar</span>
                    <span class="indicator-progress" *ngIf="loading()">
                      Por favor espera...
                      <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
                    </span>
                  </button>
                  <a routerLink="/login" class="btn btn-light">
                    <i class="ki-filled ki-arrow-left"></i>
                    Cancelar
                  </a>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!--end::Authentication - Password reset -->
  `
})
export default class ForgotPasswordComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private toast = inject(ToastService);

  loading = signal(false);
  forgotPasswordForm: FormGroup = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
  });

  isControlInvalid(controlName: string): boolean {
    const control = this.forgotPasswordForm.get(controlName);
    return !!control && control.invalid && (control.touched || control.dirty);
  }

  onSubmit() {
    if (this.forgotPasswordForm.invalid) {
      this.forgotPasswordForm.markAllAsTouched();
      return;
    }
    this.loading.set(true);
    const payload = this.forgotPasswordForm.value as ForgotPasswordPayload;
    this.authService.forgotPassword(payload).subscribe({
      next: () => {
        this.toast.success('Si el email está registrado, recibirás un enlace para recuperar tu contraseña.');
        this.loading.set(false);
      },
      error: (err) => {
        this.toast.error('Ocurrió un error. Por favor, intenta de nuevo.');
        this.loading.set(false);
      }
    });
  }
}