import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '@models/api.types';
import { Observable } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class AdminRescueService {
    private http = inject(HttpClient);

    // URLs específicas por microservicio
    private authAdminUrl = `${environment.authUrl}/admin`;
    private subscriptionAdminUrl = `${environment.subscriptionUrl}/admin`;

    forceAssignUser(userId: string, companyId: string, roleId: string): Observable<ApiResponse<any>> {
        return this.http.post<ApiResponse<any>>(`${this.authAdminUrl}/users/force-assign`, {
            user_id: userId,
            company_id: companyId,
            role_id: roleId
        });
    }

    overrideGracePeriod(companyId: string, days: number): Observable<ApiResponse<any>> {
        return this.http.post<ApiResponse<any>>(`${this.subscriptionAdminUrl}/tenants/${companyId}/override-grace`, {
            days: days
        });
    }
}
