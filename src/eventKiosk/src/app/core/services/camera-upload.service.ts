import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpEventType, HttpEvent } from '@angular/common/http';
import imageCompression from 'browser-image-compression';
import { SessionService } from './session.service';
import { finalize } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CameraUploadService {
  private http = inject(HttpClient);
  private session = inject(SessionService);
  
  isUploading = signal<boolean>(false);
  uploadProgress = signal<number>(0);

  async compressAndUpload(files: FileList | File[], eventId: string) {
    this.isUploading.set(true);
    const fileArray = Array.from(files);
    
    for (let i = 0; i < fileArray.length; i++) {
      const file = fileArray[i];
      this.uploadProgress.set(0);

      let fileToUpload: File | Blob = file;

      // Logic: Only compress images, pass videos directly
      if (file.type.startsWith('image/')) {
        const options = {
          maxSizeMB: 1.5,
          maxWidthOrHeight: 2500,
          useWebWorker: true,
          initialQuality: 0.85
        };
        try {
          fileToUpload = await imageCompression(file, options);
        } catch (e) {
          console.warn('Compression failed for', file.name, e);
        }
      } else if (file.type.startsWith('video/')) {
        // Simple safety check for videos (100MB limit for local Wi-Fi)
        if (file.size > 100 * 1024 * 1024) {
          console.error('Video strictly too large:', file.name);
          continue;
        }
      }

      const formData = new FormData();
      formData.append('file', fileToUpload, file.name);
      formData.append('event_id', eventId);
      formData.append('guest_session_id', this.session.guestSessionId());

      await new Promise((resolve) => {
        this.http.post(`https://${window.location.hostname}:8020/api/v1/kiosk/photos/upload`, formData, {
          reportProgress: true,
          observe: 'events'
        }).subscribe({
          next: (event: HttpEvent<any>) => {
            if (event.type === HttpEventType.UploadProgress && event.total) {
              // Showing overall progress if multiple, or simple if single
              const currentProgress = Math.round((100 * (i + event.loaded / event.total)) / fileArray.length);
              this.uploadProgress.set(currentProgress);
            } else if (event.type === HttpEventType.Response) {
              resolve(true);
            }
          },
          error: (err) => {
            console.error('Upload Error:', err);
            resolve(false);
          }
        });
      });
    }

    this.isUploading.set(false);
    this.uploadProgress.set(0);
  }
}
