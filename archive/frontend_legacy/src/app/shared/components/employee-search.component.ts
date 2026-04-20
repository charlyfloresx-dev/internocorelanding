
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { ApiSimulationService } from '@services/api-simulation.service';
import { Employee } from '@models/api.types';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { debounceTime, distinctUntilChanged, switchMap, filter, tap, finalize } from 'rxjs/operators';

@Component({
  selector: 'app-employee-search',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="relative w-full group">
      <!-- Search Input Container -->
      <div class="relative flex items-center bg-slate-900 border border-slate-700 rounded-full transition-all duration-300 focus-within:border-sky-500 focus-within:ring-1 focus-within:ring-sky-500 shadow-inner">
        
        <div class="pl-3 text-slate-500 group-focus-within:text-sky-400 transition-colors pointer-events-none">
          @if (loading()) {
            <i class="fa-solid fa-circle-notch fa-spin"></i>
          } @else {
            <i class="fa-solid fa-search"></i>
          }
        </div>

        <input 
          [formControl]="searchControl"
          type="text" 
          class="w-full bg-transparent border-none text-sm text-white placeholder-slate-500 focus:ring-0 px-3 py-2 leading-tight" 
          placeholder="Search employees (Type 'G' to test)...">

        @if (searchControl.value) {
          <button (click)="clear()" class="pr-3 text-slate-500 hover:text-white transition-colors">
            <i class="fa-solid fa-times-circle"></i>
          </button>
        }
      </div>

      <!-- Dropdown Results -->
      @if (showResults && results().length > 0) {
        <div class="absolute top-full left-0 w-full mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl z-50 overflow-hidden animate-fade-in-up">
          <div class="px-3 py-2 bg-slate-900/50 border-b border-slate-700 flex justify-between items-center">
            <span class="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Results</span>
            <span class="text-[10px] text-slate-600">{{ results().length }} found</span>
          </div>
          
          <ul class="max-h-60 overflow-y-auto custom-scrollbar">
            @for (emp of results(); track emp.id) {
              <li class="px-4 py-3 hover:bg-slate-700 cursor-pointer transition-colors border-l-2 border-transparent hover:border-sky-500 flex items-center gap-3 group/item">
                <img [src]="emp.avatar" class="w-8 h-8 rounded-full border border-slate-600 group-hover/item:border-sky-400">
                <div class="flex-1 min-w-0">
                  <div class="text-sm font-bold text-slate-200 group-hover/item:text-white truncate">{{ emp.name }}</div>
                  <div class="text-xs text-slate-500 truncate">{{ emp.position }} &bull; {{ emp.department }}</div>
                </div>
                <i class="fa-solid fa-chevron-right text-slate-600 opacity-0 group-hover/item:opacity-100 transition-opacity"></i>
              </li>
            }
          </ul>
        </div>
      }

      <!-- No Results State -->
      @if (showResults && results().length === 0 && searchControl.value && !loading()) {
        <div class="absolute top-full left-0 w-full mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl p-4 text-center z-50">
          <i class="fa-solid fa-user-slash text-slate-600 text-xl mb-2"></i>
          <p class="text-sm text-slate-400">No employees found.</p>
        </div>
      }
    </div>
  `
})
export class EmployeeSearchComponent {
  private api = inject(ApiSimulationService);
  
  searchControl = new FormControl('');
  results = signal<Employee[]>([]);
  loading = signal(false);
  showResults = false;

  constructor() {
    this.searchControl.valueChanges.pipe(
      takeUntilDestroyed(),
      // 1. Wait 1000ms after user stops typing (RxJS requirement)
      debounceTime(1000), 
      // 2. Ignore if same value
      distinctUntilChanged(),
      tap(() => {
        this.loading.set(true);
        this.showResults = true;
      }),
      // 3. Cancel previous request if new value comes in
      switchMap((query: string | null) => {
        if (!query || query.length < 2) {
          return Promise.resolve({ status: 'success', data: [] });
        }
        return this.api.searchEmployees(query);
      }),
      // Finalize: Turn off loader regardless of success/error
      tap(() => this.loading.set(false))
    ).subscribe({
      next: (response: any) => {
        if (response.status === 'success') {
          this.results.set(response.data);
        }
      },
      error: () => {
        this.loading.set(false);
        this.results.set([]);
      }
    });
  }

  clear() {
    this.searchControl.setValue('');
    this.results.set([]);
    this.showResults = false;
  }
}
