import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export enum PhotoStatus {
  UPLOADED = "UPLOADED",
  APPROVED = "APPROVED",
  REJECTED = "REJECTED",
  PURCHASED = "PURCHASED",
  PRINTING = "PRINTING",
  DONE = "DONE"
}

export interface EventPhoto {
  id: string;
  status: PhotoStatus;
  guest_name?: string;
  object_key: string;
  url?: string;            // presigned download URL (browser-accessible)
  approval_count: number;
  required_approvals?: number;
  mime_type?: string;
}

// Persisted event config stored in localStorage after Setup
export interface EventConfig {
  event_id: string;
  event_name: string;
  company_id: string;
}

const DEFAULT_EVENT_ID = '10000000-0000-0000-0000-000000000001';
const DEFAULT_COMPANY_ID = '00000000-0000-0000-0000-000000000002';

@Injectable({
  providedIn: 'root'
})
export class KioskService {
  private http = inject(HttpClient);
  private apiUrl = `https://${window.location.hostname}:8020/api/v1/kiosk`;

  // State
  pendingPhotos = signal<EventPhoto[]>([]);
  gallery = signal<EventPhoto[]>([]);

  /** Returns the active event config from localStorage or defaults */
  getEventConfig(): EventConfig {
    const stored = localStorage.getItem('kiosk_event');
    if (stored) return JSON.parse(stored);
    return { event_id: DEFAULT_EVENT_ID, event_name: 'Demo', company_id: DEFAULT_COMPANY_ID };
  }

  fetchPending(eventId: string) {
    this.http.get<EventPhoto[]>(`${this.apiUrl}/photos/pending-approval/${eventId}`)
      .subscribe(photos => this.pendingPhotos.set(photos));
  }

  fetchGallery(eventId: string) {
    this.http.get<EventPhoto[]>(`${this.apiUrl}/photos/gallery/${eventId}`)
      .subscribe(photos => this.gallery.set(photos));
  }

  getDeviceId(): string {
    let id = localStorage.getItem('kiosk_device_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('kiosk_device_id', id);
    }
    return id;
  }

  reviewPhoto(photoId: string, approverIndex: number, action: 'APPROVE' | 'REJECT'): Observable<any> {
    return this.http.post(`${this.apiUrl}/photos/${photoId}/review`, {
      approver_index: approverIndex,
      device_id: this.getDeviceId(),
      action
    });
  }

  resetApprovals(photoId: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/photos/${photoId}/reset-approvals`, {});
  }
}
