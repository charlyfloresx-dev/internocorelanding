export interface BaseEntity {
  id: string; // UUID
}

export interface AuditBase extends BaseEntity {
  created_at: string;
  created_by: string;
  updated_at?: string;
  updated_by?: string;
  version_id: number; // Optimistic Locking
}

export interface DocumentBase extends AuditBase {
  sequence_number: number; // Audit ID
  folio: string; // Commercial ID
  status: 'DRAFT' | 'CONFIRMED' | 'CANCELLED';
  company_id: string;
  warehouse_id: string;
  notes?: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
}

export interface Company {
  id: string;
  name: string;
  logo?: string;
  is_new: boolean;
}

export interface CompanySelection {
  company_id: string;
  company_name: string;
  logo?: string;
  role_names: string[];
  is_new: boolean;
}

export interface AuthContext {
  access_token: string;
  company_id: string;
  user: User;
  roles: string[];
  permissions: string[];
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message?: string;
  meta?: {
    trace_id: string;
    latency: string;
  };
}

export interface LoginResponse {
  selection_token: string;
  user_id: string;
  companies: CompanySelection[];
  is_new_user: boolean;
}

export interface SelectCompanyResponse {
  access_token: string;
  user: User;
  roles: string[];
  permissions: string[];
}
