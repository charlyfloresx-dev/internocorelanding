import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

export interface OnboardingCompanyPatch {
  default_tax_rate?: number;
  timezone?: string;
  base_currency?: string;
  country_code?: string;
  industry_sector?: string;
}

export interface OnboardingCategory {
  name: string;
  description?: string;
}

export interface OnboardingProductRow {
  sku: string;
  name: string;
  description?: string;
  category?: string;
  uom_code?: string;
  unit_price?: string;
  currency?: string;
}

export interface OnboardingPartnerRow {
  code: string;
  name: string;
  type: 'SUPPLIER' | 'CUSTOMER' | 'BOTH';
  rfc?: string;
  email?: string;
  phone?: string;
  city?: string;
}

export interface OnboardingWarehouse {
  name: string;
  code: string;
  warehouse_type: 'PHYSICAL' | 'VIRTUAL' | 'TRANSIT';
  address?: string;
}

export interface OnboardingCollaboratorRow {
  internal_id: string;
  name: string;
  last_name: string;
  department?: string;
  job_title?: string;
  rfid_code?: string;
  pin?: string;
  email?: string;
}

export interface OnboardingFacility {
  name: string;
  code: string;
  address?: string;
}

@Injectable({ providedIn: 'root' })
export class OnboardingService {
  private http = inject(HttpClient);
  private readonly base = '/api/v1';

  patchCompany(data: OnboardingCompanyPatch): Promise<any> {
    return firstValueFrom(this.http.patch(`${this.base}/auth/companies/current`, data));
  }

  createCategory(data: OnboardingCategory): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/categories`, data));
  }

  bulkImportProducts(rows: OnboardingProductRow[]): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/products/bulk`, { items: rows }));
  }

  bulkImportPartners(rows: OnboardingPartnerRow[]): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/partners/bulk`, { items: rows }));
  }

  createWarehouse(data: OnboardingWarehouse): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/catalog/warehouses`, data));
  }

  bulkImportCollaborators(rows: OnboardingCollaboratorRow[]): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/hcm/collaborators/bulk`, { collaborators: rows }));
  }

  createFacility(data: OnboardingFacility): Promise<any> {
    return firstValueFrom(this.http.post(`${this.base}/mes/facilities`, data));
  }

  /** Descarga un string CSV como archivo */
  downloadCsv(content: string, filename: string): void {
    const bom = '﻿'; // UTF-8 BOM para que Excel lo abra bien
    const blob = new Blob([bom + content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  /** Parser CSV robusto (maneja campos con comas entre comillas) */
  parseCsv(text: string): Record<string, string>[] {
    const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim().split('\n');
    if (lines.length < 2) return [];
    const headers = this.splitCsvLine(lines[0]);
    return lines.slice(1)
      .filter(l => l.trim())
      .map(line => {
        const values = this.splitCsvLine(line);
        return Object.fromEntries(headers.map((h, i) => [h.trim(), (values[i] ?? '').trim()]));
      });
  }

  private splitCsvLine(line: string): string[] {
    const result: string[] = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        inQuotes = !inQuotes;
      } else if (ch === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else {
        current += ch;
      }
    }
    result.push(current);
    return result;
  }
}
