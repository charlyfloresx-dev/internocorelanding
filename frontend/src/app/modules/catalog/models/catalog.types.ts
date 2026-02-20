/**
 * Generic API response envelope.
 * All responses from the backend should follow this structure.
 */
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T | null;
  message: string;
  meta?: {
    trace_id?: string;
    latency?: string;
  };
}

// --- Base Entities ---

export interface BaseEntity {
  id: string; // UUID
  company_id: string | null; // UUID
}

export interface AuditBase extends BaseEntity {
  created_at: string; // ISO Date
  updated_at: string | null; // ISO Date
}

// --- Product ---

export interface ProductRead extends AuditBase {
  name: string;
  description: string | null;
  sku: string;
  is_active: boolean;
  uom_id: string;
  category_id: string;
  brand_id: string;
  status: string;
  type: string;
}

export interface ProductReadWithVersions extends ProductRead {
  versions: Record<string, any>[];
}

export interface ProductCreate {
  name: string;
  description?: string | null;
  sku: string;
  company_id: string; // UUID
  is_active?: boolean;
}

// --- Unit of Measure (UOM) ---

export interface UOMRead extends BaseEntity {
  code: string;
  name: string;
  plural: string | null;
  translation_key: string | null;
}

export interface UOMCreate {
  code: string;
  name: string;
  plural?: string | null;
  translation_key?: string | null;
}

export interface UOMUpdate {
  code?: string | null;
  name?: string | null;
  plural?: string | null;
  translation_key?: string | null;
}

// --- Product Category ---

export interface CategoryRead extends BaseEntity {
  name: string;
  code: string;
  translation_key: string | null;
}

export interface CategoryCreate {
  name: string;
  code: string;
  translation_key?: string | null;
}

export interface CategoryUpdate {
  name: string;
  code: string;
  translation_key?: string | null;
}

// --- Product Brand ---

export interface BrandRead extends BaseEntity {
  name: string;
  code: string;
  translation_key: string | null;
}

export interface BrandCreate {
  name: string;
  code: string;
  translation_key?: string | null;
}

export interface BrandUpdate {
  name: string;
  code: string;
  translation_key?: string | null;
}