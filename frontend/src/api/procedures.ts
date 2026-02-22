import { get } from './client';
import type { ResolvedProcedure, TechPubSection, ProcedureStep } from '@/types';

export function resolveProcedure(
  itemId: number,
  serviceType?: string,
  monthsSinceService?: number,
): Promise<ResolvedProcedure> {
  const params = new URLSearchParams();
  if (serviceType) params.set('service_type', serviceType);
  if (monthsSinceService != null) params.set('months_since_service', String(monthsSinceService));
  const qs = params.toString();
  return get(`/procedures/resolve/${itemId}${qs ? `?${qs}` : ''}`);
}

export function getSections(techPubId: number): Promise<TechPubSection[]> {
  return get(`/procedures/sections/${techPubId}`);
}

export function getSteps(sectionId: number): Promise<ProcedureStep[]> {
  return get(`/procedures/steps/${sectionId}`);
}
