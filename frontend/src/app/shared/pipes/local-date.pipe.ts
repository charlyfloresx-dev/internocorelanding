import { Pipe, PipeTransform, inject } from '@angular/core';
import { DatePipe } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Pipe({
  name: 'localDate',
  standalone: true
})
export class LocalDatePipe implements PipeTransform {
  private auth = inject(AuthService);
  private datePipe = new DatePipe('en-US');

  transform(value: any, format: string = 'medium', timezone?: string): any {
    if (!value) return value;
    const activeTz = timezone || this.auth.companyTimezone();
    return this.datePipe.transform(value, format, activeTz);
  }
}
