import { Component, Input, computed, signal } from '@angular/core';
import { CommonModule, CurrencyPipe, PercentPipe } from '@angular/common';
import { OpportunityResponse } from '../../models/opportunity.model';

import { MatIconModule } from '@angular/material/icon';
import { RouterModule } from '@angular/router';

@Component({
  selector: 'app-opportunity-card',
  standalone: true,
  imports: [CommonModule, CurrencyPipe, PercentPipe, MatIconModule, RouterModule],
  templateUrl: './opportunity-card.html',
  styleUrls: ['./opportunity-card.css']
})
export class OpportunityCardComponent {
  @Input({ required: true }) set opportunity(val: OpportunityResponse) {
    this._opportunity.set(val);
  }
  
  private _opportunity = signal<OpportunityResponse | null>(null);
  
  // Exponemos la señal calculada para la vista
  opp = this._opportunity;

  // Lógica de "Semáforo"
  // Verde: ROI > 30%
  // Amarillo: ROI 20-30%
  // Rojo: ROI < 20%
  trafficLightClass = computed(() => {
    const data = this._opportunity();
    if (!data) return 'bg-gray-800 border-gray-700';
    
    if (data.roi_projected > 0.3) {
      return 'border-emerald-500/30 hover:border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.05)]';
    } else if (data.roi_projected >= 0.2) {
      return 'border-amber-500/30 hover:border-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.05)]';
    } else {
      return 'border-rose-500/30 hover:border-rose-500 shadow-[0_0_20px_rgba(244,63,94,0.05)]';
    }
  });

  statusBadgeClass = computed(() => {
    const data = this._opportunity();
    if (!data) return '';
    return data.owner_name && !data.owner_name.includes('No disponible') 
      ? 'border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400' 
      : 'border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400';
  });
}
