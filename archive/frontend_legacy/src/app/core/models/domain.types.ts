// src/app/core/models/domain.types.ts

// --- 1. Kernel (Espejo de Interno.Common) ---

export interface BaseEntity {
  id: string; // UUID v4
}

export interface MultiTenantBase extends BaseEntity {
  company_id: string; // Obligatorio para SaaS
}

export interface AuditBase extends MultiTenantBase {
  created_at: string; // ISO Date
  created_by: string; // User ID
  updated_at?: string;
  updated_by?: string;
  is_deleted: boolean; // Soft Delete
}

// --- 2. Enums Globales (Value Objects) ---

export type UserStatus = 'ACTIVE' | 'INACTIVE' | 'SUSPENDED' | 'INVITED';
export type CompanyStatus = 'TRIAL' | 'ACTIVE' | 'DELINQUENT' | 'CHURNED';
export type WorkOrderStatus = 'DRAFT' | 'RELEASED' | 'IN_PROGRESS' | 'COMPLETED' | 'HOLD';

export interface Money {
  amount: number;
  currency: 'USD' | 'MXN' | 'EUR';
}

export interface Address {
  street: string;
  city: string;
  zip_code: string;
  country: string;
}

// --- 3. DTOs de Autenticación y Acceso ---

export interface CompanyAccessDto {
  company_id: string;
  company_name: string;
  roles: string[]; // ['ADMIN', 'OPERATOR']
  status: CompanyStatus;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_profile: {
    id: string;
    email: string;
    full_name: string;
    companies: CompanyAccessDto[]; // Lista de acceso multi-tenant
  };
}

// --- 4. Entidades de Negocio (Espejo de Interno.Domain) ---

export interface WorkOrder extends AuditBase {
  order_number: string;
  product_sku: string;
  quantity_planned: number;
  quantity_produced: number;
  status: WorkOrderStatus;
  due_date: string;
  cost_estimate: Money; // Usando el Value Object
  assigned_operators: string[];
}

export interface InventoryItem extends AuditBase {
  sku: string;
  description: string;
  uom: string; // Unit of Measure (kg, ea, m)
  stock_level: number;
  reorder_point: number;
  location_code: string; // e.g., "WH1-R2-S4"
}
