import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { lastValueFrom } from 'rxjs';
import { environment } from '../../../environments/environment';
import { ShiftRead, ShiftCreate, ShiftUpdate, ShiftBreakCreate, BreakSlot } from '../models/mes.types';

@Injectable({ providedIn: 'root' })
export class ShiftService {
  private http = inject(HttpClient);
  private base = `${environment.productionUrl}/mes/shifts`;

  readonly shifts   = signal<ShiftRead[]>([]);
  readonly loading  = signal(false);
  readonly saving   = signal(false);
  readonly error    = signal<string | null>(null);

  // ── List ──────────────────────────────────────────────────────────────────

  async loadShifts(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const resp: any = await lastValueFrom(this.http.get(this.base + '/'));
      const data = resp?.data ?? resp;
      this.shifts.set(Array.isArray(data) ? data : []);
    } catch (err: any) {
      this.error.set(err?.error?.detail ?? 'Error al cargar turnos');
      this.shifts.set([]);
    } finally {
      this.loading.set(false);
    }
  }

  // ── Create ────────────────────────────────────────────────────────────────

  async createShift(body: ShiftCreate): Promise<ShiftRead> {
    this.saving.set(true);
    try {
      const resp: any = await lastValueFrom(
        this.http.post(this.base + '/', body)
      );
      const shift: ShiftRead = resp?.data ?? resp;
      this.shifts.update(list => [...list, shift]);
      return shift;
    } finally {
      this.saving.set(false);
    }
  }

  // ── Update ────────────────────────────────────────────────────────────────

  async updateShift(shiftId: string, body: ShiftUpdate): Promise<ShiftRead> {
    this.saving.set(true);
    try {
      const resp: any = await lastValueFrom(
        this.http.patch(`${this.base}/${shiftId}`, body)
      );
      const updated: ShiftRead = resp?.data ?? resp;
      this.shifts.update(list =>
        list.map(s => s.id === shiftId ? updated : s)
      );
      return updated;
    } finally {
      this.saving.set(false);
    }
  }

  // ── Soft-delete ───────────────────────────────────────────────────────────

  async deleteShift(shiftId: string): Promise<void> {
    this.saving.set(true);
    try {
      await lastValueFrom(this.http.delete(`${this.base}/${shiftId}`));
      this.shifts.update(list =>
        list.map(s => s.id === shiftId ? { ...s, is_active: false } : s)
      );
    } finally {
      this.saving.set(false);
    }
  }

  // ── Breaks ────────────────────────────────────────────────────────────────

  async createBreak(shiftId: string, body: ShiftBreakCreate): Promise<BreakSlot> {
    const resp: any = await lastValueFrom(
      this.http.post(`${this.base}/${shiftId}/breaks`, body)
    );
    const brk: BreakSlot = resp?.data ?? resp;
    this.shifts.update(list =>
      list.map(s => s.id === shiftId
        ? { ...s, breaks: [...s.breaks, brk] }
        : s)
    );
    return brk;
  }

  async deleteBreak(shiftId: string, breakId: string): Promise<void> {
    await lastValueFrom(
      this.http.delete(`${this.base}/${shiftId}/breaks/${breakId}`)
    );
    this.shifts.update(list =>
      list.map(s => s.id === shiftId
        ? { ...s, breaks: s.breaks.filter((b: any) => b.id !== breakId) }
        : s)
    );
  }
}
