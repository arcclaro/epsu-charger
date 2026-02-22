import { get } from './client';

export interface WorkJob {
  id: number;
  work_order_id?: number;
  work_order_item_id?: number;
  work_order_number?: string;
  battery_serial?: string;
  battery_part_number?: string;
  battery_amendment?: string;
  tech_pub_id?: number;
  tech_pub_cmm?: string;
  tech_pub_revision?: string;
  station_id: number;
  status: string;
  started_at?: string;
  completed_at?: string;
  started_by?: string;
  result?: string;
  overall_result?: string;
  created_at: string;
}

export function getWorkJobs(params?: {
  work_order_id?: number;
  station_id?: number;
  status?: string;
  customer_id?: number;
  from_date?: string;
  to_date?: string;
  search?: string;
}): Promise<WorkJob[]> {
  const qs = new URLSearchParams();
  if (params?.work_order_id) qs.set('work_order_id', String(params.work_order_id));
  if (params?.station_id) qs.set('station_id', String(params.station_id));
  if (params?.status) qs.set('status', params.status);
  if (params?.customer_id) qs.set('customer_id', String(params.customer_id));
  if (params?.from_date) qs.set('from_date', params.from_date);
  if (params?.to_date) qs.set('to_date', params.to_date);
  if (params?.search) qs.set('search', params.search);
  const s = qs.toString();
  return get(`/work-jobs${s ? `?${s}` : ''}`);
}

export function getWorkJob(id: number): Promise<WorkJob> {
  return get(`/work-jobs/${id}`);
}
