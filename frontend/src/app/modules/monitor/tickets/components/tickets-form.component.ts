import { Component, OnInit, inject, signal, computed, untracked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule, FormsModule } from '@angular/forms';
import { SupportService } from '../../../../core/services/support.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { SideDrawerService } from '../../../../core/services/side-drawer.service';
import { AdminService } from '../../../../core/services/admin.service';
import { AuthService } from '../../../../core/services/auth.service';
import { DepartmentService } from '../../../../core/services/department.service';
import { MatIconModule } from '@angular/material/icon';
import { finalize } from 'rxjs/operators';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';
import { LocalDatePipe } from '../../../../shared/pipes/local-date.pipe';
import { TicketStatus, TicketComment, TicketAction } from '../../../../core/models/support.types';

@Component({
  selector: 'app-tickets-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, FormsModule, MatIconModule, TranslatePipe, LocalDatePipe],
  template: `
    <div class="flex flex-col h-full bg-white animate-fade-in relative">
      
      <!-- Body -->
      <div class="flex-1 p-8" [ngClass]="view() === 'triage' ? 'overflow-hidden flex flex-col' : 'overflow-y-auto custom-scrollbar'">
        
        <!-- ================= LIST VIEW ================= -->
        <ng-container *ngIf="view() === 'list'">
          <div class="flex items-center justify-between mb-6">
            <div class="flex flex-col gap-1">
              <h3 class="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em]">{{ 'support.my_tickets' | translate:'MIS TICKETS' }}</h3>
              <a routerLink="kanban" (click)="drawerService.close()" class="text-[9px] font-bold text-sky-500 hover:text-sky-600 hover:underline uppercase tracking-widest flex items-center gap-1 cursor-pointer">
                {{ 'support.open_full_kanban' | translate:'ABRIR KANBAN COMPLETO' }} <mat-icon class="text-[10px] w-[10px] h-[10px]">launch</mat-icon>
              </a>
            </div>
            <button 
              (click)="switchView('form')"
              class="px-4 py-2 bg-sky-50 text-sky-500 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-sky-100 transition-colors"
            >
              {{ 'support.new_ticket' | translate:'NUEVO TICKET' }} +
            </button>
          </div>

          <div *ngIf="isLoadingTickets()" class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-400"></div>
          </div>

          <div *ngIf="!isLoadingTickets()" class="space-y-4">
            <div *ngFor="let t of tickets()" (click)="openTriage(t)" class="border border-slate-200 rounded-2xl p-5 bg-white hover:border-slate-300 transition-all cursor-pointer shadow-sm hover:shadow-md">
              <div class="flex justify-between items-start mb-3">
                <span class="text-sky-500 font-black text-xs tracking-widest">{{ t.reference_code || ('#TKT-' + t.id.slice(-4).toUpperCase()) }}</span>
                <span class="bg-slate-100 text-slate-500 px-2.5 py-1 rounded-md text-[9px] font-black uppercase tracking-widest">
                  {{ t.status }}
                </span>
              </div>
              <h4 class="font-bold text-slate-800 text-sm mb-1 line-clamp-1">{{ t.title }}</h4>
              <p class="text-slate-500 text-[11px] mb-5 line-clamp-2 leading-relaxed">{{ t.description }}</p>
              <div class="flex justify-between items-center text-[9px] font-black text-slate-400 uppercase tracking-widest">
                <span>{{ t.created_at | localDate:'M/d/yy, h:mm a' }}</span>
                <span class="flex items-center gap-1.5 font-bold text-slate-600">
                  <div class="w-1.5 h-1.5 rounded-full" [ngClass]="getPriorityColor(t.priority)"></div> 
                  {{ t.priority }}
                </span>
              </div>
            </div>

            <div *ngIf="tickets().length === 0" class="text-center py-12 border-2 border-dashed border-slate-100 rounded-2xl">
              <mat-icon class="text-slate-300 text-4xl mb-2">assignment</mat-icon>
              <p class="text-slate-400 text-xs font-bold">{{ 'support.no_tickets' | translate:'No se encontraron tickets.' }}</p>
            </div>
          </div>
        </ng-container>

        <!-- ================= FORM VIEW (CREATE) ================= -->
        <ng-container *ngIf="view() === 'form'">
          <button (click)="switchView('list')" class="flex items-center gap-2 text-slate-500 font-bold text-[11px] uppercase tracking-widest hover:text-slate-800 transition-colors mb-8">
            <mat-icon class="text-lg">arrow_back</mat-icon>
            {{ 'support.back_to_history' | translate:'VOLVER AL HISTORIAL' }}
          </button>

          <form [formGroup]="ticketForm" (ngSubmit)="save()" class="space-y-6">
            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ASUNTO</label>
              <input type="text" formControlName="title" placeholder="Ej: Problema con inventario" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 transition-all">
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">PRIORIDAD</label>
                <select formControlName="priority" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 appearance-none">
                  <option value="Baja">Baja</option>
                  <option value="Media">Media</option>
                  <option value="Alta">Alta</option>
                  <option value="Crítica">Crítica</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ÁREA</label>
                <select formControlName="area" class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 appearance-none">
                  @if (deptService.loading()) {
                    <option disabled>Cargando áreas...</option>
                  } @else if (deptService.departments().length === 0) {
                    <option value="">Sin áreas configuradas</option>
                  } @else {
                    @for (dept of deptService.departments(); track dept.id) {
                      <option [value]="dept.name">{{ dept.name }}</option>
                    }
                  }
                </select>
              </div>
            </div>

            <div class="space-y-2">
              <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">DESCRIPCIÓN</label>
              <textarea formControlName="description" rows="5" placeholder="Describe el problema..." class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 resize-none"></textarea>
            </div>

            <button type="submit" [disabled]="ticketForm.invalid || isSaving()" class="w-full py-4 bg-sky-500 hover:bg-sky-600 text-white rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] shadow-lg shadow-sky-200 transition-all">
              {{ isSaving() ? 'ENVIANDO...' : 'CREAR TICKET' }}
            </button>
          </form>
        </ng-container>

        <!-- ================= TRIAGE VIEW ================= -->
        <ng-container *ngIf="view() === 'triage'">
          <!-- Back -->
          <div (click)="switchView('list')" class="flex items-center gap-2 text-slate-500 font-bold text-[11px] uppercase tracking-widest hover:text-slate-800 transition-colors mb-6 cursor-pointer flex-shrink-0">
            <mat-icon class="text-lg">arrow_back</mat-icon>
            {{ 'support.back_to_list' | translate:'VOLVER AL LISTADO' }}
          </div>

          <!-- Two-column grid -->
          <div *ngIf="selectedTicket()" class="grid grid-cols-2 gap-8 flex-1 min-h-0">

            <!-- ── LEFT: Info + Assignment ── -->
            <div class="flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-2">

              <!-- Ticket card -->
              <div class="p-5 bg-slate-50 rounded-2xl border border-slate-100 flex-shrink-0">
                <span class="text-sky-500 font-black text-xs tracking-widest block mb-1">{{ selectedTicket().reference_code }}</span>
                <h3 class="text-base font-bold text-slate-800 leading-tight mb-1">{{ selectedTicket().title }}</h3>
                <p class="text-slate-500 text-[11px] leading-relaxed mb-3">{{ selectedTicket().description }}</p>
                <div class="flex gap-2">
                  <span class="px-2 py-1 rounded bg-slate-200 text-slate-600 text-[9px] font-bold uppercase tracking-widest">{{ selectedTicket().status }}</span>
                  <div class="flex items-center gap-1 px-2 py-1 rounded text-[9px] font-bold uppercase tracking-widest" [ngClass]="getPriorityColorClass(selectedTicket().priority)">
                    <div class="w-1 h-1 rounded-full bg-current"></div>
                    {{ selectedTicket().priority }}
                  </div>
                </div>
              </div>

              <!-- ASIGNACIÓN TRIPLE -->
              <div class="space-y-3">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">ASIGNAR RESPONSABLE</label>

                @if (selectedIdentities().length > 0) {
                  <div class="flex flex-wrap gap-2">
                    @for (p of selectedIdentities(); track (p.id + p.type)) {
                      <div class="flex items-center gap-1 px-3 py-1.5 rounded-full text-[10px] font-bold"
                           [ngClass]="{
                             'bg-sky-100 text-sky-700': p.type === 'INTERNAL',
                             'bg-amber-100 text-amber-700': p.type === 'PLANTA',
                             'bg-purple-100 text-purple-700': p.type === 'EXTERNO'
                           }">
                        <mat-icon class="text-[12px]">{{ p.type === 'INTERNAL' ? 'person' : (p.type === 'PLANTA' ? 'engineering' : 'business_center') }}</mat-icon>
                        <span class="uppercase tracking-tight">{{ p.label }}</span>
                        <button (click)="removeIdentity(p)" class="ml-1 hover:opacity-60 transition-opacity flex items-center">
                          <mat-icon class="text-[12px]">close</mat-icon>
                        </button>
                      </div>
                    }
                  </div>
                }

                <div class="relative">
                  <div class="flex items-center bg-slate-50 border border-slate-200 rounded-2xl p-1 transition-all focus-within:border-sky-400">
                    <mat-icon class="ml-3 text-slate-400">search</mat-icon>
                    <input
                      type="text"
                      [ngModel]="techSearchQuery()"
                      (ngModelChange)="onTechSearchChange($event)"
                      placeholder="Buscar técnico, operario o proveedor..."
                      class="flex-1 bg-transparent border-none p-3 text-sm font-medium text-slate-800 outline-none placeholder:text-slate-300"
                    >
                  </div>
                  @if (showTechDropdown() && typeaheadIdentities().length > 0) {
                    <div class="absolute z-[100] w-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-xl max-h-56 overflow-y-auto custom-scrollbar">
                      @for (identity of typeaheadIdentities(); track (identity.id + identity.type)) {
                        <div (mousedown)="selectIdentity(identity)"
                             class="px-4 py-3 hover:bg-slate-50 cursor-pointer border-b border-slate-100 last:border-0 flex items-center gap-3 transition-colors">
                          <div class="w-8 h-8 rounded-lg flex items-center justify-center"
                               [ngClass]="{
                                 'bg-sky-100 text-sky-500': identity.type === 'INTERNAL',
                                 'bg-amber-100 text-amber-500': identity.type === 'PLANTA',
                                 'bg-purple-100 text-purple-500': identity.type === 'EXTERNO'
                               }">
                            <mat-icon class="text-[18px]">{{ identity.type === 'INTERNAL' ? 'person' : (identity.type === 'PLANTA' ? 'engineering' : 'business_center') }}</mat-icon>
                          </div>
                          <div class="flex flex-col flex-1">
                            <span class="text-[11px] font-bold text-slate-800 uppercase tracking-tight">{{ identity.label }}</span>
                            <span class="text-[9px] text-slate-400 font-bold uppercase">{{ identity.type }} • {{ identity.sub }}</span>
                          </div>
                        </div>
                      }
                    </div>
                  }
                </div>

                @if (selectedIdentities().some(i => i.type === 'EXTERNO')) {
                  <div class="p-3 rounded-xl border border-purple-100 bg-purple-50/30 flex items-start gap-2 animate-fade-in">
                    <mat-icon class="text-purple-500 text-sm mt-0.5">verified_user</mat-icon>
                    <div>
                      <p class="text-[10px] font-black uppercase text-purple-600 tracking-widest mb-0.5">Acceso Externo (SLA 72h)</p>
                      <p class="text-[10px] text-slate-500 leading-tight">Se generará un Bridge Seguro para el proveedor.</p>
                    </div>
                  </div>
                }
              </div>

              <!-- Notas -->
              <div class="space-y-2">
                <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest block">INSTRUCCIONES / NOTAS</label>
                <textarea
                  [ngModel]="triageComment()"
                  (ngModelChange)="triageComment.set($event)"
                  placeholder="Instrucciones adicionales para el responsable..."
                  rows="4"
                  class="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm font-medium text-slate-800 outline-none focus:border-sky-400 transition-all resize-none placeholder:text-slate-300"
                ></textarea>
              </div>

              <!-- GUARDAR ASIGNACIÓN -->
              <button
                (click)="submitTriage()"
                [disabled]="selectedIdentities().length === 0 || isSaving()"
                class="w-full py-4 bg-sky-500 hover:bg-sky-600 text-white rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-sm"
              >
                <mat-icon class="text-[18px]">{{ isSaving() ? 'hourglass_empty' : 'save' }}</mat-icon>
                {{ isSaving() ? 'GUARDANDO...' : 'GUARDAR ASIGNACIÓN' }}
              </button>

              <!-- ── ACCIONES ── -->
              <div class="border-t border-slate-100 pt-4 space-y-3">
                <div class="flex items-center justify-between">
                  <label class="text-[11px] font-bold text-slate-500 uppercase tracking-widest">PLAN DE ACCIONES</label>
                  <button (click)="showActionForm.set(!showActionForm())"
                          class="flex items-center gap-1 text-[10px] font-black text-sky-500 hover:text-sky-600 uppercase tracking-widest transition-colors">
                    <mat-icon class="text-[14px]">{{ showActionForm() ? 'expand_less' : 'add' }}</mat-icon>
                    {{ showActionForm() ? 'CANCELAR' : 'NUEVA' }}
                  </button>
                </div>

                <!-- Formulario nueva acción -->
                @if (showActionForm()) {
                  <div class="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2 animate-fade-in">
                    <input
                      type="text"
                      [ngModel]="newActionText()"
                      (ngModelChange)="newActionText.set($event)"
                      placeholder="Descripción de la acción..."
                      class="w-full bg-white border border-slate-200 rounded-xl p-3 text-[11px] font-medium text-slate-800 outline-none focus:border-sky-400 transition-all placeholder:text-slate-300"
                    >
                    <div class="flex gap-2">
                      <input
                        type="date"
                        [ngModel]="newActionDate()"
                        (ngModelChange)="newActionDate.set($event)"
                        class="flex-1 bg-white border border-slate-200 rounded-xl p-3 text-[11px] font-medium text-slate-600 outline-none focus:border-sky-400 transition-all"
                      >
                      <input
                        type="time"
                        step="300"
                        [ngModel]="newActionTime()"
                        (ngModelChange)="newActionTime.set($event)"
                        class="w-28 bg-white border border-slate-200 rounded-xl p-3 text-[11px] font-medium text-slate-600 outline-none focus:border-sky-400 transition-all"
                      >
                    </div>
                    <div class="flex items-center gap-1 text-[10px] text-slate-400 font-bold px-1">
                      <mat-icon class="text-[12px]">person_pin</mat-icon>
                      <span>Se asignará al primer responsable del ticket</span>
                    </div>
                    <button
                      (click)="addAction()"
                      [disabled]="!newActionText().trim() || isAddingAction()"
                      class="w-full py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-40 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-colors flex justify-center items-center gap-1"
                    >
                      <mat-icon class="text-[14px]">{{ isAddingAction() ? 'hourglass_empty' : 'check' }}</mat-icon>
                      {{ isAddingAction() ? 'CREANDO...' : 'AGREGAR ACCIÓN' }}
                    </button>
                  </div>
                }

                <!-- Lista de acciones -->
                @if (isLoadingActions()) {
                  <div class="flex justify-center py-4">
                    <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-sky-400"></div>
                  </div>
                }
                @if (!isLoadingActions() && actions().length === 0) {
                  <p class="text-[10px] text-slate-400 font-bold text-center py-3">Sin acciones registradas</p>
                }
                @for (act of actions(); track act.id) {
                  <div class="p-3 rounded-xl border transition-all"
                       [ngClass]="act.is_closed ? 'bg-slate-50 border-slate-100 opacity-60' : 'bg-white border-slate-200'">
                    <div class="flex items-start gap-2">
                      <button
                        (click)="!act.is_closed && closeAction(act)"
                        [disabled]="act.is_closed"
                        class="mt-0.5 flex-shrink-0 w-4 h-4 rounded border-2 flex items-center justify-center transition-colors"
                        [ngClass]="act.is_closed ? 'bg-emerald-500 border-emerald-500' : 'border-slate-300 hover:border-emerald-400'"
                      >
                        @if (act.is_closed) {
                          <mat-icon class="text-white text-[10px] leading-none">check</mat-icon>
                        }
                      </button>
                      <div class="flex-1 min-w-0">
                        <p class="text-[11px] font-medium text-slate-700 leading-snug" [ngClass]="act.is_closed ? 'line-through text-slate-400' : ''">{{ act.description }}</p>
                        <div class="flex items-center gap-2 mt-1.5 flex-wrap">
                          <span class="text-[9px] font-black px-2 py-0.5 rounded-full uppercase"
                                [ngClass]="actionAssigneeLabel(act).css">
                            {{ actionAssigneeLabel(act).label }}
                          </span>
                          @if (act.commit_date) {
                            <span class="text-[9px] font-bold text-slate-400 flex items-center gap-1">
                              <mat-icon class="text-[11px]">event</mat-icon>
                              {{ act.commit_date | localDate:'d MMM, HH:mm' }}
                            </span>
                          }
                          @if (act.is_closed && act.closed_date) {
                            <span class="text-[9px] font-bold text-emerald-600 flex items-center gap-1">
                              <mat-icon class="text-[11px]">done_all</mat-icon>
                              {{ act.closed_date | localDate:'d MMM, HH:mm' }}
                            </span>
                          }
                        </div>
                      </div>
                    </div>
                  </div>
                }
              </div>
            </div>

            <!-- ── RIGHT: Comments ── -->
            <div class="flex flex-col border-l border-slate-100 pl-6 min-h-0">
              <h4 class="text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] mb-4 flex-shrink-0">COMENTARIOS DEL TICKET</h4>

              <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar space-y-3 mb-4 pr-1">
                <div *ngIf="comments().length === 0" class="text-center py-8 text-slate-400 text-xs font-bold">Sin comentarios aún.</div>

                @for (c of comments(); track c.id) {
                  @if (c.author_id === SYSTEM_USER_ID) {
                    <!-- AI bubble — left -->
                    <div class="flex items-start gap-2">
                      <div class="w-7 h-7 rounded-lg bg-sky-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <mat-icon class="text-sky-500 text-[14px]">smart_toy</mat-icon>
                      </div>
                      <div class="max-w-[80%]">
                        <div class="bg-sky-50 border border-sky-100 rounded-xl rounded-tl-none px-3 py-2">
                          <span class="text-[9px] font-black text-sky-500 uppercase tracking-widest block mb-1">Interno AI</span>
                          <p class="text-[11px] text-slate-700 leading-relaxed">{{ c.content }}</p>
                          <span class="text-[9px] text-slate-400 block text-right mt-1">{{ formatCommentTime(c.created_at) }}</span>
                        </div>
                      </div>
                    </div>
                  } @else if (c.author_id === currentUserId()) {
                    <!-- Own message — right -->
                    <div class="flex justify-end">
                      <div class="max-w-[80%]">
                        <div class="bg-slate-800 rounded-xl rounded-tr-none px-3 py-2">
                          <span class="text-[9px] font-black text-sky-400 uppercase tracking-widest block mb-1">{{ currentUserName() }}</span>
                          <p class="text-[11px] text-white leading-relaxed">{{ c.content }}</p>
                          <span class="text-[9px] text-slate-400 block text-right mt-1">{{ formatCommentTime(c.created_at) }}</span>
                        </div>
                      </div>
                    </div>
                  } @else {
                    <!-- Other user — left -->
                    <div class="flex items-start gap-2">
                      <div class="w-7 h-7 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <mat-icon class="text-slate-400 text-[14px]">person</mat-icon>
                      </div>
                      <div class="max-w-[80%]">
                        <div class="bg-white border border-slate-200 rounded-xl rounded-tl-none px-3 py-2">
                          <span class="text-[9px] font-black text-amber-600 uppercase tracking-widest block mb-1">{{ getAuthorName(c.author_id) }}</span>
                          <p class="text-[11px] text-slate-700 leading-relaxed">{{ c.content }}</p>
                          <span class="text-[9px] text-slate-400 block text-right mt-1">{{ formatCommentTime(c.created_at) }}</span>
                        </div>
                      </div>
                    </div>
                  }
                }
              </div>

              <!-- Input -->
              <div class="flex items-end gap-2 border-t border-slate-100 pt-3 flex-shrink-0">
                <textarea
                  [ngModel]="newCommentText()"
                  (ngModelChange)="newCommentText.set($event)"
                  (keydown.enter)="onCommentEnter($event)"
                  placeholder="Escribe un comentario..."
                  rows="2"
                  class="flex-1 bg-slate-50 border border-slate-200 rounded-xl p-3 text-[11px] font-medium text-slate-800 outline-none focus:border-sky-400 transition-all resize-none placeholder:text-slate-300"
                ></textarea>
                <button
                  (click)="sendComment()"
                  [disabled]="!newCommentText().trim() || isAddingComment()"
                  class="w-9 h-9 flex-shrink-0 bg-sky-500 hover:bg-sky-600 disabled:opacity-40 text-white rounded-xl flex items-center justify-center transition-colors"
                >
                  <mat-icon class="text-[18px]">{{ isAddingComment() ? 'hourglass_empty' : 'send' }}</mat-icon>
                </button>
              </div>
            </div>

          </div>
        </ng-container>

      </div>


    </div>
  `,
  styles: [`
    .animate-fade-in { animation: fadeIn 0.3s ease-in-out; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
    .custom-scrollbar::-webkit-scrollbar { width: 4px; }
    .custom-scrollbar::-webkit-scrollbar-thumb { background: #E2E8F0; border-radius: 10px; }
  `]
})
export class TicketsFormComponent implements OnInit {
  private fb = inject(FormBuilder);
  private supportService = inject(SupportService);
  private notifications = inject(NotificationService);
  private adminService = inject(AdminService);
  private authService = inject(AuthService);
  drawerService = inject(SideDrawerService);
  deptService = inject(DepartmentService);

