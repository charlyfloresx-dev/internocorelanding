import { Component, inject, signal, output, input, effect, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { FormsModule } from '@angular/forms';
import { SupportService } from '../../core/services/support.service';
import { Ticket, TicketPriority, TicketStatus, TicketComment } from '../../core/models/support.types';
import { TranslatePipe } from '../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-support-drawer',
  standalone: true,
  imports: [CommonModule, MatIconModule, FormsModule, TranslatePipe],
  template: `
    <div 
      class="fixed inset-y-0 right-0 w-96 bg-surface-card border-l border-surface-border shadow-2xl z-[100] transform transition-transform duration-500 ease-out flex flex-col"
      [class.translate-x-0]="isOpen()"
      [class.translate-x-full]="!isOpen()"
    >
      <!-- Header -->
      <div class="h-20 px-6 border-b border-surface-border flex items-center justify-between bg-nav-bar/50 backdrop-blur-xl">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
            <mat-icon>support_agent</mat-icon>
          </div>
          <div>
            <h2 class="text-sm font-black text-surface-text uppercase tracking-widest">{{ 'support.drawer_title' | translate:'Soporte Técnico' }}</h2>
            <span class="text-[10px] text-surface-text-muted font-bold uppercase tracking-tighter">{{ 'support.drawer_subtitle' | translate:'Centro de Ayuda AI' }}</span>
          </div>
        </div>
        <button (click)="closed.emit()" class="text-surface-text-muted hover:text-primary transition-colors">
          <mat-icon>close</mat-icon>
        </button>
      </div>

      <!-- Content Area -->
      <div class="flex-1 overflow-hidden relative flex flex-col">
        
        <!-- View: List -->
        @if (view() === 'list') {
          <div class="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-surface-text-muted uppercase tracking-[0.2em]">{{ 'support.my_tickets' | translate:'Mis Tickets' }}</span>
              <button (click)="view.set('create')" class="text-[10px] bg-primary/10 text-primary px-3 py-1 rounded-lg font-black uppercase tracking-widest hover:bg-primary/20 transition-all">
                {{ 'support.new_ticket' | translate:'Nuevo' }} +
              </button>
            </div>

            @if (supportService.loading() && supportService.tickets().length === 0) {
              <div class="flex flex-col items-center justify-center h-64">
                <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>
            } @else if (supportService.tickets().length === 0) {
              <div class="flex flex-col items-center justify-center h-64 opacity-20">
                <mat-icon class="text-6xl mb-4">confirmation_number</mat-icon>
                <p class="text-xs font-bold uppercase tracking-widest text-center">{{ 'support.empty_tickets' | translate:'No hay tickets activos' }}</p>
              </div>
            }

            @for (ticket of supportService.tickets(); track ticket.id) {
              <button 
                (click)="selectTicket(ticket)"
                class="w-full text-left p-4 rounded-xl border border-surface-border bg-surface-bg/50 hover:border-primary/30 transition-all cursor-pointer group"
              >
                <div class="flex items-start justify-between mb-2">
                  <span class="text-[10px] font-mono text-primary font-bold">#{{ ticket.reference_code }}</span>
                  <span class="text-[8px] px-2 py-0.5 rounded bg-surface-text/5 text-surface-text-muted font-bold uppercase">
                    {{ 'support.status.' + ticket.status.toLowerCase() | translate:ticket.status }}
                  </span>
                </div>
                <h3 class="text-xs font-bold text-surface-text mb-1 truncate group-hover:text-primary transition-colors">
                  {{ ticket.title }}
                </h3>
                <p class="text-[10px] text-surface-text-muted line-clamp-2 leading-relaxed">
                  {{ ticket.description }}
                </p>
                <div class="mt-3 pt-3 border-t border-surface-border flex items-center justify-between">
                  <span class="text-[8px] font-bold text-surface-text-muted uppercase">
                    {{ ticket.created_at | date:'short' }}
                  </span>
                  <div class="flex items-center gap-1">
                    <div class="w-1.5 h-1.5 rounded-full" [ngClass]="getPriorityColor(ticket.priority)"></div>
                    <span class="text-[8px] font-bold uppercase">{{ 'support.priority.' + ticket.priority.toLowerCase() | translate:ticket.priority }}</span>
                  </div>
                </div>
              </button>
            }
          </div>
        }

        <!-- View: Create -->
        @if (view() === 'create') {
          <div class="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar animate-in slide-in-from-right duration-300">
            <button (click)="view.set('list')" class="flex items-center gap-2 text-surface-text-muted hover:text-primary transition-colors">
              <mat-icon class="text-sm">arrow_back</mat-icon>
              <span class="text-[10px] font-black uppercase tracking-widest">{{ 'support.back_to_list' | translate:'Volver al historial' }}</span>
            </button>

            <div class="space-y-4">
              <div class="space-y-1">
                <label for="ticketSubject" class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest ml-1">{{ 'support.subject_label' | translate:'Asunto' }}</label>
                <input 
                  id="ticketSubject"
                  [(ngModel)]="newTicket.title"
                  placeholder="Ej: Problema con inventario"
                  class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs text-surface-text outline-none focus:border-primary transition-all placeholder:text-surface-text-muted/30"
                />
              </div>

              <div class="space-y-1">
                <label for="ticketPriority" class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest ml-1">{{ 'support.priority_label' | translate:'Prioridad' }}</label>
                <select 
                  id="ticketPriority"
                  [(ngModel)]="newTicket.priority"
                  class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs text-surface-text outline-none focus:border-primary transition-all appearance-none"
                >
                  @if (supportService.constants(); as constants) {
                    @for (p of constants.priorities; track p) {
                      <option [value]="p">{{ 'support.priority.' + p.toLowerCase() | translate:p }}</option>
                    }
                  } @else {
                    <option [value]="TicketPriority.LOW">{{ 'support.priority.low' | translate:'Baja' }}</option>
                    <option [value]="TicketPriority.MEDIUM">{{ 'support.priority.medium' | translate:'Media' }}</option>
                    <option [value]="TicketPriority.HIGH">{{ 'support.priority.high' | translate:'Alta' }}</option>
                    <option [value]="TicketPriority.CRITICAL">{{ 'support.priority.critical' | translate:'Crítica' }}</option>
                  }
                </select>
              </div>

              <div class="space-y-1">
                <label for="ticketDesc" class="text-[10px] font-black text-surface-text-muted uppercase tracking-widest ml-1">{{ 'support.description_label' | translate:'Descripción' }}</label>
                <textarea 
                  id="ticketDesc"
                  [(ngModel)]="newTicket.description"
                  rows="6"
                  placeholder="Describe detalladamente el problema..."
                  class="w-full bg-surface-bg border border-surface-border rounded-xl px-4 py-3 text-xs text-surface-text outline-none focus:border-primary transition-all resize-none placeholder:text-surface-text-muted/30"
                ></textarea>
              </div>
            </div>

            <button 
              (click)="submitTicket()"
              [disabled]="!newTicket.title || !newTicket.description || supportService.loading()"
              class="w-full py-4 bg-primary text-slate-900 rounded-xl font-black text-xs uppercase tracking-[0.2em] shadow-[0_0_20px_rgba(0,229,255,0.3)] hover:scale-[1.02] active:scale-95 disabled:opacity-50 disabled:scale-100 transition-all"
            >
              {{ supportService.loading() ? ('support.creating' | translate:'Creando...') : ('support.create_button' | translate:'Crear Ticket') }}
            </button>
          </div>
        }

        <!-- View: Chat -->
        @if (view() === 'chat' && selectedTicket()) {
          <div class="flex-1 flex flex-col animate-in slide-in-from-right duration-300">
            <div class="p-4 border-b border-surface-border flex items-center justify-between bg-surface-bg/30">
              <button (click)="view.set('list')" class="flex items-center gap-2 text-surface-text-muted hover:text-primary transition-colors">
                <mat-icon class="text-sm">arrow_back</mat-icon>
                <span class="text-[10px] font-black uppercase tracking-widest">{{ 'common.back' | translate:'Atrás' }}</span>
              </button>
              <span class="text-[10px] font-mono font-bold text-primary">#{{ selectedTicket()!.reference_code }}</span>
            </div>

            <div class="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar" #scrollContainer>
              @for (msg of messages(); track msg.id) {
                <div 
                  class="max-w-[85%] flex flex-col"
                  [ngClass]="false ? 'mr-auto' : 'ml-auto items-end'"
                >
                  <div 
                    class="px-4 py-3 rounded-2xl text-xs leading-relaxed"
                    [ngClass]="false ? 'bg-primary/10 border border-primary/20 text-surface-text rounded-tl-none' : 'bg-surface-bg border border-surface-border text-surface-text rounded-tr-none'"
                  >
                    {{ msg.content }}
                  </div>
                  <span class="text-[8px] font-bold text-surface-text-muted uppercase tracking-tighter mt-1 px-1">
                    Operador • {{ msg.created_at | date:'HH:mm' }}
                  </span>
                </div>
              }
            </div>

            <div class="p-4 border-t border-surface-border bg-nav-bar/30">
              <div class="relative">
                <input 
                  [(ngModel)]="chatMessage"
                  (keyup.enter)="sendMessage()"
                  [placeholder]="'support.chat_placeholder' | translate:'Escribe un mensaje...'"
                  class="w-full bg-surface-bg border border-surface-border rounded-xl pl-4 pr-12 py-3 text-xs text-surface-text outline-none focus:border-primary transition-all shadow-inner"
                />
                <button 
                  (click)="sendMessage()"
                  [disabled]="!chatMessage"
                  class="absolute right-2 top-2 p-1.5 text-primary hover:bg-primary/10 rounded-lg transition-all disabled:opacity-30"
                >
                  <mat-icon>send</mat-icon>
                </button>
              </div>
            </div>
          </div>
        }

      </div>

      <!-- Footer Info -->
      <div class="p-4 bg-nav-bar/20 border-t border-surface-border flex items-center justify-center gap-4">
        <div class="flex items-center gap-1.5">
          <div class="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse shadow-[0_0_8px_rgba(0,255,102,0.5)]"></div>
          <span class="text-[9px] font-black text-neon-green uppercase tracking-widest">{{ 'support.mcp_active' | translate:'Servicio Unificado Activo' }}</span>
        </div>
      </div>
    </div>

    <!-- Backdrop -->
    @if (isOpen()) {
      <button 
        (click)="closed.emit()"
        class="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] animate-in fade-in duration-500 w-full h-full text-transparent"
        aria-label="Close Support"
      >
        Close
      </button>
    }
  `,
  styles: [`
    .custom-scrollbar::-webkit-scrollbar {
      width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: rgba(0, 229, 255, 0.1);
      border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
      background: rgba(0, 229, 255, 0.3);
    }
  `]
})
export class SupportDrawerComponent {
  supportService = inject(SupportService);
  
