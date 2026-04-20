import { Pipe, PipeTransform, inject } from '@angular/core';
import { CurrencyService } from '../../core/services/currency.service';

@Pipe({
  name: 'currencyFormat',
  standalone: true,
  pure: false // ¡Crítico!: Para que la UI se actualice automáticamente al cambiar el Signal de moneda.
})
export class CurrencyFormatPipe implements PipeTransform {
  private currencyService = inject(CurrencyService);

  /**
   * Transforma un monto (asumiendo que viene en la moneda base: USD)
   * a la moneda seleccionada y le aplica formato.
   */
  transform(value: number | string | null | undefined): string {
    if (value === null || value === undefined) return '-';
    
    const amount = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(amount)) return '-';

    return this.currencyService.format(amount);
  }
}