  readonly SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000000';

  // View State
  view = signal<'list' | 'form' | 'triage'>('list');
  
  // Data States
  tickets = signal<any[]>([]);
  selectedTicket = signal<any | null>(null);
  isLoadingTickets = signal<boolean>(false);
  isSaving = signal<boolean>(false);

  // Identity Search state
  techSearchQuery = signal<string>('');
  showTechDropdown = signal<boolean>(false);
  typeaheadIdentities = signal<any[]>([]);
  selectedIdentities = signal<any[]>([]);

  selectedTechnicianId = signal<string | null>(null);
  selectedCollaboratorId = signal<string | null>(null);
  selectedExternalContactId = signal<string | null>(null);

  triageComment = signal<string>('');
  private searchTimeout: any;

  // Comments state
  comments = signal<TicketComment[]>([]);
  isAddingComment = signal<boolean>(false);
  newCommentText = signal<string>('');
  userMap = signal<Record<string, string>>({});

  // Actions state
  actions = signal<TicketAction[]>([]);
  isLoadingActions = signal<boolean>(false);
  isAddingAction = signal<boolean>(false);
  newActionText = signal<string>('');
  newActionDate = signal<string>('');
  newActionTime = signal<string>('');
  showActionForm = signal<boolean>(false);
  currentUserId = computed(() => this.authService.session()?.user_id ?? '');
  currentUserName = computed(() => this.authService.session()?.user?.full_name ?? 'Yo');
  private _usersMapLoading = false;
  private _usersMapLoaded = false;

