import { Injectable, inject } from '@angular/core';
import { Observable, of, delay } from 'rxjs';
import { HttpClient } from '@angular/common/http';
import { DiagnosticLogService } from './diagnostic-log.service';
import {
  ApiResponse, LoginResponse, SessionContext, Company, User, Role, Permission, UserCompanyAccess,
  InventoryItemDto, ProductionDashboardDto, WorkOrderDto, ProductionStatDto, DowntimeLogDto, Warehouse,
  Issue, TrendPointDto, ParetoItemDto, Partnership, Concept, PartnershipType, PartnershipStatus,
  ConceptType, InventoryDocument, ProjectState, CreateWorkOrderCommand, CreateDowntimeCommand,
  CreateInventoryItemCommand, AdjustStockCommand, CreateDocumentCommand, DocumentStatus, SelectCompanyResponse,
  RoleResponse, InvitationCreate, InvitationResponse, UserRoleAssignment
} from '@models/api.types';

@Injectable({
  providedIn: 'root'
})
export class ApiSimulationService {
  private diag = inject(DiagnosticLogService);
  private http = inject(HttpClient);

  private permissions: Permission[] = [
    { id: 'p1', name: 'dashboard', category: 'General', description: 'Ver Dashboard' },
    { id: 'p2', name: 'production', category: 'Production', description: 'Módulo de Producción' },
    { id: 'p3', name: 'orders', category: 'Production', description: 'Gestión de Órdenes' },
    { id: 'p4', name: 'inventory', category: 'Inventory', description: 'Módulo de Inventarios' },
    { id: 'p5', name: 'inventory_list', category: 'Inventory', description: 'Existencias' },
    { id: 'p6', name: 'documents', category: 'Inventory', description: 'Documentos' },
    { id: 'p7', name: 'warehouses', category: 'Inventory', description: 'Almacenes' },
    { id: 'p8', name: 'partners', category: 'Inventory', description: 'Socios' },
    { id: 'p9', name: 'system', category: 'System', description: 'Configuración Sistema' },
    { id: 'p10', name: 'snapshots', category: 'System', description: 'Rescate de Datos' }
  ];

  // DEFINICIÓN DE ROLES ESTRÍCTOS
  private roles = {
    enterprise: {
      id: 'r_ent',
      name: 'Admin Enterprise',
      description: 'Acceso Total a todos los módulos',
      permissions: this.permissions // Tiene los 10 permisos
    },
    standard: {
      id: 'r_std',
      name: 'Operador de Inventario',
      description: 'Solo puede ver Inventarios',
      // Filtrar para que solo tenga permisos relacionados con inventario
      permissions: this.permissions.filter(p => p.category === 'Inventory')
    },
    onboarding: {
      id: 'r_new',
      name: 'Configurador',
      description: 'Fase de Onboarding',
      permissions: []
    }
  };

  private companies: Company[] = [
    {
      id: '0c176b7e-d2d8-4da0-83e4-94150e967d82',
      name: 'Interno Logistics',
      registrationNumber: 'FR-889900',
      contactEmail: 'admin@interno.com',
      status: 'Active',
      logo: 'https://ui-avatars.com/api/?name=IC+Logistics&background=f59e0b&color=fff',
      plan: 'Enterprise',
      is_new: false,
      group_id: 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e',
      group_name: 'InternoCorp Group'
    },
    {
      id: '0cb7bcff-3475-40e4-aacf-fd4ef4ad76d9',
      name: 'Nueva Planta Demo',
      registrationNumber: 'DE-445566',
      contactEmail: 'ops@demo.com',
      status: 'Pending',
      logo: 'https://ui-avatars.com/api/?name=NP&background=64748b&color=fff',
      plan: 'Standard',
      is_new: true,
      group_id: 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e',
      group_name: 'InternoCorp Group'
    },
    {
      id: 'a79f7800-0a53-421e-b5a9-7b45da85dec1',
      name: 'InternoCorp Enterprise',
      registrationNumber: 'MX-000000',
      contactEmail: 'setup@internoc.com',
      status: 'Active',
      logo: 'https://ui-avatars.com/api/?name=IC+Enterprise&background=0ea5e9&color=fff',
      plan: 'Professional',
      is_new: false,
      group_id: 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e',
      group_name: 'InternoCorp Group'
    }
  ];

