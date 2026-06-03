import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

interface BulkImportResult {
  total_rows: number;
  successful: number;
  failed: number;
  results: Array<{
    row_number: number;
    success: boolean;
    ticket_id: string | null;
    reference_code: string | null;
    error: string | null;
  }>;
  created_at: string;
}

@Component({
  selector: 'app-ticket-bulk-import',
  standalone: true,
  imports: [
    CommonModule,
    MatProgressBarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressSpinnerModule,
  ],
  template: `
    <div class="bulk-import-container">
      <h2>Importar Tickets en Masa</h2>

      <!-- Drag-Drop Zone -->
      <div
        class="drag-drop-zone"
        (drop)="onFileDrop($event)"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        [class.drag-active]="isDragActive()"
      >
        <mat-icon class="upload-icon">cloud_upload</mat-icon>
        <p class="drag-text">Arrastra un archivo CSV aquí</p>
        <p class="secondary-text">o haz clic para seleccionar</p>
        <input
          #fileInput
          type="file"
          accept=".csv"
          (change)="onFileSelected($event)"
          style="display: none"
        />
        <button mat-raised-button color="primary" (click)="fileInput.click()">
          Seleccionar Archivo
        </button>
      </div>

      <!-- Template Download -->
      <div class="template-section">
        <p>¿Necesitas ayuda con el formato?</p>
        <button mat-button color="accent" (click)="downloadTemplate()">
          <mat-icon>download</mat-icon>
          Descargar Plantilla CSV
        </button>
      </div>

      <!-- Loading Progress -->
      <div *ngIf="isLoading()" class="progress-section">
        <mat-progress-spinner diameter="50" mode="indeterminate"></mat-progress-spinner>
        <p>Importando tickets...</p>
      </div>

      <!-- Results Summary -->
      <div *ngIf="importResult()" class="results-section">
        <mat-card>
          <mat-card-header>
            <mat-card-title>Resultados de Importación</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <div class="stats-grid">
              <div class="stat">
                <span class="stat-label">Total de filas</span>
                <span class="stat-value">{{ importResult()!.total_rows }}</span>
              </div>
              <div class="stat success">
                <span class="stat-label">Exitosos</span>
                <span class="stat-value">{{ importResult()!.successful }}</span>
              </div>
              <div class="stat error" *ngIf="importResult()!.failed > 0">
                <span class="stat-label">Errores</span>
                <span class="stat-value">{{ importResult()!.failed }}</span>
              </div>
            </div>

            <!-- Progress Bar -->
            <div class="progress-visual">
              <mat-progress-bar
                mode="determinate"
                [value]="
                  (importResult()!.successful / importResult()!.total_rows) * 100
                "
              ></mat-progress-bar>
            </div>

            <!-- Error Details -->
            <div
              *ngIf="importResult()!.failed > 0"
              class="error-details"
            >
              <h4>Errores detectados:</h4>
              <div class="error-list">
                <div
                  *ngFor="let result of importResult()!.results"
                  [class.error-row]="!result.success"
                >
                  <span *ngIf="!result.success" class="error-icon">✗</span>
                  <span *ngIf="!result.success" class="error-text">
                    Fila {{ result.row_number }}: {{ result.error }}
                  </span>
                  <span *ngIf="result.success" class="success-icon">✓</span>
                  <span *ngIf="result.success" class="success-text">
                    Fila {{ result.row_number }}: {{ result.reference_code }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Success Message -->
            <div
              *ngIf="importResult()!.failed === 0"
              class="success-message"
            >
              ¡Todos los tickets se importaron correctamente!
            </div>
          </mat-card-content>
          <mat-card-actions>
            <button mat-button (click)="resetForm()">Importar más</button>
          </mat-card-actions>
        </mat-card>
      </div>

      <!-- Error Message -->
      <div *ngIf="errorMessage()" class="error-message">
        <mat-icon>error</mat-icon>
        {{ errorMessage() }}
      </div>
    </div>
  `,
  styles: [`
    .bulk-import-container {
      padding: 2rem;
      max-width: 800px;
      margin: 0 auto;
    }

    h2 {
      margin-bottom: 2rem;
      font-size: 1.5rem;
      font-weight: 500;
    }

    .drag-drop-zone {
      border: 2px dashed #ccc;
      border-radius: 8px;
      padding: 3rem 2rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;
      background-color: #fafafa;

      &.drag-active {
        border-color: #1976d2;
        background-color: #e3f2fd;
      }

      .upload-icon {
        font-size: 3rem;
        width: 3rem;
        height: 3rem;
        color: #1976d2;
        margin-bottom: 1rem;
      }

      .drag-text {
        margin: 0 0 0.5rem 0;
        font-size: 1.1rem;
        font-weight: 500;
        color: #333;
      }

      .secondary-text {
        margin: 0 0 1.5rem 0;
        font-size: 0.9rem;
        color: #666;
      }
    }

    .template-section {
      margin: 2rem 0;
      text-align: center;
      padding: 1rem;
      background-color: #f5f5f5;
      border-radius: 4px;

      p {
        margin: 0 0 1rem 0;
        color: #666;
      }
    }

    .progress-section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 1rem;
      padding: 2rem;
      text-align: center;

      p {
        margin: 0;
        color: #666;
      }
    }

    .results-section {
      margin-top: 2rem;

      mat-card {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      mat-card-header {
        margin-bottom: 1rem;
      }

      mat-card-title {
        font-size: 1.3rem;
        margin: 0;
      }
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;

      .stat {
        padding: 1rem;
        border-radius: 4px;
        background-color: #f5f5f5;
        text-align: center;

        &.success {
          background-color: #e8f5e9;
          color: #2e7d32;
        }

        &.error {
          background-color: #ffebee;
          color: #c62828;
        }

        .stat-label {
          display: block;
          font-size: 0.85rem;
          margin-bottom: 0.5rem;
          opacity: 0.8;
        }

        .stat-value {
          display: block;
          font-size: 1.8rem;
          font-weight: bold;
        }
      }
    }

    .progress-visual {
      margin: 1.5rem 0;
    }

    .error-details {
      margin-top: 2rem;
      padding: 1rem;
      background-color: #fff3e0;
      border-radius: 4px;

      h4 {
        margin: 0 0 1rem 0;
        color: #e65100;
      }

      .error-list {
        max-height: 300px;
        overflow-y: auto;
      }

      .error-row {
        padding: 0.5rem;
        margin-bottom: 0.25rem;
        border-radius: 2px;
        background-color: white;
        border-left: 4px solid #d32f2f;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .success-icon {
        color: #2e7d32;
        font-weight: bold;
        min-width: 20px;
      }

      .error-icon {
        color: #d32f2f;
        font-weight: bold;
        min-width: 20px;
      }

      .error-text {
        color: #d32f2f;
        font-size: 0.9rem;
      }

      .success-text {
        color: #2e7d32;
        font-size: 0.9rem;
      }
    }

    .success-message {
      padding: 1rem;
      background-color: #e8f5e9;
      border-left: 4px solid #2e7d32;
      border-radius: 4px;
      color: #2e7d32;
      margin-top: 1rem;
      text-align: center;
      font-weight: 500;
    }

    .error-message {
      padding: 1rem;
      background-color: #ffebee;
      border-left: 4px solid #d32f2f;
      border-radius: 4px;
      color: #d32f2f;
      margin-top: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;

      mat-icon {
        flex-shrink: 0;
      }
    }

    mat-card-actions {
      text-align: right;
      padding: 1rem;
    }
  `],
})
export class TicketBulkImportComponent implements OnInit {
  isDragActive = signal(false);
  isLoading = signal(false);
  importResult = signal<BulkImportResult | null>(null);
  errorMessage = signal<string | null>(null);

