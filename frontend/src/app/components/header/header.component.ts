
import { Component, inject, output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '@services/auth.service';
import { EmployeeSearchComponent } from '../../shared/components/employee-search.component';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, EmployeeSearchComponent],
  template: `
    <header [class]="'h-16 bg-slate-800 shadow-md flex items-center justify-between px-6 z-30 relative border-t-4 ' + getBorderColor()">
      
      <!-- Left: Navigation Controls -->
      <div class="flex items-center gap-4">
        
        <!-- Mobile Menu Trigger -->
        <button (click)="toggleMenu.emit()" class="lg:hidden text-slate-400 hover:text-white transition-colors focus:outline-none">
          <i class="fa-solid fa-bars text-xl"></i>
        </button>

        <!-- Breadcrumbs -->
        <div class="flex items-center gap-2 text-sm">
          <div class="hidden sm:flex w-8 h-8 rounded bg-slate-700 items-center justify-center text-slate-300">
            <i class="fa-solid fa-building"></i>
          </div>
          <div class="flex items-center text-slate-400">
             <span class="hover:text-white cursor-pointer transition-colors hidden sm:inline">{{ auth.activeCompany()?.name }}</span>
             <i class="fa-solid fa-chevron-right text-[10px] mx-2 opacity-50 hidden sm:inline"></i>
             <span class="text-white font-medium">Production</span>
          </div>
        </div>
      </div>

      <!-- Center: Global Employee Search (Shared Component) -->
      <div class="hidden md:block w-96">
        <app-employee-search></app-employee-search>
      </div>

      <!-- Right: Context Selectors -->
      <div class="flex items-center gap-4">
        
        <!-- Line Selector -->
        <div class="hidden lg:flex items-center px-3 py-1.5 rounded bg-slate-900 border border-slate-700 text-sm text-slate-300 cursor-pointer hover:border-slate-500 transition-colors">
          <i class="fa-solid fa-industry mr-2 text-slate-500"></i>
          <span>Line A-04</span>
          <i class="fa-solid fa-caret-down ml-2 text-xs"></i>
        </div>

        <!-- Date -->
        <div class="hidden lg:flex items-center px-3 py-1.5 rounded-full bg-slate-900 text-xs font-mono text-sky-400 border border-slate-700">
           <i class="fa-regular fa-calendar mr-2"></i> Oct 24
        </div>

        <div class="h-8 w-px bg-slate-700 mx-2 hidden sm:block"></div>

        <!-- Notifications -->
        <button class="relative w-8 h-8 rounded-full bg-slate-700 hover:bg-slate-600 flex items-center justify-center text-slate-300 transition-colors">
          <i class="fa-regular fa-bell"></i>
          <span class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border-2 border-slate-800"></span>
        </button>
      </div>
    </header>
  `
})
export class HeaderComponent {
  auth = inject(AuthService);
  toggleMenu = output<void>();
  
  getBorderColor(): string {
    const id = this.auth.activeCompany()?.id;
    if (id === '0c176b7e-d2d8-4da0-83e4-94150e967d82') return 'border-amber-500'; // Interno Logistics
    if (id === 'a79f7800-0a53-421e-b5a9-7b45da85dec1') return 'border-sky-500';   // InternoCorp Enterprise
    return 'border-slate-600';
  }
}
