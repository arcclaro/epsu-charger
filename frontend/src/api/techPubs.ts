import { get, post, put, del } from './client';
import type { TechPub } from '@/types';

export function getTechPubs(): Promise<TechPub[]> {
  return get('/tech-pubs');
}

export function getTechPub(id: number): Promise<TechPub> {
  return get(`/tech-pubs/${id}`);
}

export function matchTechPub(partNumber: string): Promise<TechPub> {
  return get(`/tech-pubs/match/${encodeURIComponent(partNumber)}`);
}

export function createTechPub(data: Partial<TechPub>): Promise<TechPub> {
  return post('/tech-pubs', data);
}

export function updateTechPub(id: number, data: Partial<TechPub>): Promise<TechPub> {
  return put(`/tech-pubs/${id}`, data);
}

export function deleteTechPub(id: number): Promise<{ status: string }> {
  return del(`/tech-pubs/${id}`);
}

export function bulkReplaceApplicability(
  techPubId: number,
  entries: { part_number: string; service_type: string }[],
): Promise<unknown> {
  return put(`/tech-pubs/${techPubId}/applicability`, { entries });
}
