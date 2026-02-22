import { get, post, put, del } from './client';
import type { Tool } from '@/types';

export function getTools(category?: string): Promise<Tool[]> {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  return get(`/tools${params}`);
}

export function getValidTools(category?: string): Promise<Tool[]> {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  return get(`/tools/valid${params}`);
}

export function getTool(id: number): Promise<Tool> {
  return get(`/tools/${id}`);
}

export function createTool(data: Partial<Tool>): Promise<Tool> {
  return post('/tools', data);
}

export function updateTool(id: number, data: Partial<Tool>): Promise<Tool> {
  return put(`/tools/${id}`, data);
}

export function deleteTool(id: number): Promise<{ status: string }> {
  return del(`/tools/${id}`);
}
