import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'money',
  standalone: true
})
export class MoneyPipe implements PipeTransform {
  transform(value: any, showCurrency: boolean = true): string {
    if (!value || typeof value !== 'object') return '-';
    
    const amount = value.amount !== undefined ? value.amount : 0;
    const currency = value.currency || 'USD';
    
    const formatted = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount);
    
    return showCurrency ? `${formatted} ${currency}` : formatted;
  }
}
