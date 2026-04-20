import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  template: `
    <div style="padding: 2rem;">
      <h1>Welcome to Viatra Core Dashboard</h1>
      <p>Mission Control active.</p>
    </div>
  `,
  styles: [`
    h1 { color: var(--accent-cyan); }
  `]
})
export class DashboardComponent {}
