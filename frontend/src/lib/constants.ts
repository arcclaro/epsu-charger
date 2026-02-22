export const STATION_COUNT = 12;

export const STATE_COLORS: Record<string, string> = {
  empty: 'bg-gray-600',
  dock_detected: 'bg-blue-500',
  ready: 'bg-cyan-500',
  running: 'bg-green-500',
  complete: 'bg-emerald-400',
  error: 'bg-red-500',
};

export const STATE_LABELS: Record<string, string> = {
  empty: 'Empty',
  dock_detected: 'Dock Detected',
  ready: 'Ready',
  running: 'Running',
  complete: 'Complete',
  error: 'Error',
};

export const PHASE_LABELS: Record<string, string> = {
  idle: 'Idle',
  pre_discharge: 'Pre-Discharge',
  pre_rest: 'Pre-Rest',
  reconditioning: 'Reconditioning',
  charging: 'Charging',
  post_charge_rest: 'Post-Charge Rest',
  cap_discharging: 'Capacity Discharge',
  fast_discharging: 'Fast Discharge',
  post_partial_charge: 'Post Partial Charge',
  complete_pass: 'Complete (Pass)',
  complete_fail: 'Complete (Fail)',
};

export const STEP_TYPE_LABELS: Record<string, string> = {
  charge: 'Charge',
  discharge: 'Discharge',
  rest: 'Rest',
  wait_temp: 'Wait Temperature',
  measure_resistance: 'Measure Resistance',
  measure_voltage: 'Measure Voltage',
  measure_weight: 'Measure Weight',
  measure_temperature: 'Measure Temperature',
  visual_check: 'Visual Check',
  functional_check: 'Functional Check',
  record_value: 'Record Value',
  evaluate_result: 'Evaluate Result',
  operator_action: 'Operator Action',
};

export const TASK_STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-500',
  skipped: 'bg-yellow-600',
  in_progress: 'bg-blue-500',
  paused: 'bg-orange-500',
  awaiting_input: 'bg-amber-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
  aborted: 'bg-red-700',
};

export const SERVICE_TYPES = [
  { value: 'capacity_test', label: 'Capacity Test' },
  { value: 'inspection', label: 'Inspection Only' },
  { value: 'full_overhaul', label: 'Full Overhaul' },
  { value: 'fast_discharge_test', label: 'Fast Discharge Test' },
];