  ticketForm: FormGroup = this.fb.group({
    title: ['', [Validators.required, Validators.minLength(5)]],
    description: ['', [Validators.required, Validators.minLength(10)]],
    priority: ['Media', Validators.required],
    area: ['Sistemas', Validators.required]
  });

  // Data receiving interface from SideDrawer setup
  set data(val: any) {
    if (!val?.id) return;
    this.selectedTicket.set(val);
    this.view.set('triage');
    this.clearTechSelection();
    this.triageComment.set('');
    this.comments.set(val.comments || []);
    this.actions.set([]);
    this.showActionForm.set(false);
    this._prePopulateAssignment(val);
    setTimeout(() => this.loadActions(val.id), 0);
  }

  ngOnInit(): void {
    if (this.view() !== 'triage') {
      this.loadTickets();
    }
    this.loadUsersMap();
    this.deptService.load(true); // solo activos
  }

  switchView(newView: 'list' | 'form' | 'triage') {
    this.view.set(newView);
    if (newView === 'form') {
      const firstDept = this.deptService.departments()[0]?.name ?? '';
      this.ticketForm.reset({ priority: 'Media', area: firstDept });
    }
  }

  async loadTickets() {
    this.isLoadingTickets.set(true);
    try {
      await this.supportService.loadTickets();
      this.tickets.set(this.supportService.tickets());
    } catch (error) {
      this.notifications.error('Error', 'No se pudieron cargar los tickets.');
    } finally {
      this.isLoadingTickets.set(false);
    }
  }

