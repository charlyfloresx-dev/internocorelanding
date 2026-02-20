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
  selection_token: string;
  user_id: string; // Backend sends ID string only
  companies: CompanySelection[]; // Full company selection objects
  is_new: boolean; // Normalized to snake_case for backend parity
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
}

export interface SessionContext {
  access_token: string; // Renamed from sessionToken for clarity
  companyId: string;
  role: Role;
  permissions: string[];
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
  typeId: number;
  typeName: string;
  groupId: number;
  groupName: string;
  location: string;
  capacity: number;
  unitCode: string;
  isActive: boolean;
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
  id: number;
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
  Entry = 1,
  Output = 2
}

export interface Concept {
  id: number;
  name: string;
  type: ConceptType;
  affectStock: boolean;
  isSystem: boolean;
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
  deliveryDate: string;
  conceptId: number;
  conceptName: string;
  conceptType: ConceptType;
  warehouseId: string;
  warehouseName: string;
  partnershipId?: number;
  partnershipName?: string;
  reference: string;
  description: string;
  total: number;
  status: DocumentStatus;
  movements: any[];
}

export interface CreateDocumentCommand {
  conceptId: number;
  warehouseId: string;
  partnershipId?: number;
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