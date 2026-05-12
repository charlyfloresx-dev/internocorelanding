import { Injectable, signal } from '@angular/core';

export interface UserProfile {
  name: string;
  targetRole: string;
  experienceLevel: 'junior' | 'mid' | 'senior';
  industry: string;
  linkedinUrl?: string;
  profileText?: string;
  enrichmentAnswers?: { question: string, answer: string }[];
}

@Injectable({ providedIn: 'root' })
export class ProfileService {
  readonly profile = signal<UserProfile>({
    name: 'Carlos Flores',
    targetRole: 'Senior Developer Engineer',
    experienceLevel: 'senior',
    industry: 'Software Development',
    enrichmentAnswers: []
  });

  updateProfile(newProfile: Partial<UserProfile>) {
    this.profile.update(p => ({ ...p, ...newProfile }));
    localStorage.setItem('trainer_profile', JSON.stringify(this.profile()));
  }

  clearProfile() {
    localStorage.removeItem('trainer_profile');
    this.profile.set({
      name: 'Carlos Flores',
      targetRole: 'Senior Developer Engineer',
      experienceLevel: 'senior',
      industry: 'Software Development',
      enrichmentAnswers: []
    });
  }

  constructor() {
    const saved = localStorage.getItem('trainer_profile');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.profile.set({ ...this.profile(), ...parsed });
      } catch (e) {}
    }
  }
}
