import {inject, Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {Observable} from 'rxjs';
import {ApiResponse} from '../models/api.types';

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

  getUsers(): Observable<ApiResponse<AdminUser[]>> {
    return this.http.get<ApiResponse<AdminUser[]>>('/api/v1/users/');
  }

  getRoles(): Observable<ApiResponse<AdminRole[]>> {
    return this.http.get<ApiResponse<AdminRole[]>>('/api/v2/admin/roles');
  }

  inviteUser(invitation: InvitationCreate): Observable<ApiResponse<{code: string}>> {
    return this.http.post<ApiResponse<{code: string}>>('/api/v2/admin/users/invite', invitation);
  }

  assignRole(email: string, roleId: string): Observable<ApiResponse<void>> {
    return this.http.post<ApiResponse<void>>('/api/v2/admin/users/assign-role', { email, role_id: roleId });
  }

  updateScopes(userId: string, scopes: string[]): Observable<ApiResponse<void>> {
    // Assuming a PATCH or PUT endpoint for updating user scopes
    return this.http.patch<ApiResponse<void>>(`/api/v2/admin/users/${userId}/scopes`, { scopes });
  }

  revokeAccess(userId: string): Observable<ApiResponse<void>> {
    return this.http.delete<ApiResponse<void>>(`/api/v2/admin/users/${userId}`);
  }
}
