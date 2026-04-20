import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';
import { ApiResponse } from './models/api-response.model';

export interface SocialLoginRequest {
  token: string;
  provider: 'google' | 'facebook' | 'microsoft';
}

export interface CompanySelection {
  company_id: string;
  company_name: string;
  role_names: string[];
  is_new: boolean;
}

export interface CompanyAccessDto {
  selection_token: string;
  user_id: string;
  companies: CompanySelection[];
  is_new: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8001/api/v1/auth'; // Auth Microservice

  // Signal-based Session State
  public companyAccess = signal<CompanyAccessDto | null>(null);

  socialLogin(token: string, provider: 'google' | 'facebook' | 'microsoft') {
    const payload: SocialLoginRequest = { token, provider };
    return this.http.post<ApiResponse<CompanyAccessDto>>(`${this.apiUrl}/social-login`, payload).pipe(
      tap(response => {
        if (response.status === 'success') {
          this.companyAccess.set(response.data);
          // Store selection_token temporarily
          sessionStorage.setItem('selection_token', response.data.selection_token);
        }
      })
    );
  }

  selectCompany(companyId: string) {
    const token = sessionStorage.getItem('selection_token');
    return this.http.post<ApiResponse<any>>(
      `${this.apiUrl}/select-company`, 
      { company_id: companyId },
      { headers: { Authorization: `Bearer ${token}` } }
    ).pipe(
      tap(response => {
        if (response.status === 'success') {
          // Store permanent credentials
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('company_id', companyId);
          if (response.data.refresh_token) {
            localStorage.setItem('refresh_token', response.data.refresh_token);
          }
          // sessionStorage.removeItem('selection_token'); // Mantenemos el token para poder cambiar de empresa después
        }
      })
    );
  }
}

