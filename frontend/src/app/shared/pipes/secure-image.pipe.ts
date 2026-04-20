import { Pipe, PipeTransform } from '@angular/core';
import { environment } from '../../../environments/environment';

/**
 * secureImage Pipe
 * Transforma rutas relativas en URLs completas apuntando al assetsUrl configurado.
 * Ideal para usar en templates: <img [src]="collaborator.photo_path | secureImage">
 */
@Pipe({
  name: 'secureImage',
  standalone: true
})
export class SecureImagePipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    // Si no hay valor, devolvemos un placeholder predeterminado
    if (!value) {
      return 'assets/images/default-profile.png';
    }
    
    // Si ya es una URL absoluta, la dejamos pasar
    if (value.startsWith('http://') || value.startsWith('https://')) {
      return value;
    }
    
    // Normalizar ruta relativa (quitar / inicial si existe)
    const cleanPath = value.replace(/^\/+/, '');
    
    // Retornar URL completa usando el dominio de assets (momentos.com en desarrollo)
    return `${environment.assetsUrl}/${cleanPath}`;
  }
}
