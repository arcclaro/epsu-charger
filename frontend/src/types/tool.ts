export interface Tool {
  id: number;
  part_number: string;
  description?: string;
  manufacturer?: string;
  serial_number: string;
  calibration_date?: string;
  valid_until?: string;
  internal_reference?: string;
  tool_id_display?: string;
  category?: string;
  is_active: boolean;
  calibration_certificate?: string;
  calibrated_by?: string;
  created_at: string;
  updated_at: string;
}
