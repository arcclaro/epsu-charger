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
  contact_person: '',
};

const columns: Column<Customer>[] = [
  { header: 'Name', accessor: 'name', className: 'font-medium' },
  { header: 'Contact', accessor: (c) => c.contact_person || '-', className: 'text-muted-foreground' },
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
      contact_person: c.contact_person ?? '',
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
        <div className="grid gap-3">
          <FormField label="Company Name" name="name" value={form.name} onChange={onChange} required />
          <FormField label="Point of Contact" name="contact_person" value={form.contact_person} onChange={onChange} />
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
