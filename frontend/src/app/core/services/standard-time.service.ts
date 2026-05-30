import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface StandardTime {
  id: string;
  item_code: string;
  operation_name: string;
  set_time_hours: number;
  cycle_time_seconds: number | null;
}

export interface StandardTimeCreate {
  item_code: string;
  operation_name: string;
  set_time_hours: number;
  cycle_time_seconds: number | null;
}

export interface StandardTimeUpdate {
  operation_name?: string;
  set_time_hours?: number;
  cycle_time_seconds?: number | null;
}

export interface BulkCreateResponse {
  created: number;
  skipped: number;
  errors: { row: number; item_code: string; error: string }[];
}

@Injectable({ providedIn: 'root' })
export class StandardTimeService {
  private http = inject(HttpClient);
  private get base(): string {
    return `${environment.productionUrl}/mes/standard-times`;
  }

  items = signal<StandardTime[]>([]);
  loading = signal(false);
  saving = signal(false);
  currentItemCode = signal<string>('');

  async load(itemCode?: string): Promise<void> {
    this.loading.set(true);
    try {
      const params = itemCode ? `?item_code=${encodeURIComponent(itemCode)}` : '';
      const data = await firstValueFrom(
        this.http.get<StandardTime[]>(`${this.base}/${params}`)
      );
      this.items.set(data ?? []);
      if (itemCode) this.currentItemCode.set(itemCode);
    } finally {
      this.loading.set(false);
    }
  }

  async create(payload: StandardTimeCreate): Promise<StandardTime> {
    this.saving.set(true);
    try {
      const result = await firstValueFrom(
        this.http.post<StandardTime>(`${this.base}/`, payload)
      );
      return result;
    } finally {
      this.saving.set(false);
    }
  }

  async update(id: string, payload: StandardTimeUpdate): Promise<StandardTime> {
    this.saving.set(true);
    try {
      const result = await firstValueFrom(
        this.http.patch<StandardTime>(`${this.base}/${id}`, payload)
      );
      return result;
    } finally {
      this.saving.set(false);
    }
  }

  async remove(id: string): Promise<void> {
    this.saving.set(true);
    try {
      await firstValueFrom(this.http.delete(`${this.base}/${id}`));
    } finally {
      this.saving.set(false);
    }
  }

  async bulkCreate(items: StandardTimeCreate[]): Promise<BulkCreateResponse> {
    this.saving.set(true);
    try {
      return await firstValueFrom(
        this.http.post<BulkCreateResponse>(`${this.base}/bulk`, { items })
      );
    } finally {
      this.saving.set(false);
    }
  }
}
