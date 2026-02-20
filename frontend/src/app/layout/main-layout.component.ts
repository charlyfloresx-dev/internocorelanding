
import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../components/sidebar/sidebar.component'; // ✅ Correcto si estás en /layout
import { HeaderComponent } from '../components/header/header.component'; // ✅ Correcto si estás en /layout

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, HeaderComponent],
  template: `
    <div class="flex h-screen overflow-hidden bg-slate-950 relative">
      
      <!-- Desktop Sidebar (Hidden on mobile) -->
      <aside class="hidden lg:block z-50 flex-shrink-0 w-20 relative">
        <app-sidebar></app-sidebar>
      </aside>

      <!-- Mobile Sidebar Drawer (Overlay) -->
      @if (isMobileMenuOpen()) {
        <div class="fixed inset-0 z-[100] lg:hidden flex">
           <!-- Backdrop: High transparency (30%) and low blur to see content changes -->
           <div class="absolute inset-0 bg-black/30 backdrop-blur-[2px] transition-opacity" (click)="closeMobileMenu()"></div>

           <!-- Sidebar Container -->
           <div class="relative z-10 h-full animate-slide-in-left shadow-2xl">
              <app-sidebar></app-sidebar>
           </div>
        </div>
      }

      <!-- Main Content Wrapper -->
      <div class="flex flex-col flex-1 h-full min-w-0 overflow-hidden relative z-0">
        <app-header (toggleMenu)="toggleMobileMenu()"></app-header>
        
        <!-- Scrollable Content -->
        <main class="flex-1 overflow-y-auto p-0 scroll-smooth">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `
})
export class MainLayoutComponent {
  isMobileMenuOpen = signal(false);

  toggleMobileMenu() {
    this.isMobileMenuOpen.update(v => !v);
  }

  closeMobileMenu() {
    this.isMobileMenuOpen.set(false);
  }
}