  private warehouses: Warehouse[] = [
    { id: '1', code: 'WH-01', name: 'Almacén Central', description: 'CD Principal', typeName: 'General', groupName: 'PT', isActive: true, sequence_number: 1 }
  ];

  private inventory: InventoryItemDto[] = [
    { id: 'inv-001', companyId: '1', productId: 'p1', name: 'Bomba Hidráulica X2', description: 'High pressure pump', sku: 'SKU-A101-B', price: { amount: 1200.50, currency: 'USD' }, stockQuantity: 45, reservedQuantity: 5, warehouseId: '1', warehouseName: 'Almacén Central', location: 'A-12-04', categoryId: '1', categoryName: 'Hidráulica', isActive: true }
  ];

  private documents: InventoryDocument[] = [
    { id: 'doc-1', folio: 'WH1-ENT-2026-001', sequence_number: 1, deliveryDate: new Date().toISOString(), conceptId: '1', conceptName: 'Entrada por Compra', conceptType: ConceptType.Entry, warehouseId: '1', warehouseName: 'Almacén Central', reference: 'FAC-990', description: 'Carga inicial demo', total_amount: 1540.50, status: DocumentStatus.Confirmed, movements: [] }
  ];
  private downtimeLogs: DowntimeLogDto[] = [];
  private partnerships: Partnership[] = [{ id: '1', code: 'SUP-001', name: 'AceroMex S.A.', type: PartnershipType.Supplier, status: PartnershipStatus.Gold }];
  private workOrders: WorkOrderDto[] = [{ id: 'wo-1', orderNumber: 'WO-1001', lineId: 'ENS-01', productId: 'p1', productName: 'Bomba Hidráulica X2', sku: 'SKU-A101-B', quantityTarget: 1000, quantityProduced: 450, progress: 45, status: 'Running', scheduledDate: new Date().toISOString(), cost: { amount: 15400.50, currency: 'USD' }, dueDate: new Date(Date.now() + 86400000 * 5).toISOString() }];
  private issues: Issue[] = [{ id: 'i1', name: 'Falla Mecánica', category: 'Mantenimiento' }, { id: 'i2', name: 'Falta de Material', category: 'Logística' }];
  private concepts: Concept[] = [{ id: '1', name: 'Entrada por Compra', type: ConceptType.Entry, affectStock: true, isSystem: true }];

  constructor() {
    this.restoreFromLocalStorage();
  }

  getFullState(): ProjectState {
    return {
      version: "2.5",
      timestamp: new Date().toISOString(),
      data: {
        companies: this.companies, warehouses: this.warehouses, inventory: this.inventory,
        documents: this.documents, partnerships: this.partnerships, workOrders: this.workOrders,
        downtimeLogs: this.downtimeLogs
      }
    };
  }

  loadFullState(state: any): boolean {
    if (!state || !state.data) return false;
    try {
      this.companies = state.data.companies || this.companies;
      this.warehouses = state.data.warehouses || this.warehouses;
      this.inventory = state.data.inventory || this.inventory;
      this.documents = state.data.documents || this.documents;
      this.partnerships = state.data.partnerships || this.partnerships;
      this.workOrders = state.data.workOrders || this.workOrders;
      this.downtimeLogs = state.data.downtimeLogs || this.downtimeLogs;
      return true;
    } catch (e) { return false; }
  }

