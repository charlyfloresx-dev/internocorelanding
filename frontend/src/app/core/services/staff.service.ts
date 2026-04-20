import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ApiResponse } from '../models/domain.types';
import { EligibilityResponse } from '../models/hr.types';

@Injectable({
  providedIn: 'root'
})
export class StaffService {
  private apiUrl = `${environment.hrUrl}/staff`;

  constructor(private http: HttpClient) {}

  /**
   * Phase 50: Validates an operator (driver/floor worker) for a specific operation.
   * Default type is CROSS_BORDER for logistics shipping verification.
   */
  validateOperator(badgeId: string, type: string = 'CROSS_BORDER'): Observable<EligibilityResponse> {
    const url = `${this.apiUrl}/validate-scan/${badgeId}?type=${type}`;
    return this.http.get<ApiResponse<EligibilityResponse>>(url).pipe(
      map(response => response.data)
    );
  }

  /**
   * Downloads the CSV template for collaborator bulk upload
   */
  downloadTemplate(): void {
    const url = `${this.apiUrl}/template`;
    this.http.get(url, { responseType: 'blob' }).subscribe(blob => {
      const a = document.createElement('a');
      const objectUrl = URL.createObjectURL(blob);
      a.href = objectUrl;
      a.download = 'collaborator_template.csv';
      a.click();
      URL.revokeObjectURL(objectUrl);
    });
  }

  /**
   * Performs bulk upload of collaborators via CSV
   */
  bulkUpload(file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.apiUrl}/bulk-upload`, formData);
  }
}