  constructor(private http: HttpClient) {}

  ngOnInit(): void {}

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragActive.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragActive.set(false);
  }

  onFileDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragActive.set(false);

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.processFile(files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.processFile(input.files[0]);
    }
  }

  private processFile(file: File): void {
    if (!file.name.endsWith('.csv')) {
      this.errorMessage.set('Por favor selecciona un archivo CSV');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      this.errorMessage.set('El archivo es demasiado grande (máximo 5MB)');
      return;
    }

    this.errorMessage.set(null);
    this.uploadFile(file);
  }

  private uploadFile(file: File): void {
    const formData = new FormData();
    formData.append('file', file);

    this.isLoading.set(true);
    this.http
      .post<any>('/api/v1/tickets/bulk-import', formData)
      .subscribe({
        next: (response) => {
          this.importResult.set(response.data);
          this.isLoading.set(false);
        },
        error: (error) => {
          this.errorMessage.set(
            error.error?.detail || 'Error al importar tickets'
          );
          this.isLoading.set(false);
        },
      });
  }

  downloadTemplate(): void {
    const csvContent = `title,description,ticket_type,priority,area,module_origin
"Revisar sensor de temperatura","El sensor de temperatura en la línea 3 reporta valores inconsistentes",MAINTENANCE,MEDIA,Producción,MES
"Falta stock de tuercas M8","Se agotó el stock de tuercas M8 para ensamble",INVENTORY,ALTA,Almacén,INVENTORY
"Capacitación nuevo operador","Nuevo operador requiere inducción de seguridad",SUPPORT,BAJA,RH,MANUAL`;

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', 'plantilla-tickets.csv');
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  resetForm(): void {
    this.importResult.set(null);
    this.errorMessage.set(null);
    this.isLoading.set(false);
  }
}
