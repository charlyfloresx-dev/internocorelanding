export interface ApiMeta {
  trace_id?: string;
  latency?: string;
  count?: number;
  page?: number;
  total_pages?: number;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta?: ApiMeta;
}

export interface Money {
  amount: number;
  currency: string;
}

// --- Base Entity (Mirror of Python MultiTenantBase) ---
export interface BaseEntity {
  id: string; // UUID
  company_id?: string | null; // Nullable for Global records
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  translation_key?: string;
}

// --- Units of Measure ---
export interface UOMRead extends BaseEntity {
  code: string;
  name: string;
  plural?: string;
}

export interface UOMCreate {
  code: string;
  name: string;
  plural?: string;
  translation_key?: string;
}

export interface UOMUpdate {
  code?: string;
  name?: string;
  plural?: string;
}

// --- Categories ---
export interface CategoryRead extends BaseEntity {
  name: string;
  code: string;
}

export interface CategoryCreate {
  name: string;
  code: string;
  translation_key?: string;
}

export interface CategoryUpdate {
  name?: string;
  code?: string;
}

// --- Brands ---
export interface BrandRead extends BaseEntity {
  name: string;
  code: string;
}

export interface BrandCreate {
  name: string;
  code: string;
  translation_key?: string;
}

export interface BrandUpdate {
  name?: string;
  code?: string;
}

// --- Products ---
export interface ProductRead extends BaseEntity {
  sku: string;
  name: string;
  description?: string;
  uom_id: string;
  category_id: string;
  brand_id: string;
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'DISCONTINUED';
  type: 'GOOD' | 'SERVICE';
  
  // Relaciones expandidas (si el backend las envía, opcionales)
  uom?: UOMRead;
  category?: CategoryRead;
  brand?: BrandRead;
}

export interface ProductVersion {
  version_id: number;
  specifications: Record<string, any>;
  created_at: string;
  is_current: boolean;
}

export interface ProductReadWithVersions extends ProductRead {
  versions: ProductVersion[];
}

export interface ProductCreate {
  sku: string;
  name: string;
  description?: string;
  uom_id: string;
  category_id: string;
  brand_id: string;
  type: 'GOOD' | 'SERVICE';
  specifications?: Record<string, any>; // Versión inicial
}

export interface ProductVersionCreate {
  specifications: Record<string, any>;
  change_reason?: string;
}