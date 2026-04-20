import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { AuthService } from '@services/auth.service';

@Component({
  selector: 'app-setup-warehouse',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <div class="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md">
        <div class="text-center">
          <h1 class="text-3xl font-bold text-gray-800">Welcome to Interno Core!</h1>
          <p class="mt-2 text-gray-600">Let's get your first warehouse set up.</p>
        </div>
        
        <!-- Placeholder for future form -->
        <div class="p-4 border-2 border-dashed rounded-lg">
          <p class="text-center text-gray-500">Warehouse configuration form will be here.</p>
        </div>

        <button 
          (click)="completeSetup()" 
          [disabled]="isLoading()"
          class="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400">
          {{ isLoading() ? 'Completing...' : 'Complete Initial Setup' }}
        </button>
      </div>
    </div>
  `,
})
export class SetupWarehouseComponent {
  private authService = inject(AuthService);
  private router = inject(Router);
  isLoading = signal(false);

  completeSetup() {
    this.isLoading.set(true);
    this.authService.completeOnboarding().subscribe({
      next: () => {
        console.log('[Onboarding] Backend status updated successfully.');
        this.authService.updateCompanyIsNewStatus(false);
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        console.error('[Onboarding] Failed to update backend status:', err);
        // TODO: Show a toast message to the user
        this.isLoading.set(false);
      },
      complete: () => {
        this.isLoading.set(false);
      }
    });
  }
}