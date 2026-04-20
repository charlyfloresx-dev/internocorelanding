import { Pipe, PipeTransform, inject } from '@angular/core';
import { TranslationService } from '@services/translation.service';

@Pipe({
    name: 'translate',
    standalone: true,
    pure: false // Necessary because the dictionary is a signal and can change
})
export class TranslatePipe implements PipeTransform {
    private translationService = inject(TranslationService);

    transform(key: string | undefined, fallback = ''): string {
        return this.translationService.translate(key || '', fallback);
    }
}
