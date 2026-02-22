import { get, post, put, del } from './client';

export interface BatteryProfile {
  id: number;
  part_number: string;
  amendment?: string;
  description: string;
  manufacturer: string;
  nominal_voltage_v: number;
  capacity_ah: number;
  num_cells: number;
  chemistry: string;
  std_charge_current_ma: number;
  std_charge_duration_h: number;
  std_charge_voltage_limit_mv: number;
  std_charge_temp_max_c: number;
  cap_test_current_a: number;
  cap_test_voltage_min_mv: number;
  cap_test_duration_min: number;
  cap_test_temp_max_c: number;
  fast_charge_enabled: boolean;
  fast_charge_current_a?: number;
  fast_charge_max_duration_min?: number;
  fast_charge_delta_v_mv?: number;
  trickle_charge_current_ma?: number;
  trickle_charge_voltage_max_mv?: number;
  partial_charge_duration_h?: number;
  rest_period_age_threshold_months: number;
  rest_period_duration_h: number;
  emergency_temp_max_c: number;
  emergency_temp_min_c: number;
  delta_v_enabled: boolean;
  fast_discharge_enabled: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export function getBatteryProfiles(activeOnly?: boolean): Promise<BatteryProfile[]> {
  const params = activeOnly != null ? `?active_only=${activeOnly}` : '';
  return get(`/battery-profiles${params}`);
}

export function getBatteryProfile(id: number): Promise<BatteryProfile> {
  return get(`/battery-profiles/${id}`);
}

export function getBatteryProfileByPart(partNumber: string, amendment?: string): Promise<BatteryProfile> {
  const params = amendment ? `?amendment=${encodeURIComponent(amendment)}` : '';
  return get(`/battery-profiles/by-part/${encodeURIComponent(partNumber)}${params}`);
}

export function createBatteryProfile(data: Partial<BatteryProfile>): Promise<BatteryProfile> {
  return post('/battery-profiles', data);
}

export function updateBatteryProfile(id: number, data: Partial<BatteryProfile>): Promise<BatteryProfile> {
  return put(`/battery-profiles/${id}`, data);
}

export function deleteBatteryProfile(id: number): Promise<{ status: string }> {
  return del(`/battery-profiles/${id}`);
}
