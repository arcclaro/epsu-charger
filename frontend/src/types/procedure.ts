import type { StepType } from './jobTask';

export interface ProcedureStepSummary {
  step_id: number;
  step_number: number;
  step_type: StepType;
  label: string;
  description?: string;
  is_automated: boolean;
  estimated_duration_min: number;
  requires_tools: string[];
  param_source: string;
  pass_criteria_type?: string;
  pass_criteria_value?: string;
  measurement_key?: string;
  measurement_unit?: string;
  measurement_label?: string;
}

export interface ProcedureSection {
  section_id: number;
  section_number: string;
  title: string;
  section_type: string;
  is_mandatory: boolean;
  description?: string;
  steps: ProcedureStepSummary[];
}

export interface ResolvedProcedure {
  tech_pub_id: number;
  cmm_number: string;
  cmm_revision: string;
  cmm_title: string;
  part_number: string;
  amendment: string;
  service_type: string;
  total_steps: number;
  estimated_hours: number;
  sections: ProcedureSection[];
}

export interface TechPubApplicabilityEntry {
  part_number: string;
  service_type: string;
}

export interface TechPub {
  id: number;
  cmm_number: string;
  title: string;
  revision?: string;
  revision_date?: string;
  applicable_part_numbers: string[];
  ata_chapter?: string;
  issued_by?: string;
  manufacturer?: string;
  applicability?: TechPubApplicabilityEntry[];
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TechPubSection {
  id: number;
  tech_pub_id: number;
  section_number: string;
  title: string;
  section_type: string;
  description?: string;
  sort_order: number;
  is_mandatory: boolean;
  condition_type: string;
  condition_key?: string;
  condition_value?: string;
  is_active: boolean;
  created_at: string;
}

export interface ProcedureStep {
  id: number;
  section_id: number;
  step_number: number;
  step_type: StepType;
  label: string;
  description?: string;
  param_source: string;
  param_overrides: Record<string, unknown>;
  pass_criteria_type?: string;
  pass_criteria_value?: string;
  measurement_key?: string;
  measurement_unit?: string;
  measurement_label?: string;
  estimated_duration_min: number;
  is_automated: boolean;
  requires_tools: string[];
  condition_type: string;
  condition_key?: string;
  condition_value?: string;
  sort_order: number;
  is_active: boolean;
}
