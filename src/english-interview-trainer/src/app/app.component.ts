import { Component } from '@angular/core';
import { MainTrainerComponent } from './components/main-trainer/main-trainer.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [MainTrainerComponent],
  template: `<app-main-trainer></app-main-trainer>`
})
export class AppComponent {}
