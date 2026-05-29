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
}

export interface PlannedWorkOrderResponse {
  work_order_id: string;
  order_number: string;
  item_code: string;
  planned_quantity: number;
  actual_quantity: number;
  status: string;
}
