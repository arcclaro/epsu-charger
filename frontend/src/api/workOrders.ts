import { get, post, put, del } from './client';
import type { WorkOrder, WorkOrderIntake } from '@/types';

export function getWorkOrders(params?: {
  status?: string;
  search?: string;
  limit?: number;
}): Promise<WorkOrder[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.search) qs.set('search', params.search);
  if (params?.limit) qs.set('limit', String(params.limit));
  const s = qs.toString();
  return get(`/work-orders${s ? `?${s}` : ''}`);
}

export function getWorkOrder(id: number): Promise<WorkOrder> {
  return get(`/work-orders/${id}`);
}

export function createWorkOrder(data: WorkOrderIntake): Promise<{ status: string; message: string; work_order: WorkOrder }> {
  return post('/work-orders', data);
}

export function updateWorkOrder(id: number, data: Partial<WorkOrder>): Promise<WorkOrder> {
  return put(`/work-orders/${id}`, data);
}

export function deleteWorkOrder(id: number): Promise<{ status: string }> {
  return del(`/work-orders/${id}`);
}

export function assignItemToStation(
  woId: number,
  itemId: number,
  stationId: number,
): Promise<{ status: string; message: string }> {
  return post(`/work-orders/${woId}/items/${itemId}/assign`, { station_id: stationId });
}
