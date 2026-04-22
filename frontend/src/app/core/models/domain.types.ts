// temp_future/src/app/core/models/domain.types.ts

/**
 * Kernel Interfaces (Mirror of backend/common)
 */

export interface BaseEntity {
  id: string; // UUID v4
}

export interface MultiTenantBase extends BaseEntity {
  readonly company_id: string; // Controlled by backend/interceptor
}

/**
 * Audit tracking fields managed by backend
 * Included in TS for display purposes
 */
export interface AuditBase extends MultiTenantBase {
  readonly created_at: string;
  readonly created_by: string;
  readonly updated_at?: string;
  readonly updated_by?: string;
  readonly is_active: boolean;
  readonly version_id: number;
}

/**
 * Enums as const for performance and strictness
 */

export const enum UserStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
  PENDING = 'PENDING'
}

export const enum CompanyStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  SUSPENDED = 'SUSPENDED',
  DELINQUENT = 'DELINQUENT'
}

export const enum Currency {
  USD = 'USD',
  MXN = 'MXN',
  EUR = 'EUR'
}

export const enum ValidationStatus {
  CLEAN = 'CLEAN',
  OVERFLOW_CONFIRMED = 'OVERFLOW_CONFIRMED',
  UNDER_REVIEW = 'UNDER_REVIEW'
}

/**
 * Value Objects
 */

export interface Money {
  amount: number;
  currency: Currency;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
}

/**
 * Authentication & Access DTOs
 */

export interface CompanyAccessDto {
  company_id: string;
  company_name: string;
  logo?: string;
  role_names: string[];
  is_new: boolean;
  group_id?: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface AuthHandshake {
  selection_token: string;
  user_id: string;
  companies: CompanyAccessDto[];
  is_new: boolean;
}

export interface AuthSession {
  access_token: string;
  refresh_token: string;
  company_id: string;
  user_id: string;
  user: AuthUser;
  roles: string[];
  permissions: string[];
}


/**
 * Dashboard & Analytics DTOs
 */
export interface ValuationSummary {
  current_total_stock: number;
  total_usd: Money;
  variation_percentage: number;
  stock_yesterday: number;
}

export interface StockAlert {
  product_id: string;
  sku: string;
  name?: string;
  current_quantity: number;
  min_quantity: number;
  warehouse_id: string;
  warehouse_name?: string;
}

export interface HourlyMovement {
  hour: string;
  entries: number;
  exits: number;
  entries_money?: Money;
  exits_money?: Money;
}

export interface RecentActivityRow {
  date: string;
  document_folio: string;
  movement_type: string;
  quantity_delta: number;
  uom_symbol: string;
  status?: string;
  warehouse_name?: string;
  id?: string;
  movement_id?: string;
  validation_status?: ValidationStatus;
  /** Concept traceability — preferred for UI display */
  concept_id?: string;
  concept_name?: string; // e.g. "Recepción de Compra", "Traspaso Inter-Empresa"
}

export interface DashboardDTO {
  valuation: ValuationSummary;
  critical_alerts: StockAlert[];
  movement_series: HourlyMovement[];
  recent_activity: RecentActivityRow[];
  meta: any;
}

/**
 * Business Entities (Inheriting from AuditBase)
 */

export interface InventoryItem extends AuditBase {
  sku: string;
  description: string;
  uom: string; 
  stock_level: number;
  reorder_point: number;
  location_code: string; 
}

export interface UOMRead extends AuditBase {
  code: string;
  name: string;
  plural?: string;
}

export interface CategoryRead extends AuditBase {
  name: string;
  code: string;
}

export interface BrandRead extends AuditBase {
  name: string;
  code: string;
}

export interface ProductRead extends AuditBase {
  sku: string;
  name: string;
  description?: string;
  
  // Phase 33.5: Fiscal & Commercial Fields
  sat_product_code?: string;
  hts_code?: string;
  is_taxable: boolean;
  allow_price_override: boolean;
  
  uom_id: string;
  category_id: string;
  brand_id: string;
  status: 'DRAFT' | 'ACTIVE' | 'INACTIVE' | 'DISCONTINUED';
  type: 'GOOD' | 'SERVICE';
  
