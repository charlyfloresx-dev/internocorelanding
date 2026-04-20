import { Component, OnInit, inject, signal, effect, afterNextRender } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '../../core/auth.service';
import { ToastrService } from 'ngx-toastr';

declare var google: any;

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit {
  private authService = inject(AuthService);
  private router = inject(Router);
  private toastr = inject(ToastrService);

  isSelectingCompany = signal(false);
  availableCompanies = signal<any[]>([]);
  isNewUser = signal(false);

  constructor() {
    // Reactive Effect to handle company selection step
    effect(() => {
      const access = this.authService.companyAccess();
      if (access) {
        if (access.is_new) this.isNewUser.set(true);
        
        if (access.companies.length > 0) {
          this.isSelectingCompany.set(true);
          this.availableCompanies.set(access.companies);
          
          // Auto-select if only 1 company (Standard for Traveler accounts)
          // But only if they are not explicitly "NEW" and waiting for roles
          if (access.companies.length === 1 && !access.is_new) {
            this.selectCompany(access.companies[0].company_id);
          }
        }
      }
    });

    // Modern Angular 19 DOM access
    afterNextRender(() => {
      this.initGoogleAuth();
    });
  }

  ngOnInit() {}

  private initGoogleAuth() {
    if (typeof google === 'undefined') {
      setTimeout(() => this.initGoogleAuth(), 300);
      return;
    }

    const btn = document.getElementById('google-btn');
    if (!btn) return;

    google.accounts.id.initialize({
      client_id: '865711103072-o4gj37pbf6o7umphbv0fti6l9d4i0a6r.apps.googleusercontent.com',
      callback: this.handleGoogleCredentialResponse.bind(this),
      auto_select: false,
      cancel_on_tap_outside: true
    });

    google.accounts.id.renderButton(
      btn,
      { theme: 'filled_black', size: 'large', width: '380px', shape: 'pill' }
    );
  }

  private handleGoogleCredentialResponse(response: any) {
    if (response.credential) {
      this.authService.socialLogin(response.credential, 'google').subscribe({
        next: (res) => {
          if (res.data.is_new) {
            this.toastr.info('¡Bienvenido! Tu cuenta ha sido creada. Un administrador te asignará roles pronto.', 'Registro Exitoso');
          }
        },
        error: (err) => console.error('Social Login Error:', err)
      });
    }
  }

  selectCompany(companyId: string) {
    this.authService.selectCompany(companyId).subscribe({
      next: () => {
        this.router.navigate(['/dashboard']);
      },
      error: (err) => console.error('Select Company Error:', err)
    });
  }
}