  openTriage(ticket: any) {
    this.selectedTicket.set(ticket);
    this.view.set('triage');
    this.clearTechSelection();
    this.triageComment.set('');
    this.comments.set(ticket.comments || []);
    this.actions.set([]);
    this.showActionForm.set(false);
    this._prePopulateAssignment(ticket);
    this.loadActions(ticket.id);
  }

  private _prePopulateAssignment(ticket: any) {
    // untracked prevents creating a reactive dependency on userMap when called
    // inside the SideDrawer effect context (via set data(val)), which would cause
    // the effect to re-run every time loadUsersMap() sets the map → infinite loop.
    const map = untracked(() => this.userMap());
    const identities: any[] = [];

    const assignees: any[] = ticket.assignees ?? [];
    if (assignees.length > 0) {
      for (const a of assignees) {
        const type = a.identity_type as 'INTERNAL' | 'PLANTA' | 'EXTERNO';
        let label = type === 'INTERNAL' ? (map[a.identity_id] || 'Usuario') :
                    type === 'PLANTA'   ? 'Colaborador' : 'Externo';
        identities.push({ id: a.identity_id, type, label, sub: a.identity_id.slice(-6) });
      }
    } else {
      // Fallback a 3 columnas legacy mientras se migra data
      if (ticket.assigned_to_id) {
        const name = map[ticket.assigned_to_id] || 'Usuario asignado';
        identities.push({ id: ticket.assigned_to_id, type: 'INTERNAL', label: name, sub: '' });
      }
      if (ticket.collaborator_id) {
        identities.push({ id: ticket.collaborator_id, type: 'PLANTA', label: 'Colaborador', sub: ticket.collaborator_id.slice(-6) });
      }
      if (ticket.external_contact_id) {
        identities.push({ id: ticket.external_contact_id, type: 'EXTERNO', label: 'Externo', sub: '' });
      }
    }

    if (identities.length > 0) {
      this.selectedIdentities.set(identities);
      this._syncIds();
    }
  }

