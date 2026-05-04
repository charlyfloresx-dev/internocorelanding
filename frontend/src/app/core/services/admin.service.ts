import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {ApiResponse} from '../models/api.types';
import {environment} from '../../../environments/environment';

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  role_name: string;
  status: 'active' | 'inactive' | 'invited';
  created_at: string;
  scopes: string[];
}

export interface AdminRole {
  id: string;
  name: string;
  description?: string;
}

export interface InvitationCreate {
  email: string;
  role_id: string;
}

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private http = inject(HttpClient);

  getUsers(q?: string): Observable<ApiResponse<AdminUser[]>> {
    let url = `${environment.apiUrl}/api/v1/users/`;
    if (q) {
      url += `?q=${encodeURIComponent(q)}`;
    }
    return this.http.get<ApiResponse<AdminUser[]>>(url);
  }

  getRoles(): Observable<ApiResponse<AdminRole[]>> {
    return this.http.get<ApiResponse<AdminRole[]>>(`${environment.apiUrl}/api/v2/admin/roles`);
  }

  inviteUser(invitation: InvitationCreate): Observable<ApiResponse<{code: string}>> {
    return this.http.post<ApiResponse<{code: string}>>(`${environment.apiUrl}/api/v2/admin/users/invite`, invitation);
  }

  assignRole(email: string, roleId: string): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>(`${environment.apiUrl}/api/v2/admin/users/assign-role`, { email, role_id: roleId });
  }

  updateScopes(userId: string, scopes: string[]): Observable<ApiResponse<void>> {
    return this.http.patch<ApiResponse<void>>(`${environment.apiUrl}/api/v2/admin/users/${userId}/scopes`, { scopes });
  }

  revokeAccess(userId: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`${environment.apiUrl}/api/v2/admin/users/${userId}`);
  }
}
