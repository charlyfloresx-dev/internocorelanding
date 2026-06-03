import { Component, OnInit, OnDestroy, inject, signal, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { SideDrawerService } from '../../../../core/services/side-drawer.service';
import { TicketService } from '../../../../core/services/ticket.service';
import { ToastService } from '../../../../core/services/toast.service';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface TicketComment {
  id: string;
  content: string;
  author_id: string;
  created_at: string;
}

@Component({
  selector: 'app-ticket-comments-drawer',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule],
  template: `
    <div class="flex flex-col h-full">
      <!-- Header -->
      <div class="px-6 py-5 border-b border-surface-border flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-2">
          <mat-icon>chat</mat-icon>
          <h2 class="text-sm font-black text-surface-text uppercase tracking-widest">Comentarios</h2>
          @if (comments().length > 0) {
            <span class="text-xs bg-primary/20 text-primary px-1.5 py-0.5 rounded-full">{{ comments().length }}</span>
          }
        </div>
        <button (click)="drawerSvc.close()"
                class="p-1 hover:bg-surface-text/10 rounded-lg transition-colors">
          <mat-icon class="text-sm">close</mat-icon>
        </button>
      </div>

      <!-- Comments List -->
      <div class="flex-1 overflow-y-auto px-6 py-4 space-y-3 custom-scrollbar">
        @if (isLoading()) {
          <div class="flex items-center justify-center py-8">
            <mat-icon class="animate-spin text-surface-text-muted">refresh</mat-icon>
          </div>
        } @else if (comments().length === 0) {
          <div class="flex flex-col items-center justify-center h-full gap-2 opacity-40 py-8">
            <mat-icon class="text-4xl">chat_bubble_outline</mat-icon>
            <p class="text-xs text-surface-text-muted">Sin comentarios aún</p>
          </div>
        } @else {
          @for (comment of comments(); track comment.id) {
            <div class="flex gap-2">
              <div class="w-6 h-6 rounded-full bg-primary/10 flex-shrink-0 flex items-center justify-center">
                <mat-icon class="text-xs text-primary">person</mat-icon>
              </div>
              <div class="flex-1">
                <div class="bg-surface-text/[0.03] border border-surface-border rounded-lg px-3 py-2">
                  <p class="text-xs text-surface-text leading-relaxed">{{ comment.content }}</p>
                  <p class="text-[10px] text-surface-text-muted mt-1">{{ formatTime(comment.created_at) }}</p>
                </div>
              </div>
            </div>
          }
        }
      </div>

      <!-- Input Bar -->
      <div class="px-6 py-4 border-t border-surface-border flex-shrink-0 flex gap-2">
        <input type="text"
               [(ngModel)]="newCommentText"
               (keyup.enter)="onAddComment()"
               placeholder="Agregar comentario..."
               class="flex-1 bg-surface-card border border-surface-border text-surface-text text-xs rounded-lg px-3 py-2 focus:ring-primary focus:border-primary" />
        <button (click)="onAddComment()"
                [disabled]="!newCommentText.trim() || isSubmitting()"
                class="p-2 bg-primary hover:bg-primary-hover text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center">
          @if (isSubmitting()) {
            <mat-icon class="animate-spin text-sm">refresh</mat-icon>
          } @else {
            <mat-icon class="text-sm">send</mat-icon>
          }
        </button>
      </div>
    </div>
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar { width: 6px; }
    .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.3); border-radius: 10px; }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(148, 163, 184, 0.6); }
  `]
})
export class TicketCommentsDrawerComponent implements OnInit, OnDestroy {
  readonly drawerSvc = inject(SideDrawerService);
  private ticketSvc = inject(TicketService);
  private toastSvc = inject(ToastService);

  ticket: any = null;
  comments = signal<TicketComment[]>([]);
  newCommentText = '';
  isLoading = signal(false);
  isSubmitting = signal(false);

  private destroy$ = new Subject<void>();

  ngOnInit(): void {
    this.ticket = this.drawerSvc.data();
    this.loadComments();

    // Refresh when drawer notifies
    this.drawerSvc.refresh$
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => this.loadComments());
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadComments(): void {
    if (!this.ticket?.id) return;
    this.isLoading.set(true);
    // TODO: Replace with real API call
    // For now, mock data
    setTimeout(() => {
      this.comments.set([
        {
          id: '1',
          content: 'Revisar la alineación de la máquina antes de proceder.',
          author_id: 'user-1',
          created_at: new Date(Date.now() - 3600000).toISOString()
        },
        {
          id: '2',
          content: 'Confirmado, ya se verificó. Todo dentro de tolerancia.',
          author_id: 'user-2',
          created_at: new Date(Date.now() - 1800000).toISOString()
        }
      ]);
      this.isLoading.set(false);
    }, 300);
  }

  onAddComment(): void {
    const text = this.newCommentText.trim();
    if (!text || !this.ticket?.id) return;

    this.isSubmitting.set(true);
    this.ticketSvc.addComment(this.ticket.id, text).subscribe({
      next: () => {
        this.newCommentText = '';
        this.toastSvc.success('Comentario Agregado', '');
        this.loadComments();
        this.isSubmitting.set(false);
      },
      error: (err) => {
        this.toastSvc.error('Error', 'No se pudo agregar el comentario');
        console.error('Comment error:', err);
        this.isSubmitting.set(false);
      }
    });
  }

  formatTime(iso: string): string {
    try {
      const d = new Date(iso);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'Ahora';
      if (diffMins < 60) return `hace ${diffMins}m`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `hace ${diffHours}h`;
      return d.toLocaleDateString('es-MX');
    } catch {
      return '';
    }
  }
}
