import { Injectable, signal, computed } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class GodModeStore {
  readonly token     = signal<string | null>(null);
  readonly jti       = signal<string | null>(null);
  readonly expiresAt = signal<number | null>(null);
  readonly attempts  = signal<number>(0);

  readonly isActive = computed(() => {
    const exp = this.expiresAt();
    return this.token() !== null && exp !== null && Date.now() < exp;
  });

  readonly isLocked = computed(() => this.attempts() >= 3);

  readonly secondsRemaining = computed(() => {
    const exp = this.expiresAt();
    if (!exp || !this.isActive()) return 0;
    return Math.max(0, Math.ceil((exp - Date.now()) / 1000));
  });

  activate(token: string, jti: string, expiresIn: number): void {
    this.token.set(token);
    this.jti.set(jti);
    this.expiresAt.set(Date.now() + expiresIn * 1000);
    this.attempts.set(0);
    setTimeout(() => this.clear(), expiresIn * 1000);
  }

  recordFailedAttempt(): void {
    this.attempts.update(n => n + 1);
  }

  clear(): void {
    this.token.set(null);
    this.jti.set(null);
    this.expiresAt.set(null);
  }
}