  private restoreFromLocalStorage() {
    const KEY = 'interno_core_db';
    try {
      const saved = localStorage.getItem(KEY);
      if (!saved || saved === 'undefined' || saved === 'null') return;
      const parsed = JSON.parse(saved);
      if (parsed && typeof parsed === 'object') {
        this.loadFullState(parsed);
      }
    } catch (e) {
      localStorage.removeItem(KEY);
    }
  }

  login(u: string): Observable<ApiResponse<LoginResponse>> {
    const user: User = { id: '1', email: u, firstName: 'User', lastName: 'Interno', avatar: 'https://i.pravatar.cc/150?u=' + u, status: 'Active' };

    // Mapeo automático de roles basado en el plan de la empresa
    const accesses: UserCompanyAccess[] = this.companies.map(c => {
      let role = this.roles.enterprise;
      if (c.plan === 'Standard') role = this.roles.standard;
      if (c.is_new) role = this.roles.onboarding;

      return { company: c, role: role };
    });

    return of({
      status: 'success' as const,
      data: {
        selection_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZTdkNzM4Ni03YjFkLTQ3ZTktYTk5MS01NDYzMzA2NmY4NzUiLCJleHAiOjE3NzAzOTg1OTN9.jv1qRTQLe85lZPcGqU4vxfZWIY_rUKFizc4aoXM6ItI',
        user_id: user.id,
        companies: this.companies.map(c => ({
          company_id: c.id,
          company_name: c.name,
          logo: c.logo,
          role_names: [this.roles.enterprise.name],
          is_new: c.is_new || false,
          group_id: c.group_id || 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e',
          group_name: c.group_name || 'InternoCorp Group'
        })),
        is_new: false
      },
      message: 'Autenticación Exitosa',
      meta: {}
    }).pipe(delay(500));
  }

  selectCompany(companyId: string): Observable<ApiResponse<SelectCompanyResponse>> {
    return of({
      status: 'success' as const,
      data: {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZTdkNzM4Ni03YjFkLTQ3ZTktYTk5MS01NDYzMzA2NmY4NzUiLCJjb21wYW55X2lkIjoiMGMxNzZiN2UtZDJkOC00ZGEwLTgzZTQtOTQxNTBlOTY3ZDgyIiwicm9sZV9uYW1lcyI6WyJvcGVyYXRvciJdLCJpc19uZXciOmZhbHNlLCJleHAiOjE3NzA0MDIwNjV9.8bestsQu_shq7aGeQDPb6rqwj1qCGxwqJ05lQ98mMTY',
        token_type: 'bearer',
        company_id: companyId
      },
      message: 'Company selected, access token issued.',
      meta: {}
    }).pipe(delay(300));
  }

  getProductionDashboard(id: any): Observable<ApiResponse<ProductionDashboardDto>> {
    const trendData: TrendPointDto[] = [
      { label: 'Lun', value: 75, goal: 85 },
      { label: 'Mar', value: 82, goal: 85 },
      { label: 'Mie', value: 88, goal: 85 },
      { label: 'Jue', value: 79, goal: 85 },
      { label: 'Vie', value: 85, goal: 85 }
    ];

    const paretoData: ParetoItemDto[] = [
      { label: 'Falla Mecánica', value: 120, cumulative: 40 },
      { label: 'Falta de Material', value: 90, cumulative: 70 },
      { label: 'Ajustes de Máquina', value: 45, cumulative: 85 },
      { label: 'Mantenimiento Planeado', value: 30, cumulative: 95 },
      { label: 'Otros', value: 15, cumulative: 100 }
    ];

    return of({
      status: 'success' as const,
      data: {
        oee: 88,
        downtimeMinutes: 12,
        activeOrdersCount: this.workOrders.length,
        averageEfficiency: 92,
        hourlyStats: this.generateStats(),
        activeOrders: this.workOrders,
        recentDowntime: this.downtimeLogs,
        weeklyTrend: trendData,
        downtimePareto: paretoData
      },
      message: '',
      meta: {}
    });
  }