  async onTechSearchChange(value: string) {
    this.techSearchQuery.set(value);
    if (!value) {
      this.clearTechSelection();
    } else {
      if (this.searchTimeout) clearTimeout(this.searchTimeout);
      this.searchTimeout = setTimeout(async () => {
        const results = await this.supportService.searchIdentities(value);
        this.typeaheadIdentities.set(results);
      }, 300);
    }
    this.showTechDropdown.set(true);
  }

  selectIdentity(identity: any) {
    this.selectedIdentities.update(list => {
      const alreadyIn = list.some(i => i.id === identity.id && i.type === identity.type);
      return alreadyIn ? list : [...list, identity];
    });
    this._syncIds();
    this.techSearchQuery.set('');
    this.typeaheadIdentities.set([]);
    this.showTechDropdown.set(false);
  }

  removeIdentity(identity: any) {
    this.selectedIdentities.update(list => list.filter(i => !(i.id === identity.id && i.type === identity.type)));
    this._syncIds();
  }

  private _syncIds() {
    // untracked: _syncIds is called from _prePopulateAssignment which can run inside
    // the SideDrawer effect context. Reading selectedIdentities() there would make it
    // a reactive dependency — causing the effect to re-run every time loadUsersMap()
    // updates the chips → infinite form destroy/recreate loop.
    const all = untracked(() => this.selectedIdentities());
    this.selectedTechnicianId.set(all.find(i => i.type === 'INTERNAL')?.id ?? null);
    this.selectedCollaboratorId.set(all.find(i => i.type === 'PLANTA')?.id ?? null);
    this.selectedExternalContactId.set(all.find(i => i.type === 'EXTERNO')?.id ?? null);
  }

