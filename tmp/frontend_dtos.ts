export enum MovementType {
  ENTRADA = 'ENTRADA',
  SALIDA = 'SALIDA',
  TRASPASO = 'TRASPASO'
}

export interface MovementConceptDTO {
  id: str;
  code: str;
  name: str;
  type: MovementType;
  requires_external_entity: boolean;
  requires_target_warehouse: boolean;
}

export enum WarehouseType {
  PHYSICAL = 'PHYSICAL',
  VIRTUAL = 'VIRTUAL',
  TRANSIT = 'TRANSIT'
}

export interface WarehouseDTO {
  id: str;
  code: str;
  name: str;
  type: WarehouseType;
  is_active: boolean;
}

export interface UOMDTO {
  id: str;
  code: str;
  name: str;
  plural: str;
  abbreviation: str;
  conversion_factor: number;
}
