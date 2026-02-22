import { get, post, put, del } from './client';
import type { Customer, CustomerCreate, WorkOrder } from '@/types';

export function getCustomers(search?: string, limit?: number): Promise<Customer[]> {
  const qs = new URLSearchParams();
  if (search) qs.set('search', search);
  if (limit) qs.set('limit', String(limit));
  const s = qs.toString();
  return get(`/customers${s ? `?${s}` : ''}`);
}

export function getCustomer(id: number): Promise<Customer> {
  return get(`/customers/${id}`);
}

export function createCustomer(data: CustomerCreate): Promise<{ id: number; customer_code: string; message: string }> {
  return post('/customers', data);
}

export function updateCustomer(id: number, data: Partial<CustomerCreate>): Promise<{ success: boolean; message: string }> {
  return put(`/customers/${id}`, data);
}

export function deleteCustomer(id: number): Promise<{ status: string }> {
  return del(`/customers/${id}`);
}

export function getCustomerWorkOrders(id: number): Promise<WorkOrder[]> {
  return get(`/customers/${id}/work-orders`);
}
