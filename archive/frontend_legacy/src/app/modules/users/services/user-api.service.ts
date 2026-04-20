import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '@env/environment';
import { AuthService } from '@core/services/auth.service';
import { ApiResponse, RoleResponse, InvitationCreate, InvitationResponse, UserRoleAssignment } from '@models/api.types';

@Injectable({
    providedIn: 'root'
})
export class UserApiService {
    private http = inject(HttpClient);
    private auth = inject(AuthService);
    private apiUrl = environment.authUrl; // Admin v2 is in auth-service

    private get headers(): HttpHeaders {
        const companyId = this.auth.activeCompanyId();
        let headers = new HttpHeaders({
            'Content-Type': 'application/json'
        });

        if (companyId) {
            headers = headers.set('X-Company-ID', companyId);
        }

        return headers;
    }

    getRoles(): Observable<ApiResponse<RoleResponse[]>> {
        return this.http.get<ApiResponse<RoleResponse[]>>(`${this.apiUrl}/api/v2/admin/roles`, {
            headers: this.headers
        });
    }

    inviteUser(payload: InvitationCreate): Observable<ApiResponse<InvitationResponse>> {
        return this.http.post<ApiResponse<InvitationResponse>>(`${this.apiUrl}/api/v2/admin/users/invite`, payload, {
            headers: this.headers
        });
    }

    assignRole(payload: UserRoleAssignment): Observable<ApiResponse<void>> {
        return this.http.post<ApiResponse<void>>(`${this.apiUrl}/api/v2/admin/users/assign-role`, payload, {
            headers: this.headers
        });
    }
}