  isOpen = input(false);
  closed = output<void>();

  view = signal<'list' | 'create' | 'chat'>('list');
  selectedTicket = signal<Ticket | null>(null);
  messages = signal<TicketComment[]>([]);

  @ViewChild('scrollContainer') scrollContainer?: ElementRef;

  // New ticket form
  TicketPriority = TicketPriority;
  newTicket = {
    title: '',
    description: '',
    priority: TicketPriority.MEDIUM
  };

  // Chat
  chatMessage = '';

  constructor() {
    effect(() => {
      if (this.isOpen()) {
        this.supportService.loadTickets();
      }
    });
  }

  async selectTicket(ticket: Ticket) {
    this.selectedTicket.set(ticket);
    this.view.set('chat');
    const msgs = await this.supportService.getMessages(ticket.id);
    this.messages.set(msgs);
    this.scrollToBottom();
  }

  async submitTicket() {
    try {
      await this.supportService.createTicket(
        this.newTicket.title, 
        this.newTicket.description, 
        this.newTicket.priority
      );
      this.newTicket = { title: '', description: '', priority: TicketPriority.MEDIUM };
      this.view.set('list');
    } catch (err) {
      // Handle error
    }
  }

  async sendMessage() {
    if (!this.chatMessage || !this.selectedTicket()) return;
    try {
      const newMsg = await this.supportService.addMessage(this.selectedTicket()!.id, this.chatMessage);
      if (newMsg) {
        this.messages.update(ms => [...ms, newMsg]);
        this.chatMessage = '';
        this.scrollToBottom();
      }
    } catch (err) {
      // Handle error
    }
  }

  getPriorityColor(priority: TicketPriority) {
    switch (priority) {
      case TicketPriority.LOW: return 'bg-slate-500';
      case TicketPriority.MEDIUM: return 'bg-amber-500';
      case TicketPriority.HIGH: return 'bg-orange-500';
      case TicketPriority.CRITICAL: return 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]';
      default: return 'bg-slate-500';
    }
  }

  private scrollToBottom() {
    setTimeout(() => {
      if (this.scrollContainer) {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }
}
