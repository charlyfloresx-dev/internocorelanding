import { Routes } from '@angular/router';

export const CATALOG_ROUTES: Routes = [
  {
    path: 'products',
    loadComponent: () => import('./pages/product-list/product-list.component').then(m => m.ProductListComponent)
  },
  {
    path: 'uom',
    loadComponent: () => import('./pages/uom-list/uom-list.component').then(m => m.UomListComponent)
  },
  {
    path: 'categories',
    loadComponent: () => import('./pages/category-list/category-list.component').then(m => m.CategoryListComponent)
  },
  {
    path: 'brands',
    loadComponent: () => import('./pages/brand-list/brand-list.component').then(m => m.BrandListComponent)
  },
  {
    path: '',
    redirectTo: 'products',
    pathMatch: 'full'
  }
];