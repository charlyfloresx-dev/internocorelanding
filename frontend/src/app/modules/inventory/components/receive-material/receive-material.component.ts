import { Component, inject, OnInit, ViewChild, ElementRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { InventoryService } from '../../../../core/services/inventory.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { Subject } from 'rxjs';
import { debounceTime, takeUntil } from 'rxjs/operators';
import { TranslationService } from '../../../../core/services/translation.service';
import { TranslatePipe } from '../../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-receive-material',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  templateUrl: './receive-material.component.html'
})
export class ReceiveMaterialComponent implements OnInit, OnDestroy {
  private fb = inject(FormBuilder);
  private inventoryService = inject(InventoryService);
  private notification = inject(NotificationService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  
  public ts = inject(TranslationService);
  protected selectedWarehouseId = this.inventoryService.selectedWarehouseId;
  private destroy$ = new Subject<void>();

  mode: 'NORMAL_ENTRY' | 'TRANSFER_RECEIPT' = 'TRANSFER_RECEIPT';
  transferId: string | null = null;
  loading = false;
  
  // Data for the receive flow
  transferData: any = null;
  
  receiveForm: FormGroup = this.fb.group({
    productId: [null], // For manual selection
    sku: [''],        // Display/Input SKU
    documentRef: ['', Validators.required],
    receivedQuantity: [0, [Validators.required, Validators.min(0)]],
    damagedQuantity: [0, [Validators.required, Validators.min(0)]],
    pedimento: [''],   // Anexo 24 compliance
    notes: ['']
  });

  @ViewChild('scannerInput', { static: false }) scannerInput!: ElementRef;
  scannerSubject = new Subject<string>();

  ngOnInit() {
    this.route.queryParams.pipe(takeUntil(this.destroy$)).subscribe(params => {
      if (params['transfer_id']) {
        this.mode = 'TRANSFER_RECEIPT';
        this.transferId = params['transfer_id'];
        this.loadTransferDetail(this.transferId!);
      } else {
        // Por defecto, modo normal si no hay transfer id, 
        // pero podemos requerirlo explícitamente.
        this.mode = 'NORMAL_ENTRY';
      }
    });

    // Scanner debouncer
    this.scannerSubject.pipe(
      debounceTime(500),
      takeUntil(this.destroy$)
    ).subscribe(scanValue => {
      if (scanValue && scanValue.trim().length > 0) {
        this.handleScan(scanValue.trim());
      }
    });
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onScanInput(event: Event) {
    const input = (event.target as HTMLInputElement).value;
    this.scannerSubject.next(input);
  }

  async handleScan(barcode: string) {
    if (this.mode === 'NORMAL_ENTRY') {
      this.receiveForm.patchValue({ sku: barcode });
      await this.lookupManualSku();
      return;
    }

    this.loading = true;
    try {
      await this.loadTransferDetail(barcode);
    } catch (e: any) {
      this.notification.error('Error', 'No se encontró la transferencia: ' + barcode);
    } finally {
      this.loading = false;
      this.receiveForm.patchValue({ documentRef: '' }); 
    }
  }

  async lookupManualSku() {
    const sku = this.receiveForm.get('sku')?.value?.toUpperCase();
    if (!sku || sku.length < 3) return;

    this.loading = true;
    try {
      // We seek in the general catalog
      const product = await this.inventoryService.getProductBySku(sku);
      if (product) {
        this.receiveForm.patchValue({
          productId: product.id,
          sku: product.sku
        });
        this.notification.success('Material Identificado', product.name);
      }
    } catch (e) {
      this.notification.error('Error', 'No se encontró el producto en el catálogo maestro.');
    } finally {
      this.loading = false;
    }
  }

  async loadTransferDetail(id: string) {
    this.loading = true;
    try {
      this.transferData = await this.inventoryService.getTransferDetail(id);
      
      // Play success beep
      const audio = new Audio('assets/sounds/success_beep.mp3');
      audio.play().catch(e => console.warn('Audio playback prevented by auto-play policy', e));

      // Auto-populate receive amounts
      this.receiveForm.patchValue({
        receivedQuantity: this.transferData.quantity,
        damagedQuantity: 0
      });
      this.notification.success('Documento cargado', 'Folio: ' + this.transferData.folio);
    } catch (e: any) {
      // Play error sound
      const audio = new Audio('assets/sounds/error_beep.mp3');
      audio.play().catch(e => console.warn('Audio playback prevented by auto-play policy', e));
      this.notification.error('Error', 'No se pudo cargar la transferencia.');
      this.transferData = null;
    } finally {
      this.loading = false;
    }
  }

  getExpectedQuantity(): number {
    return this.transferData?.quantity || 0;
  }

  getProductName(): string {
    // Requires joining with product catalog, currently not full populated in ICT object natively unless expanded
    return this.transferData?.destination_product_id || this.transferData?.product_id || 'Unknown Product';
  }

  async submitReception() {
    if (this.receiveForm.invalid) return;
    
    const { productId, sku, receivedQuantity, damagedQuantity, notes, pedimento } = this.receiveForm.value;
    const expected = this.getExpectedQuantity();
    const total = receivedQuantity + damagedQuantity;
    
    // Validation for transfers
    if (this.mode === 'TRANSFER_RECEIPT') {
      if (total > expected) {
        this.notification.error('Error', 'La cantidad total no puede exceder la esperada en una transferencia.');
        return;
      }
      if (total < expected && !notes) {
        this.notification.error('Requerido', 'Debe justificar la recepción parcial.');
        return;
      }
    } else {
      // Validation for manual
      if (!productId) {
        this.notification.error('Identidad Requerida', 'Debe buscar un SKU válido primero.');
        return;
      }
      if (total <= 0) {
        this.notification.error('Error', 'Debe ingresar una cantidad mayor a cero.');
        return;
      }
    }

    this.loading = true;
    try {
      if (this.mode === 'TRANSFER_RECEIPT') {
        await this.inventoryService.receiveTransfer(
          this.transferData.id,
          receivedQuantity > 0 ? receivedQuantity : null,
          damagedQuantity,
          notes
        );
      } else {
        // Create a Standard ENTRY document
        const payload: any = {
          type: 'ENTRY',
          warehouse_id: this.selectedWarehouseId() || 'MAIN-001', // Fallback
          items: [
            {
              product_id: productId,
              quantity: receivedQuantity,
              damaged_quantity: damagedQuantity,
              customs_pedimento: pedimento,
              notes: notes
            }
          ]
        };
        await this.inventoryService.createDocument(payload, crypto.randomUUID());
      }

      this.notification.success('Éxito', 'Inventario registrado correctamente.');
      this.router.navigate(['/inventory/dashboard']);
    } catch (e: any) {
      this.notification.error('Error', e?.error?.message || 'Falló la operación.');
    } finally {
      this.loading = false;
    }
  }
}
