import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrders, createWorkOrder, updateWorkOrder, deleteWorkOrder } from '@/api/workOrders';
import { getCustomers } from '@/api/customers';
import { getBatteryProfiles } from '@/api/batteryProfiles';
import type { WorkOrder, WorkOrderIntake } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { SERVICE_TYPES } from '@/lib/constants';

const emptyForm = {
  work_order_number: '',
  customer_id: '',
  part_number: '',
  serial_number: '',
  service_type: 'inspection_test',
  internal_work_number: '',
};

const statusColor = (s: string) => {
  switch (s) {
    case 'received': return 'bg-blue-600';
    case 'in_progress': return 'bg-amber-600';
    case 'completed': return 'bg-green-600';
    default: return 'bg-gray-600';
  }
};

const columns: Column<WorkOrder>[] = [
  { header: 'WO Number', accessor: 'work_order_number', className: 'font-medium' },
  { header: 'Customer', accessor: (wo) => wo.customer_name || '-' },
  { header: 'Service', accessor: (wo) => wo.service_type.replace(/_/g, ' ') },
  {
    header: 'Status',
    accessor: (wo) => (
      <Badge className={`${statusColor(wo.status)} text-white text-xs`}>{wo.status}</Badge>
    ),
  },
  { header: 'Items', accessor: (wo) => String(wo.item_count ?? wo.items?.length ?? 0) },
  {
    header: 'Received',
    accessor: (wo) => new Date(wo.received_date).toLocaleDateString(),
    className: 'text-muted-foreground text-xs',
  },
];

export function AdminWorkOrders() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(
    () => getWorkOrders({ search: search || undefined }),
    [search]
  );
  const { data: customers } = useApiQuery(() => getCustomers(), []);
  const { data: profiles } = useApiQuery(() => getBatteryProfiles(true), []);

  const partNumbers = profiles
    ? [...new Set(profiles.map((p) => p.part_number))]
    : [];

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<WorkOrder | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<WorkOrder | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((wo: WorkOrder) => {
    setEditing(wo);
    const firstItem = wo.items?.[0];
    setForm({
      work_order_number: wo.work_order_number,
      customer_id: String(wo.customer_id),
      part_number: firstItem?.part_number ?? '',
      serial_number: firstItem?.serial_number ?? '',
      service_type: wo.service_type,
      internal_work_number: wo.internal_work_number ?? '',
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
        await updateWorkOrder(editing.id, {
          work_order_number: form.work_order_number,
          customer_id: Number(form.customer_id),
          service_type: form.service_type,
          internal_work_number: form.internal_work_number || undefined,
        });
      } else {
        const intake: WorkOrderIntake = {
          work_order_number: form.work_order_number,
          customer_id: Number(form.customer_id),
          part_number: form.part_number,
          serial_number: form.serial_number,
          service_type: form.service_type,
          internal_work_number: form.internal_work_number || undefined,
        };
        await createWorkOrder(intake);
      }
      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save work order failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, refetch]);

  const handleDelete = useCallback(async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await deleteWorkOrder(deleting.id);
      setDeleting(null);
      refetch();
    } catch (e) {
      console.error('Delete work order failed:', e);
    } finally {
      setDeleteLoading(false);
    }
  }, [deleting, refetch]);

  return (
    <>
      <AdminCrudTable
        title="Work Orders"
        data={data}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search work orders..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Work Order' : 'New Work Order'}
        loading={saving}
      >
        <FormField
          label="Work Order Number"
          name="work_order_number"
          value={form.work_order_number}
          onChange={onChange}
          required
        />

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              Customer<span className="text-red-600 ml-0.5">*</span>
            </Label>
            <Select value={form.customer_id} onValueChange={(v) => onChange('customer_id', v)}>
              <SelectTrigger className="h-8 text-sm w-full">
                <SelectValue placeholder="Select customer" />
              </SelectTrigger>
              <SelectContent>
                {customers?.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.customer_code} — {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              Service Type<span className="text-red-600 ml-0.5">*</span>
            </Label>
            <Select value={form.service_type} onValueChange={(v) => onChange('service_type', v)}>
              <SelectTrigger className="h-8 text-sm w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SERVICE_TYPES.map((st) => (
                  <SelectItem key={st.value} value={st.value}>
                    {st.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-xs font-medium">
            Battery Part Number<span className="text-red-600 ml-0.5">*</span>
          </Label>
          <Select value={form.part_number} onValueChange={(v) => onChange('part_number', v)}>
            <SelectTrigger className="h-8 text-sm w-full">
              <SelectValue placeholder="Select part number" />
            </SelectTrigger>
            <SelectContent>
              {partNumbers.map((pn) => (
                <SelectItem key={pn} value={pn}>
                  {pn}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <FormField
          label="Serial Number"
          name="serial_number"
          value={form.serial_number}
          onChange={onChange}
          required
        />

        <FormField
          label="Internal Work Number"
          name="internal_work_number"
          value={form.internal_work_number}
          onChange={onChange}
          placeholder="Optional"
        />
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Work Order"
        description={`Delete work order "${deleting?.work_order_number}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
