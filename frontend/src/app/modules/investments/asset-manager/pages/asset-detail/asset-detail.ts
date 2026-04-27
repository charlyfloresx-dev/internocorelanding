import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule, CurrencyPipe, PercentPipe } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { OpportunityResponse, KanbanBoard } from '../../models/opportunity.model';
import { AssetCrmService } from '../../services/asset-crm';

@Component({
  selector: 'app-asset-detail',
  standalone: true,
  imports: [CommonModule, CurrencyPipe, PercentPipe, MatIconModule, RouterModule],
  templateUrl: './asset-detail.html',
  styleUrls: ['./asset-detail.css']
})
export class AssetDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private assetCrmService = inject(AssetCrmService);

  asset = signal<OpportunityResponse | null>(null);
  loading = signal<boolean>(true);

  // Mock de datos extendidos (Vendrían del backend en el futuro)
  extendedData = signal({
    valor_terreno: { amount: 1250000, currency: 'MXN' },
    valor_construccion: { amount: 850000, currency: 'MXN' },
    uso_suelo: 'INDUSTRIAL - ALTA DENSIDAD',
    superficie_construccion: 450,
    predial_status: 'ADEUDO 4 AÑOS',
    gravamen: 'LIBRE DE GRAVAMEN'
  });

  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    if (id) {
      this.loadAsset(id);
    }
  }

  async loadAsset(id: string) {
    this.loading.set(true);
    // Por ahora usamos el mock del servicio filtrado por ID
    setTimeout(() => {
      this.assetCrmService.getKanbanBoard().subscribe((board: KanbanBoard) => {
        for (const col of board.columns) {
          const found = col.opportunities.find((o: OpportunityResponse) => o.id === id);
          if (found) {
            this.asset.set(found);
            break;
          }
        }
        this.loading.set(false);
      });
    }, 800);
  }
}
