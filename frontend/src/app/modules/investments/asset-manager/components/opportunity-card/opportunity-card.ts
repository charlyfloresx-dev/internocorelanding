import { Component, Input, computed, signal } from '@angular/core';
import { CommonModule, CurrencyPipe, PercentPipe } from '@angular/common';
import { OpportunityResponse } from '../../models/opportunity.model';

@Component({
  selector: 'app-opportunity-card',
  standalone: true,
  imports: [CommonModule, CurrencyPipe, PercentPipe],
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
      return 'glass-card border-green-500/50 hover:border-green-400 shadow-[0_0_15px_rgba(34,197,94,0.15)]';
    } else if (data.roi_projected >= 0.2) {
      return 'glass-card border-yellow-500/50 hover:border-yellow-400 shadow-[0_0_15px_rgba(234,179,8,0.15)]';
    } else {
      return 'glass-card border-red-500/50 hover:border-red-400 shadow-[0_0_15px_rgba(239,68,68,0.15)]';
    }
  });

  statusBadgeClass = computed(() => {
    const data = this._opportunity();
    if (!data) return '';
    return data.owner_name && !data.owner_name.includes('No disponible') 
      ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' 
      : 'bg-amber-500/20 text-amber-300 border-amber-500/30';
  });
}