  clearTechSelection() {
    this.selectedIdentities.set([]);
    this.selectedTechnicianId.set(null);
    this.selectedCollaboratorId.set(null);
    this.selectedExternalContactId.set(null);
    this.techSearchQuery.set('');
    this.typeaheadIdentities.set([]);
  }

  async submitTriage() {
    const ticket = this.selectedTicket();
    if (!ticket || this.selectedIdentities().length === 0) return;

    const assignees = this.selectedIdentities().map((id, idx) => ({
      identity_type: id.type as 'INTERNAL' | 'PLANTA' | 'EXTERNO',
      identity_id: id.id,
      is_lead: idx === 0,
    }));

    this.isSaving.set(true);
    try {
      await this.supportService.triageTicket(
        ticket.id,
        'REASSIGN',
        assignees,
        this.triageComment(),
      );

      this.notifications.success('Éxito', 'Asignación guardada.');
      this.triageComment.set('');

      // Refresh ticket data to show updated comments — stay in triage view
      const fresh = await this.supportService.getTicket(ticket.id);
      if (fresh) {
        this.selectedTicket.set(fresh);
        this.comments.set(fresh.comments || []);
        // Keep chips but update labels from refreshed data
        this._prePopulateAssignment(fresh);
      }

      this.loadTickets();
      this.drawerService.notifyRefresh();
    } catch (err: any) {
      this.notifications.error('Error', err.message || 'Error al procesar triaje');
    } finally {
      this.isSaving.set(false);
    }
  }

