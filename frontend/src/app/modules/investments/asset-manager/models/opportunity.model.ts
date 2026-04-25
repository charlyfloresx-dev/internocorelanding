export interface Money {
  amount: number;
  currency: string;
}

export interface OpportunityResponse {
  id: string;
  cve_cat: string;
  address: string;
  status: 'DETECTED' | 'IN_ANALYSIS' | 'NEGOTIATION' | 'EXECUTED' | 'DISCARDED';
  valor_m2_zona: Money;
  superficie: number;
  adeudo_detectado: Money;
  historical_base_value?: Money; // Valor catastral base del Padrón (2020)
  appreciation_rate?: number; // % de plusvalía detectada
  roi_projected: number;
  risk_buffer: number;
  owner_name?: string;
  created_at: string;
}

export interface KanbanBoard {
  columns: {
    id: string;
    title: string;
    opportunities: OpportunityResponse[];
  }[];
}
