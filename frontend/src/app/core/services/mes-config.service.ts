import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ScanPattern {
  id: string;
  item_code: string;
  pattern_name: string;
  regex: string;
  error_message: string;
  priority: number;
  is_active: boolean;
}

export interface AddScanPatternCommand {
  item_code: string;
  pattern_name: string;
  regex: string;
  error_message: string;
  priority: number;
  is_active: boolean;
}

@Injectable({ providedIn: 'root' })
export class MesConfigService {
  private http = inject(HttpClient);
  private base = environment.masterDataUrl;

  // ── Query state ────────────────────────────────────────────────────────────
  readonly patterns = signal<ScanPattern[]>([]);
  readonly queryLoading = signal(false);
  readonly queryError = signal<string | null>(null);
  readonly queriedItemCode = signal<string | null>(null);

  // ── Command state ──────────────────────────────────────────────────────────
  readonly commandBusy = signal(false);
  readonly commandError = signal<string | null>(null);

  // ── Query: GET /products/{item_code}/scan-patterns ─────────────────────────
  async queryPatterns(itemCode: string): Promise<void> {
    this.queryLoading.set(true);
    this.queryError.set(null);
    this.queriedItemCode.set(itemCode);
    try {
      const resp: any = await lastValueFrom(
        this.http.get(`${this.base}/products/${encodeURIComponent(itemCode)}/scan-patterns`)
      );
      this.patterns.set(resp?.data ?? []);
    } catch (err: any) {
      this.queryError.set(err?.error?.detail ?? 'Error al cargar patrones');
      this.patterns.set([]);
    } finally {
      this.queryLoading.set(false);
    }
  }

  // ── Command: POST /products/{item_code}/scan-patterns ──────────────────────
  async addPattern(cmd: AddScanPatternCommand): Promise<boolean> {
    this.commandBusy.set(true);
    this.commandError.set(null);
    try {
      await lastValueFrom(
        this.http.post(
          `${this.base}/products/${encodeURIComponent(cmd.item_code)}/scan-patterns`,
          cmd
        )
      );
      // Refresh query after command (CQRS eventual sync)
      await this.queryPatterns(cmd.item_code);
      return true;
    } catch (err: any) {
      this.commandError.set(err?.error?.detail ?? 'Error al crear patrón');
      return false;
    } finally {
      this.commandBusy.set(false);
    }
  }

  // ── Command: DELETE /products/{item_code}/scan-patterns/{id} ───────────────
  async removePattern(itemCode: string, patternId: string): Promise<boolean> {
    this.commandBusy.set(true);
    this.commandError.set(null);
    try {
      await lastValueFrom(
        this.http.delete(
          `${this.base}/products/${encodeURIComponent(itemCode)}/scan-patterns/${patternId}`
        )
      );
      // Optimistic removal from local state
      this.patterns.update(list => list.filter(p => p.id !== patternId));
      return true;
    } catch (err: any) {
      this.commandError.set(err?.error?.detail ?? 'Error al eliminar patrón');
      return false;
    } finally {
      this.commandBusy.set(false);
    }
  }

  clearCommandError(): void {
    this.commandError.set(null);
  }
}