  // Expanded relations
  uom?: UOMRead;
  category?: CategoryRead;
  brand?: BrandRead;
}

export interface ProductPrice {
  id: string;
  product_id: string;
  price_list_index: number;
  amount: number;
  currency: Currency;
  unit_type: 'BASE' | 'SALE';
  warehouse_id?: string | null;
  effective_date: string;
  is_active: boolean;
}

/**
 * Inventory Documents & Movements
 */

export const enum ConceptType {
  ENTRY = 'ENTRADA',
  OUTPUT = 'SALIDA',
  TRANSFER = 'TRASPASO',
  ADJUSTMENT = 'ADJUSTMENT' // Backend usually uses ENTRADA/SALIDA for adjustments with a specific concept
}

export interface InventoryMovement extends BaseEntity {
  product_id: string;
  sku: string;
  quantity: number;
  unit_price: number;
  weight?: number;
  location_code?: string;
  is_weight_mismatch?: boolean;
  validation_status?: ValidationStatus;
}

export interface InventoryDocument extends AuditBase {
  folio: string;
  delivery_date: string;
  concept_type: ConceptType;
  warehouse_id: string;
  destination_warehouse_id?: string;
  partnership_id?: string;
  reference?: string;
  description?: string;
  total_amount: number;
  movements: InventoryMovement[];
  /** Concept traceability */
  concept_id?: string;
  concept_name?: string;  // Display label: "Traspaso Inter-Empresa"
  concept_code?: string;  // Deterministic code: "INT-TRA"
}
/**
 * Standard API Wrapper (Middleware Mirror)
 */
export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  total_count?: number; // Optional for paginated lists
  message: string;
  meta: {
    trace_id?: string;
    latency?: string;
    pagination?: {
      limit: number;
      offset: number;
      count: number;
    };
  };
}

/**
 * Production & Shopfloor DTOs
 */

export interface ProductionStatDto {
  hour: string;
  actual: number;
  goal: number;
  status: 'excellent' | 'good' | 'warning' | 'critical';
}

export interface WorkOrderDto extends AuditBase {
  order_number: string;
  line_id: string;
  product_id: string;
  product_name: string;
  sku: string;
  quantity_target: number;
  quantity_produced: number;
  progress: number;
  status: 'RUNNING' | 'DELAYED' | 'RISK' | 'COMPLETED' | 'PENDING';
  scheduled_date: string;
  cost: Money;
  due_date: string;
}

export interface DowntimeLogDto extends AuditBase {
  line_id: string;
  issue_name: string;
  duration_minutes: number;
  start_time: string;
  status: 'ACTIVE' | 'RESOLVED';
}

export interface ProductionDashboardDto {
  oee: number;
  downtime_minutes: number;
  active_orders_count: number;
  average_efficiency: number;
  hourly_stats: ProductionStatDto[];
  active_orders: WorkOrderDto[];
  recent_downtime: DowntimeLogDto[];
}

/**
 * Support & Ticket System
 */

export const enum TicketStatus {
  NEW = 'NEW',
  IN_REVIEW = 'IN_REVIEW',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  ON_HOLD = 'ON_HOLD',
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED',
  CANCELED = 'CANCELED'
}

export const enum TicketPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export const enum TicketType {
  SUPPORT = 'SUPPORT',
  INCIDENT = 'INCIDENT',
  IMPROVEMENT = 'IMPROVEMENT',
  COMPLAINT = 'COMPLAINT',
  TASK = 'TASK'
}

export interface TicketComment {
  id: string;
  ticket_id: string;
  content: string;
  author_id: string;
  created_at: string;
}

export interface Ticket extends AuditBase {
  reference_code: string;
  title: string;
  description: string;
  ticket_type: TicketType;
  priority: TicketPriority;
  status: TicketStatus;
  assigned_to_id?: string;
}

/**
 * Master Data Extended
 */

export const enum PartnershipType {
  CUSTOMER = 1,
  SUPPLIER = 2
}

export const enum PartnershipStatus {
  PLATINUM = 'PLATINUM',
  GOLD = 'GOLD',
  SILVER = 'SILVER',
  ACTIVE = 'ACTIVE'
}

export interface Partnership extends AuditBase {
  code: string;
  name: string;
  type: PartnershipType;
  status: PartnershipStatus;
}

export interface Concept extends AuditBase {
  name: string;
  /**
   * Deterministic code for frontend resolution.
   * Standard system codes: PUR-REC, PUR-RET, INT-TRA, ADJ-POS, ADJ-NEG, SCRAP.
   * Use `resolveConceptByCode(code)` in MasterDataService for signal-safe lookup.
   */
  code: string;
  type: ConceptType;
  affect_stock: boolean;
  is_system: boolean;
  requires_external_entity?: boolean;
  requires_target_warehouse?: boolean;
}

/**
 * Concept loading state for defensive UI guards.
 * LOADING  — catalog fetch in progress (block submit)
 * READY    — concepts available, concept_id can be resolved
 * ERROR    — fetch failed, show retry/fallback UI
 */
export type ConceptCatalogState = 'LOADING' | 'READY' | 'ERROR';
