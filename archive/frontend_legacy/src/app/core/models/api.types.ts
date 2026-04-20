// src/app/core/models/api.types.ts

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data: T;
  message: string;
  meta: any;
}

export interface Money {
  amount: number;
  currency: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar: string;
  status: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
}

export interface Permission {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface Company {
  id: string;
  name: string;
  registrationNumber: string;
  contactEmail: string;
  status: string;
  logo?: string;
  plan?: string;

  // Backend Mapping (v2.1)
  is_new?: boolean;
  group_id?: string;
  group_name?: string;
}

export interface UserCompanyAccess {
  company: Company;
  role: Role;
}

export interface HandshakeData {
  user: User;
  accesses: UserCompanyAccess[];
}

export interface LoginResponse {
  selection_token: string; // Pre-authorization token for company selection
  companies: CompanySelection[]; // List of companies the user has access to
}

export interface SelectCompanyResponse {
  access_token: string;
  token_type: string;
  company_id: string; // Crucial para multitenancy
}

export interface CompanySelection {
  company_id: string;
  company_name: string;
  logo?: string;
  role_names: string[];
  is_new: boolean;
  group_id: string;
  group_name: string;
}

// Admin v2 Interfaces (Auth-Service v2.1.0)
export interface RoleResponse {
  id: string;
  name: string;
}

export interface InvitationCreate {
  email: string;
  role_id: string;
}

export interface InvitationResponse {
  id: string;
  code: string;
  email: string;
  role_id: string;
  company_id: string;
  expires_at: string;
  is_used: boolean;
}

export interface UserRoleAssignment {
  email: string;
  role_id: string;
}

export interface GodModeIntervention {
  action: string;
  target_id: string;
  company_id: string;
  timestamp: string;
  transaction_id: string;
}

export interface UpdateSubscriptionCommand {
  days: number;
  reason: string;
}

export interface SessionContext {
  access_token: string; // Renamed from sessionToken for clarity
  companyId: string;
  company_name?: string;
  role: Role;
  permissions: string[];
  group_id: string;
  group_name: string;
}

export interface RegisterCompanyPayload {
  company_name: string;
  tax_id: string;
  admin_email: string;
  password: string;
}

export interface RegisterResponse {
  access_token: string;
  token_type: string;
  company_id: string;
  user_id: string;
  company: Company;
  role: Role;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  email: string;
  password: string;
}

export interface CompleteRegistrationPayload {
  code: string;
  full_name: string;
  password: string;
}

export interface ProductCreatePayload {
  name: string;
  sku: string;
  description?: string | null;
  product_type: 'FINISHED_GOOD' | 'RAW_MATERIAL' | 'SEMI_FINISHED';
  uom_id: string;
  category_id?: string | null;
}

export interface AuditBase {
  created_at: string;
  created_by: string;
  updated_at?: string | null;
  updated_by?: string | null;
  version_id: number;
}

export interface UOMRead extends AuditBase {
  id: string;
  company_id?: string | null;
  code: string;
  name: string;
  plural?: string | null;
  translation_key?: string | null;
}

export interface ProductRead extends AuditBase {
  id: string;
  company_id: string;
  name: string;
  description?: string | null;
  sku: string;
  product_type: string;
  status: string;
  is_active?: boolean;
  is_global_in_group: boolean;
}

export interface InventoryTransactionRead extends AuditBase {
  id: string;
  inventory_id: string;
  transaction_type: 'IN' | 'OUT' | 'TRANSFER' | 'ADJUSTMENT';
  quantity_change: number;
  previous_balance: number;
  new_balance: number;
  reference_document_id?: string;
  reference_document_type?: string;
  notes?: string;
}

export interface BrandRead extends AuditBase {
  id: string;
  company_id?: string | null;
  name: string;
  code: string;
  translation_key?: string | null;
}

export interface CategoryRead extends AuditBase {
  id: string;
  company_id?: string | null;
  name: string;
  code: string;
  translation_key?: string | null;
}

export interface Employee {
  id: number;
  name: string;
  position: string;
  department: string;
  avatar: string;
}

export interface InventoryItemDto {
  id: string;
  companyId: string;
  productId: string;
  name: string;
  description: string;
  sku: string;
  price: Money;
  stockQuantity: number;
  reservedQuantity: number;
  warehouseId: string;
  warehouseName: string;
  location: string;
  categoryId: string;
  categoryName: string;
  isActive: boolean;
}

export interface CreateInventoryItemCommand {
  name: string;
  sku: string;
  description: string;
  price: Money;
  initialStockQuantity: number;
  categoryId: string;
  warehouseId: string;
}

export interface AdjustStockCommand {
  itemId: string;
  quantityChange: number;
  reason: string;
}

export interface RegisterUserCommand {
  email: string;
  password?: string;
  firstName: string;
  lastName: string;
  companyName: string;
  companyRegistrationNumber: string;
  companyContactEmail: string;
  companyAddress: {
    street: string;
    city: string;
    state: string;
    country: string;
    zipCode: string;
  };
}

export enum TicketStatus {
  New = 'New',
  InReview = 'InReview',
  Assigned = 'Assigned',
  InProgress = 'InProgress',
  OnHold = 'OnHold',
  Resolved = 'Resolved',
  Closed = 'Closed',
  Canceled = 'Canceled'
}

export enum TicketPriority {
  Low = 'Low',
  Medium = 'Medium',
  High = 'High',
  Critical = 'Critical'
}

export enum TicketType {
  Support = 'Support',
  Incident = 'Incident',
  Improvement = 'Improvement',
  Complaint = 'Complaint',
  Task = 'Task'
}

export interface TicketComment {
  id: string;
  ticket_id: string;
  content: string;
  author_id: string;
  created_at: string;
}

export interface TicketHistory {
  id: string;
  ticket_id: string;
  change_type: string;
  old_value?: string;
  new_value?: string;
  changed_by_id: string;
  created_at: string;
}

export interface Ticket {
  id: string;
  reference_code: string;
  title: string;
  description: string;
  ticket_type: TicketType;
  priority: TicketPriority;
  status: TicketStatus;
  assigned_to_id?: string;
  company_id: string;
  created_by: string;
  created_at: string;
  comments?: TicketComment[];
  history?: TicketHistory[];
}

export interface CreateTicketCommand {
  company_id: string;
  title: string;
  description: string;
  ticket_type: TicketType;
  priority: TicketPriority;
}

export interface UpdateTicketCommand {
  title?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  assigned_to_id?: string;
}

export interface ProductionStatDto {
  hour: string;
  actual: number;
  goal: number;
  status: 'excellent' | 'good' | 'warning' | 'critical';
}

export interface WorkOrderDto {
  id: string;
  orderNumber: string;
  lineId: string;
  productId: string;
  productName: string;
  sku: string;
  quantityTarget: number;
  quantityProduced: number;
  progress: number;
  status: 'Running' | 'Delayed' | 'Risk' | 'Completed' | 'Pending';
  scheduledDate: string;
  cost: Money;
  dueDate: string | Date;
}

export interface DowntimeLogDto {
  id: string;
  lineId: string;
  issueName: string;
  durationMinutes: number;
  startTime: string;
  status: string;
}

export interface ProductionDashboardDto {
  oee: number;
  downtimeMinutes: number;
  activeOrdersCount: number;
  averageEfficiency: number;
  hourlyStats: ProductionStatDto[];
  activeOrders: WorkOrderDto[];
  recentDowntime: DowntimeLogDto[];
  weeklyTrend: TrendPointDto[];
  downtimePareto: ParetoItemDto[];
}

export interface CreateWorkOrderCommand {
  productId: string;
  quantity: number;
  scheduledDate: string;
  notes?: string;
  estimatedCost: Money;
}

export interface Issue {
  id: string;
  name: string;
  category: string;
}

export enum DowntimeStatus {
  Active = 'Active',
  Resolved = 'Resolved'
}

export interface CreateDowntimeCommand {
  lineId: string;
  workOrderId?: string;
  issueId: string;
  description: string;
  requestNumber?: number;
}

export interface TrendPointDto {
  label: string;
  value: number;
  goal: number;
}

export interface ParetoItemDto {
  label: string;
  value: number;
  cumulative: number;
}

export interface Warehouse {
  id: string;
  code: string;
  name: string;
  description: string;
  typeId?: string;
  typeName?: string;
  groupId?: string;
  groupName?: string;
  location?: string;
  capacity?: number;
  unitCode?: string;
  isActive: boolean;
  type?: string; 
  sequence_number?: number; // Added for audit
}

export enum PartnershipType {
  Customer = 1,
  Supplier = 2
}

export enum PartnershipStatus {
  Platinum = 'Platinum',
  Gold = 'Gold',
  Silver = 'Silver',
  Active = 'Active'
}

export interface Partnership {
  id: string;
  code: string;
  name: string;
  type: PartnershipType;
  status: PartnershipStatus;
}

export interface ProductCategory {
  id: string;
  name: string;
}

export enum ConceptType {
  Entry = 'Entry',
  Output = 'Output',
  Adjustment = 'Adjustment',
  Transfer = 'Transfer'
}

export interface Concept {
  id: string;
  name: string;
  type: ConceptType;
  affectStock: boolean;
  isSystem: boolean;
  requires_external_entity?: boolean;
  requires_target_warehouse?: boolean;
}

export interface WarehouseType {
  id: number;
  name: string;
}

export interface WarehouseGroup {
  id: number;
  name: string;
}

export enum DocumentStatus {
  Confirmed = 'Confirmed',
  Draft = 'Draft',
  Canceled = 'Canceled'
}

export interface InventoryDocument {
  id: string;
  folio: string;
  sequence_number: number; // For audit traceability
  deliveryDate: string;
  conceptId: string;
  conceptName: string;
  conceptType: ConceptType;
  warehouseId: string;
  warehouseName: string;
  partnershipId?: string;
  partnershipName?: string;
  reference: string;
  description: string;
  total_amount: number; // Renamed for parity
  status: DocumentStatus;
  movements: any[];
  destination_warehouse_id?: string;
  destination_warehouse_name?: string;
}

export interface InventorySummary {
  entries_24h: number;
  outputs_24h: number;
  transfers_24h: number;
  pending_docs: number;
}

export interface MovementDocumentRow {
  id: string;
  folio: string;
  date: string;
  type: string;
  origin: string;
  destination: string;
  items_count: number;
  status: string;
}

// --- Mission Control Dashboard (Consolidated Telemetry) ---

export interface StockAlert {
  product_id: string;
  sku: string;
  current_quantity: number;
  min_quantity: number;
  warehouse_id: string;
  status: 'LOW' | 'CRITICAL';
}

export interface HourlyMovement {
  hour: string;
  entries: number;
  exits: number;
}

export interface ValuationSummary {
  total_usd: number;
  variation_percentage: number;
  stock_yesterday: number;
}

export interface DashboardDTO {
  valuation: ValuationSummary;
  critical_alerts: StockAlert[];
  hourly_series: HourlyMovement[];
  recent_movements: any[]; // Matches KardexRowEntity
}

export interface CreateDocumentCommand {
  conceptId: string;
  warehouseId: string;
  destination_warehouse_id?: string;
  partnershipId?: string;
  deliveryDate: string;
  reference: string;
  description: string;
  movements: { productId: string; quantity: number; unitPrice: number; }[];
}

export interface ProjectState {
  version: string;
  timestamp: string;
  data: {
    companies: Company[];
    warehouses: Warehouse[];
    inventory: InventoryItemDto[];
    documents: InventoryDocument[];
    partnerships: Partnership[];
    workOrders: WorkOrderDto[];
    downtimeLogs: DowntimeLogDto[];
  };
}