export type StepType =
  | 'charge'
  | 'discharge'
  | 'rest'
  | 'wait_temp'
  | 'measure_resistance'
  | 'measure_voltage'
  | 'measure_weight'
  | 'measure_temperature'
  | 'visual_check'
  | 'functional_check'
  | 'record_value'
  | 'evaluate_result'
  | 'operator_action';

export type TaskStatus =
  | 'pending'
  | 'skipped'
  | 'in_progress'
  | 'paused'
  | 'awaiting_input'
  | 'completed'
  | 'failed'
  | 'aborted';

export type StepResult = 'pass' | 'fail' | 'info' | 'skipped';

export interface JobTask {
  id: number;
  work_job_id: number;
  parent_task_id?: number;
  section_id?: number;
  step_id?: number;
  task_number: number;
  step_type: StepType;
  label: string;
  description?: string;
  is_automated: boolean;
  source: 'procedure' | 'manual' | 'rule_engine';
  status: TaskStatus;
  params: Record<string, unknown>;
  step_result?: StepResult;
  measured_values: Record<string, unknown>;
  result_notes?: string;
  start_time?: string;
  end_time?: string;
  chart_data: unknown[];
  data_points: number;
  influx_query_ref?: string;
  performed_by?: string;
  verified_by?: string;
  created_at: string;
  tools_used?: TaskToolUsage[];
}

export interface TaskToolUsage {
  id: number;
  job_task_id: number;
  tool_id: number;
  tool_id_display: string;
  tool_description?: string;
  tool_serial_number: string;
  tool_calibration_valid: boolean;
  tool_calibration_due?: string;
  tool_calibration_cert?: string;
  used_at: string;
}

export interface ManualResultSubmit {
  measured_values: Record<string, unknown>;
  step_result: StepResult;
  result_notes: string;
  performed_by: string;
  tool_ids?: number[];
}

export interface StartJobRequest {
  work_order_item_id: number;
  station_id: number;
  service_type?: string;
  months_since_service?: number;
  started_by: string;
}

export interface StartJobResponse {
  work_job_id: number;
  tasks_created: number;
  estimated_hours: number;
  cmm: string;
  message: string;
}
