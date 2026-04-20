import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'money',
  standalone: true
})
export class MoneyPipe implements PipeTransform {
  transform(value: any): string {
    if (!value) return '-';
    
    // Si ya es un numero o string
    if (typeof value === 'number') {
       return `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD`;
    }

    // Si es el objeto de valoracion
    if (typeof value === 'object' && value.amount !== undefined) {
      const amount = Number(value.amount) || 0;
      const cur = value.currency || 'USD';
      
      const formatted = amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      return `$${formatted} ${cur}`;
    }
    
    return '-';
  }
}
