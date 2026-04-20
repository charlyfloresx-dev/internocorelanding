import { ApiResponse } from './domain.types';

/**
 * Phase 50: HR & Eligibility Models
 * Mirror of backend/hr_service/app/schemas/collaborator.py
 */

export interface EligibilityDetail {
  document: string;
  expiry_date?: string;
  days_remaining?: number;
}

export interface EligibilityResponse {
  eligible: boolean;
  reason: string;
  collaborator_id?: string;
  full_name?: string;
  details?: EligibilityDetail;
}

/**
 * Common emergency contact structure for industrial safety
 */
export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  alternative_phone?: string;
}

export interface CollaboratorRead {
  id: string;
  internal_id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  department?: string;
  job_title?: string;
  translation_key?: string;
  is_active: boolean;
  is_direct: boolean;
  home_warehouse_id?: string;
  m3_operator_id?: string;
  hazardous_material_certified: boolean;
  blood_type?: string;
  emergency_contact?: EmergencyContact;
  company_id: string;
}
