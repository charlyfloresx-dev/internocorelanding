import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';

export interface Department {
  id: string;
  company_id: string;
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
}

export interface DepartmentCreate {
  name: string;
  code: string;
  description?: string | null;
  is_active: boolean;
}

export interface DepartmentUpdate {
  name?: string;
  code?: string;
  description?: string | null;
  is_active?: boolean;
}

@Injectable({ providedIn: 'root' })
export class DepartmentService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  departments = signal<Department[]>([]);
  loading = signal(false);
  saving = signal(false);

  private get baseUrl(): string {
    return `${environment.hrUrl}/hcm/departments`;
  }

  load(activeOnly?: boolean) {
    this.loading.set(true);
    const params: Record<string, string> = { limit: '100' };
    if (activeOnly !== undefined) params['is_active'] = String(activeOnly);

    this.http.get<any>(`${this.baseUrl}/`, { params }).subscribe({
      next: (res) => {
        this.departments.set(res.data ?? []);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  create(payload: DepartmentCreate) {
    this.saving.set(true);
    return this.http.post<any>(`${this.baseUrl}/`, payload);
  }

  update(id: string, payload: DepartmentUpdate) {
    this.saving.set(true);
    return this.http.patch<any>(`${this.baseUrl}/${id}`, payload);
  }

  deactivate(id: string) {
    return this.http.delete<any>(`${this.baseUrl}/${id}`);
  }
}
