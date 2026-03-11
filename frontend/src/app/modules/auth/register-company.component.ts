import { Component, inject, signal } from '@angular/core';
import { Router, RouterModule } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { AuthService } from '@services/auth.service';
import { ToastService } from '@services/toast.service';
import { RegisterCompanyPayload } from '@models/api.types';

@Component({
  selector: 'app-register-company',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  template: `
    <div class="flex items-center justify-center min-h-screen bg-gray-100">
      <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <h2 class="text-2xl font-bold text-center text-gray-800">Registrar Nueva Empresa</h2>
        <form [formGroup]="registerForm" (ngSubmit)="onSubmit()" novalidate>
          <div class="space-y-4">
            <input formControlName="company_name" placeholder="Nombre de la Empresa" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('company_name') }">
            <input formControlName="tax_id" placeholder="RUC / Tax ID" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('tax_id') }">
            <input formControlName="admin_email" type="email" placeholder="Email del Administrador" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('admin_email') }">
            <input formControlName="password" type="password" placeholder="Contraseña" class="input-field" [ngClass]="{ 'is-invalid': isControlInvalid('password') }">
          </div>
          <button type="submit" [disabled]="loading() || registerForm.invalid" class="w-full mt-6 btn-primary">
            <span class="indicator-label" *ngIf="!loading()">Crear Cuenta</span>
            <span class="indicator-progress" *ngIf="loading()">
              Registrando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span>
            </span>
          </button>
        </form>
        <div class="text-center">
          <a routerLink="/login" class="text-sm text-primary-600 hover:underline">¿Ya tienes una cuenta? Inicia Sesión</a>
        </div>
      </div>
    </div>
  `,
  styles: ['.input-field { width: 100%; padding: 0.75rem; border: 1px solid #ccc; border-radius: 0.375rem; }', '.btn-primary { background-color: #0A4F70; color: white; padding: 0.75rem; border-radius: 0.375rem; }']
})
export default class RegisterCompanyComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private toast = inject(ToastService);

  loading = signal(false);
  registerForm: FormGroup = this.fb.group({
    company_name: ['', Validators.required],
    tax_id: ['', Validators.required],
    admin_email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]],
  });

  isControlInvalid(controlName: string): boolean {
    const control = this.registerForm.get(controlName);
    return !!control && control.invalid && (control.touched || control.dirty);
  }

  onSubmit() {
    if (this.registerForm.invalid) { this.registerForm.markAllAsTouched(); return; }

    this.loading.set(true);
    this.authService.registerCompany(this.registerForm.value as RegisterCompanyPayload).subscribe({
      next: () => {
        this.toast.success('Empresa registrada y sesión iniciada con éxito.');
        this.router.navigate(['/dashboard']); // Redirigir al dashboard tras el registro y auto-login
      },
      error: (err) => {
        console.error('Error al registrar la empresa:', err);
        this.toast.error(err.error?.message || 'Error al registrar la empresa. Inténtalo de nuevo.');
        this.loading.set(false);
      },
      complete: () => {
        this.loading.set(false);
      }
    });
  }
}