  async sendComment() {
    const text = this.newCommentText().trim();
    const ticket = this.selectedTicket();
    if (!text || !ticket) return;
    this.isAddingComment.set(true);
    try {
      const newMsg = await this.supportService.addMessage(ticket.id, text);
      this.newCommentText.set('');
      if (newMsg) {
        this.comments.update(ms => [...ms, newMsg]);
      } else {
        const msgs = await this.supportService.getMessages(ticket.id);
        this.comments.set(msgs);
      }
    } catch {
      this.notifications.error('Error', 'No se pudo enviar el comentario.');
    } finally {
      this.isAddingComment.set(false);
    }
  }

  async loadUsersMap() {
    if (this._usersMapLoading || this._usersMapLoaded) return;
    this._usersMapLoading = true;
    try {
      const { firstValueFrom } = await import('rxjs');
      const res = await firstValueFrom(this.adminService.getUsers());
      if (res.data) {
        const map: Record<string, string> = {};
        res.data.forEach(u => { map[u.id] = u.full_name; });
        this.userMap.set(map);
        // Re-populate chips now that user names are available
        const ticket = this.selectedTicket();
        if (ticket && this.view() === 'triage') {
          this._prePopulateAssignment(ticket);
        }
      }
    } catch { /* non-critical */ }
    finally {
      this._usersMapLoading = false;
      this._usersMapLoaded = true; // mark done even if empty — prevents retry loop
    }
  }

