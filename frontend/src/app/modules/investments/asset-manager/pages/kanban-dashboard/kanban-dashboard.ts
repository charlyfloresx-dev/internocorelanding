import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CdkDragDrop, DragDropModule, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { OpportunityCardComponent } from '../../components/opportunity-card/opportunity-card';
import { KanbanBoard, OpportunityResponse } from '../../models/opportunity.model';
import { AssetCrmService } from '../../services/asset-crm';

@Component({
  selector: 'app-kanban-dashboard',
  standalone: true,
  imports: [CommonModule, DragDropModule, OpportunityCardComponent],
  templateUrl: './kanban-dashboard.html',
  styleUrls: ['./kanban-dashboard.css']
})
export class KanbanDashboardComponent implements OnInit {
  private crmService = inject(AssetCrmService);
  
  // Señal principal que mantiene el estado del tablero original
  private _rawBoard = signal<KanbanBoard | null>(null);

  // Filtro de Zonas Calientes
  selectedZone = signal<string>('ALL');
  availableZones = ['ALL', 'PRESIDENTES', 'OTAY', 'ZONA RIO', 'CENTRO'];

  // Tablero computado basado en el filtro
  board = computed(() => {
    const b = this._rawBoard();
    const zone = this.selectedZone();
    
    if (!b) return null;
    if (zone === 'ALL') return b;

    return {
      ...b,
      columns: b.columns.map(col => ({
        ...col,
        opportunities: col.opportunities.filter(opp => 
          opp.address.toUpperCase().includes(zone)
        )
      }))
    };
  });

  // Computado: ROI Promedio o Total Inversión Requerida (para el Header)
  totalProjectedRoi = computed(() => {
    const currentBoard = this.board();
    if (!currentBoard) return 0;
    
    let totalRoi = 0;
    let count = 0;
    
    // Calculamos el ROI promedio de las oportunidades activas (DETECTED e IN_ANALYSIS)
    currentBoard.columns.forEach(col => {
      if (col.id !== 'DISCARDED' && col.id !== 'EXECUTED') {
        col.opportunities.forEach(opp => {
          totalRoi += opp.roi_projected;
          count++;
        });
      }
    });
    
    return count > 0 ? (totalRoi / count) : 0;
  });

  ngOnInit() {
    this.loadBoard();
  }

  loadBoard() {
    this.crmService.getKanbanBoard().subscribe(data => {
      this._rawBoard.set(data);
    });
  }

  setZone(zone: string) {
    this.selectedZone.set(zone);
  }

  drop(event: CdkDragDrop<OpportunityResponse[]>, columnId: string) {
    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex,
      );
      
      // La oportunidad movida
      const movedOpp = event.container.data[event.currentIndex];
      
      // Actualizamos el backend de forma asíncrona (Optimistic UI)
      this.crmService.updateOpportunityStatus(movedOpp.id, columnId).subscribe();
      
      // Forzamos actualización de la señal base para que los computed se recalculen
      this._rawBoard.update(b => ({ ...b! }));
    }
  }
}
