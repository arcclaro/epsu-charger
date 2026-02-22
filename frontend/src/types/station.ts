export type StationState = 'empty' | 'dock_detected' | 'ready' | 'running' | 'complete' | 'error';

export type TestPhase =
  | 'idle'
  | 'pre_discharge'
  | 'pre_rest'
  | 'reconditioning'
  | 'charging'
  | 'post_charge_rest'
  | 'cap_discharging'
  | 'fast_discharging'
  | 'post_partial_charge'
  | 'complete_pass'
  | 'complete_fail';

export interface BatteryConfig {
  serial_number: string;
  part_number: string;
  amendment?: string;
  eeprom_present: boolean;
}

export interface StationStatus {
  station_id: number;
  state: StationState;
  temperature_c: number;
  temperature_valid: boolean;
  voltage_mv: number;
  current_ma: number;
  eeprom_present: boolean;
  error_message: string | null;
  session_id: number | null;
  work_order_item_id: number | null;
  work_job_id: number | null;
  test_phase: TestPhase;
  current_task_label: string | null;
  elapsed_time_s: number;
  battery_config: BatteryConfig | null;
  is_online?: boolean;
  is_enabled?: boolean;
  state_progress_pct?: number;
  dock_serial?: string | null;
}

export interface StationEquipment {
  id: number;
  station_id: number;
  equipment_role: 'psu' | 'dc_load' | 'rp2040' | 'temp_sensor';
  tool_id?: number;
  model?: string;
  serial_number?: string;
  ip_address?: string;
  is_active: boolean;
}

export interface ControlCommand {
  station_id: number;
  command: 'charge' | 'discharge' | 'wait' | 'stop';
  voltage_mv?: number;
  current_ma?: number;
  voltage_min_mv?: number;
  duration_min?: number;
  delta_v_enabled?: boolean;
  delta_v_threshold_mv?: number;
  delta_v_peak_hold_time_s?: number;
  delta_v_min_charge_time_min?: number;
}

export interface DiagnosticsReport {
  station_id: number;
  psu_status: string;
  load_status: string;
  rp2040_status: string;
  temp_sensor_status: string;
  [key: string]: unknown;
}
