import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class JobService {
  readonly vacancyText = signal<string>(localStorage.getItem('trainer_vacancy') || '');

  setVacancy(text: string) {
    this.vacancyText.set(text);
    localStorage.setItem('trainer_vacancy', text);
  }

  getKeywords(): string[] {
    const text = this.vacancyText().toLowerCase();
    const allKeywords = ['tulip', 'python', 'sql', 'mes', 'sap', 'traceability', 'wip', 'cloud', 'iot', 'api', 'etl', 'manufacturing'];
    return allKeywords.filter(kw => text.includes(kw));
  }
}
