import { Injectable, inject, Type } from '@angular/core';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';

@Injectable({
  providedIn: 'root'
})
export class ModalService {
  private dialog = inject(MatDialog);

  /**
   * Abre un componente como modal, inyectándolo directamente al `<body>`.
   * Esto elimina cualquier conflicto de CSS (z-index, transformaciones del padre).
   */
  open<T, D = any, R = any>(
    component: Type<T>,
    data?: D,
    config?: Partial<MatDialogConfig>,
    onOk?: (result: R) => void,
    onCancel?: () => void
  ): MatDialogRef<T, R> {
    const dialogRef = this.dialog.open(component, {
      data: data,
      panelClass: ['bg-transparent', 'shadow-none', 'p-0', 'border-0'], // Limpiar estilos por defecto de Material
      backdropClass: 'backdrop-blur-sm',
      disableClose: true, // Forzar a usar los botones para cerrar (opcional)
      autoFocus: false,
      maxWidth: '100vw',
      ...config
    });

    dialogRef.afterClosed().subscribe(result => {
      // result es undefined si se cierra con backdrop o Escape (o dialogRef.close())
      // result falso o equivalente significa cancelar
      if (result !== undefined && result !== null && result !== false) {
        if (onOk) onOk(result);
      } else {
        if (onCancel) onCancel();
      }
    });

    return dialogRef;
  }

  /**
   * Cierra todos los modales abiertos actualmente.
   */
  closeAll(): void {
    this.dialog.closeAll();
  }
}
