export interface Customer {
  id: number;
  name: string;
  customer_code: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country: string;
  tax_id?: string;
  payment_terms: string;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
  work_order_stats?: {
    total: number;
    in_progress: number;
    completed: number;
  };
}

export interface CustomerCreate {
  name: string;
  customer_code?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  tax_id?: string;
  payment_terms?: string;
  notes?: string;
}
