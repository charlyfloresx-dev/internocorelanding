import { Routes } from '@angular/router';
import { InventoryDashboardComponent } from './inventory-dashboard.component';
import { InventoryDocumentEditorComponent } from './inventory-document-editor.component';

export const INVENTORY_ROUTES: Routes = [
  {
    path: '',
    component: InventoryDashboardComponent
  },
  {
    path: 'documents/new',
    component: InventoryDocumentEditorComponent
  },
  {
    path: 'documents/:id',
    component: InventoryDocumentEditorComponent
  },
  {
    path: '**',
    redirectTo: ''
  }
];