  private generateStats(): ProductionStatDto[] {
    return Array.from({ length: 8 }, (_, i) => ({ hour: `${8 + i}:00`, actual: 80 + i, goal: 100, status: 'good' }));
  }

  getWorkOrders(id: any): Observable<ApiResponse<WorkOrderDto[]>> { return of({ status: 'success' as const, data: this.workOrders, message: '', meta: {} }); }
  getInventoryItems(id: any): Observable<ApiResponse<InventoryItemDto[]>> { return of({ status: 'success' as const, data: this.inventory, message: '', meta: {} }); }
  getDocuments(id: any): Observable<ApiResponse<InventoryDocument[]>> { return of({ status: 'success' as const, data: this.documents, message: '', meta: {} }); }
  getDocument(companyId: string, id: string): Observable<ApiResponse<InventoryDocument>> {
    const doc = this.documents.find(d => d.id === id);
    if (doc) return of({ status: 'success' as const, data: doc, message: '', meta: {} });
    return of({ status: 'error' as const, data: null as any, message: 'Not found', meta: {} });
  }
  getNextFolioPreview(companyId: string, conceptId: string): Observable<ApiResponse<{ nextFolio: string }>> {
    return of({ status: 'success' as const, data: { nextFolio: `PREV-${conceptId}-00${this.documents.length + 1}` }, message: '', meta: {} });
  }
  getWarehouses(id: any): Observable<ApiResponse<Warehouse[]>> { return of({ status: 'success' as const, data: this.warehouses, message: '', meta: {} }); }
  getPartnerships(): Observable<ApiResponse<Partnership[]>> { return of({ status: 'success' as const, data: this.partnerships, message: '', meta: {} }); }
  getConcepts(): Observable<ApiResponse<Concept[]>> { return of({ status: 'success' as const, data: this.concepts, message: '', meta: {} }); }
  getIssues(): Observable<ApiResponse<Issue[]>> { return of({ status: 'success' as const, data: this.issues, message: '', meta: {} }); }
  getProductCategories(): Observable<ApiResponse<any[]>> { return of({ status: 'success' as const, data: [{ id: '1', name: 'General' }], message: '', meta: {} }); }
  getWarehouseTypes(): Observable<ApiResponse<any[]>> { return of({ status: 'success' as const, data: [], message: '', meta: {} }); }
  getWarehouseGroups(): Observable<ApiResponse<any[]>> { return of({ status: 'success' as const, data: [], message: '', meta: {} }); }
  searchEmployees(q: string): Observable<ApiResponse<any[]>> { return of({ status: 'success' as const, data: [], message: '', meta: {} }); }
  completeOnboarding(companyId: string, state: any): Observable<ApiResponse<any>> {
    return of({ status: 'success' as const, data: { company_id: companyId, is_new: false }, message: 'Onboarding completado', meta: {} }).pipe(delay(500));
  }

  createWorkOrder(companyId: any, cmd: CreateWorkOrderCommand): Observable<ApiResponse<WorkOrderDto>> {
    const product = this.inventory.find(i => i.productId === cmd.productId);
    const newOrder: WorkOrderDto = { id: 'wo-' + Math.random(), orderNumber: 'WO-' + (1000 + this.workOrders.length), lineId: 'ENS-01', productId: cmd.productId, productName: product?.name || 'Nuevo', sku: product?.sku || 'SKU', quantityTarget: cmd.quantity, quantityProduced: 0, progress: 0, status: 'Pending', scheduledDate: cmd.scheduledDate, cost: cmd.estimatedCost, dueDate: cmd.scheduledDate };
    this.workOrders.push(newOrder);
    return of({ status: 'success' as const, data: newOrder, message: 'Creada', meta: {} }).pipe(delay(300));
  }

