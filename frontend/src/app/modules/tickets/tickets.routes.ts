import { Routes } from '@angular/router';
import { TicketListComponent } from './ticket-list.component';
import { TicketEditorComponent } from './ticket-editor.component';

export const TICKETS_ROUTES: Routes = [
    {
        path: '',
        component: TicketListComponent
    },
    {
        path: 'new',
        component: TicketEditorComponent
    },
    {
        path: 'detail/:id',
        component: TicketEditorComponent
    }
];
