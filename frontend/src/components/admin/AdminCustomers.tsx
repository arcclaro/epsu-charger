import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getCustomers, createCustomer, updateCustomer, deleteCustomer } from '@/api/customers';
import type { Customer } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';

const emptyForm = {
  name: '',
  customer_code: '',
  contact_person: '',
  email: '',
  phone: '',
  address_line1: '',
  address_line2: '',
  city: '',
  state: '',
  postal_code: '',
  country: '',
  tax_id: '',
  payment_terms: '',
  notes: '',
};

const columns: Column<Customer>[] = [
  { header: 'Code', accessor: 'customer_code', className: 'font-mono text-xs' },
  { header: 'Name', accessor: 'name', className: 'font-medium' },
  { header: 'Contact', accessor: (c) => c.contact_person || '-', className: 'text-muted-foreground' },
  { header: 'Email', accessor: (c) => c.email || '-', className: 'text-muted-foreground' },
  { header: 'Country', accessor: 'country' },
];

export function AdminCustomers() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(
    () => getCustomers(search || undefined),
    [search]
  );
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<Customer | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((c: Customer) => {
    setEditing(c);
    setForm({
      name: c.name,
      customer_code: c.customer_code,
      contact_person: c.contact_person ?? '',
      email: c.email ?? '',
      phone: c.phone ?? '',
      address_line1: c.address_line1 ?? '',
      address_line2: c.address_line2 ?? '',
      city: c.city ?? '',
      state: c.state ?? '',
      postal_code: c.postal_code ?? '',
      country: c.country,
      tax_id: c.tax_id ?? '',
      payment_terms: c.payment_terms,
      notes: c.notes ?? '',
    });
    setFormOpen(true);
  }, []);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      if (editing) {
        await updateCustomer(editing.id, form);
      } else {
        await createCustomer(form);
      }
      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save customer failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, refetch]);

  const handleDelete = useCallback(async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await deleteCustomer(deleting.id);
      setDeleting(null);
      refetch();
    } catch (e) {
      console.error('Delete customer failed:', e);
    } finally {
      setDeleteLoading(false);
    }
  }, [deleting, refetch]);

  return (
    <>
      <AdminCrudTable
        title="Customers"
        data={data}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search customers..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Customer' : 'New Customer'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Name" name="name" value={form.name} onChange={onChange} required />
          <FormField label="Customer Code" name="customer_code" value={form.customer_code} onChange={onChange} disabled={!!editing} placeholder="Auto-generated if empty" />
          <FormField label="Contact Person" name="contact_person" value={form.contact_person} onChange={onChange} />
          <FormField label="Email" name="email" value={form.email} onChange={onChange} type="email" />
          <FormField label="Phone" name="phone" value={form.phone} onChange={onChange} type="tel" />
          <FormField label="Country" name="country" value={form.country} onChange={onChange} />
          <FormField label="Address Line 1" name="address_line1" value={form.address_line1} onChange={onChange} className="col-span-2" />
          <FormField label="Address Line 2" name="address_line2" value={form.address_line2} onChange={onChange} className="col-span-2" />
          <FormField label="City" name="city" value={form.city} onChange={onChange} />
          <FormField label="State" name="state" value={form.state} onChange={onChange} />
          <FormField label="Postal Code" name="postal_code" value={form.postal_code} onChange={onChange} />
          <FormField label="Tax ID" name="tax_id" value={form.tax_id} onChange={onChange} />
          <FormField label="Payment Terms" name="payment_terms" value={form.payment_terms} onChange={onChange} />
          <FormField label="Notes" name="notes" value={form.notes} onChange={onChange} textarea className="col-span-2" />
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Customer"
        description={`Delete customer "${deleting?.name}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
