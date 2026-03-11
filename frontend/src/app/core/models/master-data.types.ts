/**
 * Represents the standard API response wrapper from the backend.
 * @template T The type of the data payload.
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

export interface BaseCatalog {
  id: string; // UUID
  name: string;
  code: string;
  translation_key: string | null;
  company_id: string | null; // UUID
}

// --- Product Models ---

/**
 * Base product model, used for lists.
 * Corresponds to the `ProductRead` schema in OpenAPI.
 */
export interface ProductRead {
  id: string; // UUID
  name: string;
  description?: string | null;
  sku: string;
  is_active?: boolean;
  is_global_in_group: boolean;
  company_id: string; // UUID
  created_at?: string; // ISO Date string
  updated_at?: string | null; // ISO Date string
}

/**
 * Detailed product model, includes versions.
 * Corresponds to the `ProductReadWithVersions` schema in OpenAPI.
 */
export interface ProductReadWithVersions extends ProductRead {
  versions: any[]; // TODO: Define a proper version type if needed
}

// --- Other Catalog Models ---

/**
 * Represents a Unit of Measure (UOM).
 * Corresponds to the `UOMRead` schema in OpenAPI.
 */
export interface UOMRead extends BaseCatalog {
  plural: string | null;
}

/**
 * Represents a Product Category.
 * Corresponds to the `CategoryRead` schema in OpenAPI.
 */
export interface CategoryRead extends BaseCatalog { }

/**
 * Represents a Product Brand.
 * Corresponds to the `BrandRead` schema in OpenAPI.
 */
export interface BrandRead extends BaseCatalog { }
