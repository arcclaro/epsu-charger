export interface WorkOrder {
  id: number;
  work_order_number: string;
  customer_reference?: string;
  customer_id: number;
  customer_name?: string;
  service_type: string;
  priority: string;
  status: string;
  received_date: string;
  due_date?: string;
  started_date?: string;
  completed_date?: string;
  assigned_technician?: string;
  customer_notes?: string;
  technician_notes?: string;
  estimated_cost?: number;
  actual_cost?: number;
  invoiced: boolean;
  invoice_number?: string;
  created_at: string;
  updated_at: string;
  items?: WorkOrderItem[];
  item_count?: number;
}

export interface WorkOrderItem {
  id: number;
  work_order_id: number;
  serial_number: string;
  part_number: string;
  revision: string;
  amendment?: string;
  profile_id?: number;
  manufacture_date?: string;
  battery_block_replacement_date?: string;
  age_months?: number;
  status: string;
  current_station_id?: number;
  current_test_id?: number;
  reported_condition?: string;
  visual_inspection_notes?: string;
  visual_inspection_passed?: boolean;
  result?: string;
  test_passed?: boolean;
  failure_reason?: string;
  measured_capacity_ah?: number;
  received_at: string;
  testing_started_at?: string;
  testing_completed_at?: string;
}

export interface WorkOrderIntake {
  customer_id: number;
  customer_reference?: string;
  service_type?: string;
  customer_notes?: string;
  batteries: {
    serial_number: string;
    part_number: string;
    revision: string;
    amendment?: string;
    reported_condition?: string;
  }[];
}
