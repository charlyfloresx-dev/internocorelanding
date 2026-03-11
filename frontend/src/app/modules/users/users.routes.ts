import { Routes } from '@angular/router';

export const USER_ROUTES: Routes = [
    {
        path: '',
        loadComponent: () => import('./pages/user-list/user-list.component').then(m => m.UserListComponent)
    },
    {
        path: 'roles',
        loadComponent: () => import('./pages/user-roles/user-roles.component').then(m => m.UserRolesComponent)
    },
    {
        path: 'invitations',
        loadComponent: () => import('./pages/invitation-codes/invitation-codes.component').then(m => m.InvitationCodesComponent)
    }
];
