import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminAuthService } from '@services/admin-auth.service';
import { AdminRescueService } from '@services/admin-rescue.service';
import { GodModeIntervention } from '@models/api.types';

@Component({
    selector: 'app-admin-god-mode',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './admin-god-mode.component.html',
    styleUrl: './admin-god-mode.component.css'
})
export class AdminGodModeComponent {
    private adminAuthService = inject(AdminAuthService);
    private rescueService = inject(AdminRescueService);

    isModalOpen = !this.adminAuthService.isGodModeEnabled();
    masterKeyInput = '';

    // Data para formularios
    rescueTarget = {
        userId: '',
        companyId: '',
        roleId: ''
    };

    subscriptionOverride = {
        companyId: '',
        days: 7
    };

    interventions: GodModeIntervention[] = [];

    get isGodModeActive() {
        return this.adminAuthService.isGodModeEnabled();
    }

    activateGodMode() {
        if (this.masterKeyInput.trim()) {
            this.adminAuthService.enableGodMode(this.masterKeyInput);
            this.isModalOpen = false;
        }
    }

    deactivateGodMode() {
        this.adminAuthService.disableGodMode();
        this.isModalOpen = true;
    }

    runForceAssign() {
        const { userId, companyId, roleId } = this.rescueTarget;
        if (!userId || !companyId || !roleId) return;

        this.rescueService.forceAssignUser(userId, companyId, roleId).subscribe({
            next: (res) => {
                alert('Asignación forzada completada con éxito.');
                this.addInterventionLog('FORCE_ASSIGN_USER', userId, companyId, res.data.transaction_id || 'N/A');
            },
            error: (err) => alert('Error en la asignación: ' + (err.error?.message || err.message))
        });
    }

    runOverrideGrace() {
        const { companyId, days } = this.subscriptionOverride;
        if (!companyId || !days) return;

        this.rescueService.overrideGracePeriod(companyId, days).subscribe({
            next: (res) => {
                alert('Periodo de gracia extendido con éxito.');
                this.addInterventionLog('OVERRIDE_GRACE', companyId, companyId, res.data.transaction_id || 'N/A');
            },
            error: (err) => alert('Error en la extensión: ' + (err.error?.message || err.message))
        });
    }

    private addInterventionLog(action: string, targetId: string, companyId: string, txId: string) {
        this.interventions.unshift({
            action,
            target_id: targetId,
            company_id: companyId,
            timestamp: new Date().toISOString(),
            transaction_id: txId
        });
    }
}