  createDowntime(companyId: any, cmd: CreateDowntimeCommand): Observable<ApiResponse<DowntimeLogDto>> {
    const log: DowntimeLogDto = { id: 'dt-' + Math.random(), lineId: cmd.lineId, issueName: 'Paro', durationMinutes: 0, startTime: new Date().toISOString(), status: 'Active' };
    this.downtimeLogs.push(log);
    return of({ status: 'success' as const, data: log, message: 'Registrado', meta: {} }).pipe(delay(300));
  }

  createInventoryItem(companyId: any, cmd: CreateInventoryItemCommand): Observable<ApiResponse<InventoryItemDto>> {
    const newItem: InventoryItemDto = { id: 'inv-' + Math.random(), companyId, productId: 'p-' + Math.random(), name: cmd.name, description: cmd.description, sku: cmd.sku, price: cmd.price, stockQuantity: cmd.initialStockQuantity, reservedQuantity: 0, warehouseId: cmd.warehouseId, warehouseName: 'Almacén', location: 'A1', categoryId: cmd.categoryId, categoryName: 'Cat', isActive: true };
    this.inventory.push(newItem);
    return of({ status: 'success' as const, data: newItem, message: 'Creado', meta: {} }).pipe(delay(300));
  }

  adjustStock(companyId: any, cmd: AdjustStockCommand): Observable<ApiResponse<any>> {
    const item = this.inventory.find(i => i.id === cmd.itemId);
    if (item) item.stockQuantity += cmd.quantityChange;
    return of({ status: 'success' as const, data: null, message: 'Ajustado', meta: {} }).pipe(delay(300));
  }

  createDocument(companyId: any, cmd: CreateDocumentCommand): Observable<ApiResponse<InventoryDocument>> {
    const newDoc: InventoryDocument = { id: 'doc-' + Math.random(), folio: 'INV-001', sequence_number: this.documents.length + 1, deliveryDate: cmd.deliveryDate, conceptId: cmd.conceptId.toString(), conceptName: 'Movimiento', conceptType: ConceptType.Entry, warehouseId: cmd.warehouseId, warehouseName: 'Almacén', reference: cmd.reference, description: cmd.description, total_amount: 0, status: DocumentStatus.Confirmed, movements: cmd.movements };
    this.documents.push(newDoc);
    return of({ status: 'success' as const, data: newDoc, message: 'Generado', meta: {} }).pipe(delay(300));
  }

  // === ADMIN V2 MOCKS ===
  private v2Roles: RoleResponse[] = [
    { id: 'eb8f7e2c-3f4a-11ee-be56-0242ac120002', name: 'Administrador Global' },
    { id: 'eb8f7e2c-3f4a-11ee-be56-0242ac120003', name: 'Gerente de Planta' },
    { id: 'eb8f7e2c-3f4a-11ee-be56-0242ac120004', name: 'Operador Logístico' }
  ];

  getRolesV2(): Observable<ApiResponse<RoleResponse[]>> {
    return of({
      status: 'success' as const,
      data: this.v2Roles,
      message: 'Roles fetched successfully',
      meta: {}
    }).pipe(delay(400));
  }

  inviteUserV2(payload: InvitationCreate): Observable<ApiResponse<InvitationResponse>> {
    const inv: InvitationResponse = {
      id: Math.random().toString(36).substring(2, 15),
      code: Math.random().toString(36).substring(2, 10).toUpperCase(),
      email: payload.email,
      role_id: payload.role_id,
      company_id: 'eb8f7e2c-3f4a-4b5c-8d7e-1f2a3b4c5d6e',
      expires_at: new Date(Date.now() + 86400000 * 3).toISOString(),
      is_used: false
    };
    return of({
      status: 'success' as const,
      data: inv,
      message: 'Invitation generated',
      meta: {}
    }).pipe(delay(600));
  }

  assignRoleV2(payload: UserRoleAssignment): Observable<ApiResponse<void>> {
    return of({
      status: 'success' as const,
      data: undefined,
      message: 'Role assigned successfully',
      meta: {}
    }).pipe(delay(500));
  }
}