  getAuthorName(authorId: string): string {
    return this.userMap()[authorId] || 'Usuario';
  }

  onCommentEnter(event: Event) {
    if (!(event as KeyboardEvent).shiftKey) {
      event.preventDefault();
      this.sendComment();
    }
  }

  formatCommentTime(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleString('es-MX', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  }

  getPriorityColor(priority: string): string {
    const p = (priority || '').toUpperCase();
    if (p.includes('ALTA') || p.includes('CRIT')) return 'bg-red-500';
    if (p.includes('MEDIA')) return 'bg-amber-500';
    return 'bg-emerald-500';
  }

  getPriorityColorClass(priority: string): string {
    const p = (priority || '').toUpperCase();
    if (p.includes('ALTA') || p.includes('CRIT')) return 'bg-red-50 text-red-600';
    if (p.includes('MEDIA')) return 'bg-amber-50 text-amber-600';
    return 'bg-emerald-50 text-emerald-600';
  }

  async loadActions(ticketId: string) {
    this.isLoadingActions.set(true);
    try {
      const acts = await this.supportService.getActions(ticketId);
      this.actions.set(acts);
    } finally {
      this.isLoadingActions.set(false);
    }
  }

  async addAction() {
    const text = this.newActionText().trim();
    if (!text || this.isAddingAction()) return;
    const ticket = this.selectedTicket();
    if (!ticket) return;

    const assignee = untracked(() => this.selectedIdentities())[0];
    if (!assignee) {
      this.notifications.error('Sin responsable', 'Asigna primero al menos un responsable al ticket.');
      return;
    }

    const payload: any = { description: text };
    if (assignee.type === 'INTERNAL') payload.assigned_to_id = assignee.id;
    else if (assignee.type === 'PLANTA') payload.collaborator_id = assignee.id;
    else payload.external_contact_id = assignee.id;
    if (this.newActionDate()) {
      const time = this.newActionTime() || '00:00';
      payload.commit_date = new Date(`${this.newActionDate()}T${time}:00`).toISOString();
    }

    this.isAddingAction.set(true);
    try {
      const created = await this.supportService.createAction(ticket.id, payload);
      this.actions.update(list => [...list, created]);
      this.newActionText.set('');
      this.newActionDate.set('');
      this.newActionTime.set('');
      this.showActionForm.set(false);
    } catch (err: any) {
      this.notifications.error('Error', err.message || 'No se pudo crear la acción');
    } finally {
      this.isAddingAction.set(false);
    }
  }

  async closeAction(action: TicketAction) {
    const ticket = this.selectedTicket();
    if (!ticket) return;
    try {
      const updated = await this.supportService.closeAction(ticket.id, action.id);
      this.actions.update(list => list.map(a => a.id === updated.id ? updated : a));
    } catch (err: any) {
      this.notifications.error('Error', 'No se pudo cerrar la acción');
    }
  }

  actionAssigneeLabel(action: TicketAction): { label: string; css: string } {
    const map = untracked(() => this.userMap());
    if (action.assigned_to_id) {
      return { label: map[action.assigned_to_id] || 'INTERNO', css: 'bg-sky-100 text-sky-700' };
    }
    if (action.collaborator_id) return { label: 'PLANTA', css: 'bg-amber-100 text-amber-700' };
    if (action.external_contact_id) return { label: 'EXTERNO', css: 'bg-purple-100 text-purple-700' };
    return { label: 'SIN ASIGNAR', css: 'bg-slate-100 text-slate-500' };
  }

  async save() {
    if (this.ticketForm.invalid || this.isSaving()) return;
    this.isSaving.set(true);
    try {
      await this.supportService.createTicket(
        this.ticketForm.value.title,
        this.ticketForm.value.description,
        this.ticketForm.value.priority,
        this.ticketForm.value.area
      );
      this.notifications.success('Éxito', 'Ticket creado correctamente.');
      this.loadTickets();
      this.switchView('list');
      this.drawerService.notifyRefresh();
    } catch (err: any) {
      this.notifications.error('Error', 'No se pudo crear el ticket.');
    } finally {
      this.isSaving.set(false);
    }
  }
}
