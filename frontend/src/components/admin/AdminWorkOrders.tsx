import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrders, createWorkOrder, updateWorkOrder, deleteWorkOrder } from '@/api/workOrders';
import { getCustomers } from '@/api/customers';
import type { WorkOrder, WorkOrderIntake } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Plus, Trash2 } from 'lucide-react';

interface BatteryRow {
  serial_number: string;
  part_number: string;
  revision: string;
  amendment: string;
  reported_condition: string;
}

const emptyBattery: BatteryRow = {
  serial_number: '',
  part_number: '',
  revision: '',
  amendment: '',
  reported_condition: '',
};

const emptyForm = {
  customer_id: '',
  customer_reference: '',
  service_type: 'overhaul',
  customer_notes: '',
};

const serviceTypes = ['overhaul', 'inspection', 'repair', 'capacity_test', 'initial_acceptance'];

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

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<WorkOrder | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [batteries, setBatteries] = useState<BatteryRow[]>([{ ...emptyBattery }]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<WorkOrder | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setBatteries([{ ...emptyBattery }]);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((wo: WorkOrder) => {
    setEditing(wo);
    setForm({
      customer_id: String(wo.customer_id),
      customer_reference: wo.customer_reference ?? '',
      service_type: wo.service_type,
      customer_notes: wo.customer_notes ?? '',
    });
    setBatteries(
      wo.items?.map((i) => ({
        serial_number: i.serial_number,
        part_number: i.part_number,
        revision: i.revision,
        amendment: i.amendment ?? '',
        reported_condition: i.reported_condition ?? '',
      })) ?? [{ ...emptyBattery }]
    );
    setFormOpen(true);
  }, []);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const updateBattery = useCallback((idx: number, field: keyof BatteryRow, value: string) => {
    setBatteries((prev) => prev.map((b, i) => (i === idx ? { ...b, [field]: value } : b)));
  }, []);

  const addBattery = useCallback(() => {
    setBatteries((prev) => [...prev, { ...emptyBattery }]);
  }, []);

  const removeBattery = useCallback((idx: number) => {
    setBatteries((prev) => (prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      if (editing) {
        await updateWorkOrder(editing.id, {
          customer_id: Number(form.customer_id),
          customer_reference: form.customer_reference || undefined,
          service_type: form.service_type,
          customer_notes: form.customer_notes || undefined,
        });
      } else {
        const intake: WorkOrderIntake = {
          customer_id: Number(form.customer_id),
          customer_reference: form.customer_reference || undefined,
          service_type: form.service_type,
          customer_notes: form.customer_notes || undefined,
          batteries: batteries
            .filter((b) => b.serial_number && b.part_number)
            .map((b) => ({
              serial_number: b.serial_number,
              part_number: b.part_number,
              revision: b.revision || 'A',
              amendment: b.amendment || undefined,
              reported_condition: b.reported_condition || undefined,
            })),
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
  }, [editing, form, batteries, refetch]);

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
        wide
      >
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-xs font-medium">
              Customer<span className="text-red-400 ml-0.5">*</span>
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
            <Label className="text-xs font-medium">Service Type</Label>
            <Select value={form.service_type} onValueChange={(v) => onChange('service_type', v)}>
              <SelectTrigger className="h-8 text-sm w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {serviceTypes.map((s) => (
                  <SelectItem key={s} value={s}>
                    {s.replace(/_/g, ' ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <FormField label="Customer Reference" name="customer_reference" value={form.customer_reference} onChange={onChange} />
          <FormField label="Customer Notes" name="customer_notes" value={form.customer_notes} onChange={onChange} textarea className="col-span-2" />
        </div>

        {!editing && (
          <>
            <Separator className="my-3" />
            <div className="flex items-center justify-between mb-2">
              <Label className="text-xs font-semibold">Battery Items</Label>
              <Button type="button" variant="outline" size="xs" onClick={addBattery}>
                <Plus className="h-3 w-3 mr-1" />
                Add Row
              </Button>
            </div>
            <div className="space-y-2">
              {batteries.map((b, idx) => (
                <div key={idx} className="grid grid-cols-[1fr_1fr_0.5fr_0.5fr_1fr_auto] gap-2 items-end">
                  <div className="space-y-1">
                    {idx === 0 && <Label className="text-xs text-muted-foreground">Serial</Label>}
                    <Input
                      className="h-7 text-xs"
                      value={b.serial_number}
                      onChange={(e) => updateBattery(idx, 'serial_number', e.target.value)}
                      placeholder="Serial"
                    />
                  </div>
                  <div className="space-y-1">
                    {idx === 0 && <Label className="text-xs text-muted-foreground">Part Number</Label>}
                    <Input
                      className="h-7 text-xs"
                      value={b.part_number}
                      onChange={(e) => updateBattery(idx, 'part_number', e.target.value)}
                      placeholder="Part #"
                    />
                  </div>
                  <div className="space-y-1">
                    {idx === 0 && <Label className="text-xs text-muted-foreground">Rev</Label>}
                    <Input
                      className="h-7 text-xs"
                      value={b.revision}
                      onChange={(e) => updateBattery(idx, 'revision', e.target.value)}
                      placeholder="A"
                    />
                  </div>
                  <div className="space-y-1">
                    {idx === 0 && <Label className="text-xs text-muted-foreground">Amend</Label>}
                    <Input
                      className="h-7 text-xs"
                      value={b.amendment}
                      onChange={(e) => updateBattery(idx, 'amendment', e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    {idx === 0 && <Label className="text-xs text-muted-foreground">Condition</Label>}
                    <Input
                      className="h-7 text-xs"
                      value={b.reported_condition}
                      onChange={(e) => updateBattery(idx, 'reported_condition', e.target.value)}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => removeBattery(idx)}
                    disabled={batteries.length <= 1}
                    className="mb-0.5"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </>
        )}
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
