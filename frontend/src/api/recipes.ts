import { get } from './client';

export interface Recipe {
  id: number;
  name: string;
  tech_pub_id?: number;
  cmm_ref?: string;
  part_number?: string;
  description?: string;
  steps: unknown[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export function getRecipes(params?: { tech_pub_id?: number; part_number?: string }): Promise<Recipe[]> {
  const qs = new URLSearchParams();
  if (params?.tech_pub_id) qs.set('tech_pub_id', String(params.tech_pub_id));
  if (params?.part_number) qs.set('part_number', params.part_number);
  const s = qs.toString();
  return get(`/recipes${s ? `?${s}` : ''}`);
}

export function getRecipe(id: number): Promise<Recipe> {
  return get(`/recipes/${id}`);
}
