export interface Tool {
  id: number;
  part_number: string;
  description?: string;
  manufacturer?: string;
  serial_number: string;
  calibration_date?: string;
  verification_date?: string;
  verification_cycle_days?: number;
  valid_until?: string;
  internal_reference?: string;
  tool_id_display?: string;
  tcp_ip_address?: string;
  designated_station?: number;
  category?: string;
  is_active: boolean;
  calibration_certificate?: string;
  calibrated_by?: string;
  created_at: string;
  updated_at: string;
}
