import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TinderSwipeComponent } from '../components/tinder-swipe/tinder-swipe.component';
import { KioskService } from '../../../core/services/kiosk.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-approval-page',
  standalone: true,
  imports: [CommonModule, TinderSwipeComponent],
  template: `
    <div class="h-full flex flex-col pt-8 bg-brand-dark px-4">
      <div class="mb-6 flex flex-col px-4">
        <h2 class="text-white text-3xl font-black italic uppercase leading-none mb-1 tracking-tighter">Aprobación</h2>
        
        <div class="bg-brand-surface border border-white/10 rounded-2xl p-4 mt-4 flex items-center justify-between">
           <div>
              <p class="text-brand-primary text-[10px] font-black uppercase tracking-widest">Rol Activo</p>
              <h3 class="text-white font-bold uppercase transition-all">Aprobador #{{approverIndex}}</h3>
           </div>
           <div class="flex flex-col items-end">
              <span class="material-icons text-brand-primary">verified_user</span>
              <p class="text-white/40 text-[10px] mt-1">{{kiosk.pendingPhotos().length}} Pendientes</p>
           </div>
        </div>

        <!-- Quorum Info (Generic context) -->
        <p class="text-white/50 text-[10px] italic mt-4 px-2">
          * Para que una foto sea pública, requiere la validación de todos los jefes designados.
        </p>
      </div>

      <app-tinder-swipe 
        [photos]="kiosk.pendingPhotos()"
        [approverIndex]="approverIndex"
        (onApprove)="handleApprove($event)"
        (onReject)="handleReject($event)">
      </app-tinder-swipe>
    </div>
  `
})
export class ApprovalPageComponent implements OnInit {
  kiosk = inject(KioskService);
  route = inject(ActivatedRoute);
  approverIndex = 1;

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      this.approverIndex = +params['approver'] || 1;
    });

    const config = this.kiosk.getEventConfig();
    this.kiosk.fetchPending(config.event_id);
  }

  handleApprove(id: string) {
    this.kiosk.reviewPhoto(id, this.approverIndex, 'APPROVE').subscribe((res) => {
        if (res.photo_state === 'APPROVED') {
           import('../../../core/utils/celebrate').then(m => m.celebrate());
        }
        this.kiosk.pendingPhotos.set(this.kiosk.pendingPhotos().slice(1));
    });
  }

  handleReject(id: string) {
    this.kiosk.reviewPhoto(id, this.approverIndex, 'REJECT').subscribe(() => {
        this.kiosk.pendingPhotos.set(this.kiosk.pendingPhotos().slice(1));
    });
  }
}
