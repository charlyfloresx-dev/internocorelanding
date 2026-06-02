/**
 * MES Service Types — Phase 154 Part 3
 * Mirrors backend/mes_service graphic_service.py response dataclasses.
 */

export interface SupportMemberRead {
  id: string;
  collaborator_id: string;
  role: string;
}

export interface ResourceRead {
  id: string;
  code: string;
  name: string;
  description: string | null;
  resource_type: 'CELL' | 'MACHINE' | 'AREA' | 'LINE' | null;
  capacity: number | null;
  warehouse_id: string | null;
  production_area_id: string | null;
  active: boolean;
  support_members: SupportMemberRead[];
}

export interface FacilityRead {
  id: string;
  code: string;
  name: string;
  location_description: string | null;
}

export interface ProductionAreaRead {
  id: string;
  name: string;
  description: string | null;
  facility_id: string | null;
}

/** Single bar in the hora×hora chart */
export interface HourlySlot {
  time: string;        // "HH:MM"
  goal: number;
  actual: number;
  missing: number;
  excess: number;
  efficiency: number;  // 0-100+
}

export interface BreakSlot {
  code: string;
  label: string;
  break_type?: string;  // BREAK | MEAL | MAINTENANCE
  start_time: string;   // "HH:MM"
  end_time: string;
  duration_minutes: number;
}

export interface CumulativeRow {
  time: string;
  goal_cumulative: number;
  actual_cumulative: number;
}

/** Full response from GET /resources/{code}/graphic */
export interface ResourceGraphicResponse {
  resource_code: string;
  shift_name: string;
  shift_start: string;
  shift_end: string;
  total_goal: number;
  total_actual: number;
  breaks: BreakSlot[];
  hours: HourlySlot[];
  cumulative_table: CumulativeRow[];
}

export interface ActiveWorkOrderResponse {
  work_order_id: string;
  order_number: string;
  item_code: string;
  manufactured_quantity: number;
  order_quantity: number;
  progress_pct: number;
  status: string;
  material_status?: string;  // "PENDING_ISSUE" | "ISSUED" | null
}

export interface PlannedWorkOrderResponse {
  work_order_id: string;
  order_number: string;
  item_code: string;
  planned_quantity: number;
  actual_quantity: number;
  status: string;
}

// ── Phase 156-B: Resource + Shift config types ─────────────────────────────

export interface ResourceCreate {
  code: string;
  name: string;
  description?: string | null;
  resource_type?: 'CELL' | 'MACHINE' | 'AREA' | 'LINE' | null;
  capacity?: number | null;
  production_area_id?: string | null;
}

export interface ResourceUpdate {
  name?: string;
  description?: string | null;
  resource_type?: 'CELL' | 'MACHINE' | 'AREA' | 'LINE' | null;
  capacity?: number | null;
  production_area_id?: string | null;
  active?: boolean;
}

export interface ShiftRead {
  id: string;
  code: string;
  name: string;
  start_time: string;   // "HH:MM"
  end_time: string;     // "HH:MM"
  is_overnight: boolean;
  break_minutes: number;
  is_active: boolean;
  resource_id: string | null;
  breaks: BreakSlot[];
}

export interface ShiftCreate {
  code: string;
  name: string;
  start_time: string;
  end_time: string;
  is_overnight?: boolean;
  break_minutes?: number;
}

export interface ShiftUpdate {
  name?: string;
  start_time?: string;
  end_time?: string;
  is_overnight?: boolean;
  break_minutes?: number;
  is_active?: boolean;
}

export interface ShiftBreakCreate {
  code: string;
  label: string;
  break_type?: 'BREAK' | 'MEAL' | 'MAINTENANCE';
  start_time: string;
  end_time: string;
  duration_minutes: number;
}

// ── Phase 170: Headcount Tracking & Shop Floor Badge Auth ──────────────────

export type LaborStatus = 'ACTIVE' | 'ON_PERMIT' | 'TRANSFERRED_IN';

export interface CollaboratorOnFloor {
  id: string | null;
  name: string;
  status: LaborStatus;
  clock_in: string;   // "HH:MM"
  is_deviation: boolean;
}

export interface HeadcountSummary {
  active: number;
  on_permit: number;
  transferred_in: number;
  total_rostered: number;
}

export interface HeadcountResponse {
  resource_id: string;
  snapshot_time: string;
  headcount: HeadcountSummary;
  collaborators: CollaboratorOnFloor[];
}

export interface HourlyLaborPoint {
  hour: number;
  label: string;
  active: number;
  on_permit: number;
  transferred_in: number;
  transferred_out: number;
  total: number;
  total_labor_minutes: number;
  paid_hrs: number;
}

export interface HeadcountHistoryResponse {
  resource_id: string;
  date: string;
  series: HourlyLaborPoint[];
}

export interface BadgeClockInRequest {
  resource_code: string;
  production_run_id?: string;   // optional — auto-resolved server-side from resource_code
  badge_raw_value: string;
  client_timestamp: string;
}

export type BadgeAction = 'CLOCK_IN' | 'TRANSFER' | 'ALREADY_CLOCKED_IN';

export interface BadgeClockInResponse {
  status: 'SUCCESS' | 'ERROR';
  action: BadgeAction;
  collaborator: {
    employee_number: number | null;
    full_name: string;
    collaborator_id: string;
    category_assigned: string;
  };
  timestamp: string;
}

export interface CollaboratorBadgeRead {
  id: string;
  collaborator_id: string;
  collaborator_name: string;
  employee_number: number | null;
  badge_raw_value: string;
  badge_type: 'BARCODE' | 'QR' | 'RFID';
  is_active: boolean;
  expires_at: string | null;
}

export interface CollaboratorBadgeCreate {
  collaborator_id: string;
  badge_raw_value: string;
  badge_type: 'BARCODE' | 'QR' | 'RFID';
  expires_at?: string | null;
}
