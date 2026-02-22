import { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrders, createWorkOrder, updateWorkOrder, deleteWorkOrder } from '@/api/workOrders';
import { getCustomers } from '@/api/customers';
import { getBatteryProfiles } from '@/api/batteryProfiles';
import { FormDialog } from '@/components/admin/FormDialog';
import { FormField } from '@/components/admin/FormField';
import { ConfirmDialog } from '@/components/admin/ConfirmDialog';
import { SERVICE_TYPES } from '@/lib/constants';
import type { WorkOrder, WorkOrderIntake } from '@/types';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Search, MoreHorizontal, Plus, Pencil, Trash2 } from 'lucide-react';

type StatusFilter = 'all' | 'open' | 'closed';

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
    case 'closed': return 'bg-gray-600';
    default: return 'bg-gray-600';
  }
};

export default function WorkOrderList() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('open');
  const [search, setSearch] = useState('');

  const { data, isLoading, error, refetch } = useApiQuery(
    () =>
      getWorkOrders({
        status: statusFilter === 'all' ? undefined : statusFilter,
        search: search || undefined,
      }),
    [statusFilter, search],
  );

  const { data: customers } = useApiQuery(() => getCustomers(), []);
  const { data: profiles } = useApiQuery(() => getBatteryProfiles(true), []);

  // Deduplicate part numbers from profiles
  const partNumbers = profiles
    ? [...new Set(profiles.map((p) => p.part_number))]
    : [];

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<WorkOrder | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<WorkOrder | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

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

  const filterButtons: { label: string; value: StatusFilter }[] = [
    { label: 'All', value: 'all' },
    { label: 'Open', value: 'open' },
    { label: 'Closed', value: 'closed' },
  ];

  return (
    <div>
      <PageHeader title="Work Orders" description="Customer service orders" />

      {/* Toolbar: status filter, search, new button */}
      <div className="flex items-center gap-3 mb-4 flex-wrap">
        <div className="flex rounded-md border overflow-hidden">
          {filterButtons.map((fb) => (
            <button
              key={fb.value}
              onClick={() => setStatusFilter(fb.value)}
              className={`px-3 py-1.5 text-sm font-medium transition-colors ${
                statusFilter === fb.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-background text-muted-foreground hover:bg-accent'
              }`}
            >
              {fb.label}
            </button>
          ))}
        </div>

        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search work orders..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Button onClick={openCreate} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          New Work Order
        </Button>
      </div>

      {/* Table */}
      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <p className="text-red-600">Failed to load work orders</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>WO Number</TableHead>
                <TableHead>Customer</TableHead>
                <TableHead>Battery PN</TableHead>
                <TableHead>Serial</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map((wo) => {
                const firstItem = wo.items?.[0];
                return (
                  <TableRow key={wo.id} className="hover:bg-accent/50">
                    <TableCell>
                      <Link
                        to={`/work-orders/${wo.id}`}
                        className="text-blue-600 hover:underline font-medium"
                      >
                        {wo.work_order_number}
                      </Link>
                    </TableCell>
                    <TableCell>{wo.customer_name || '-'}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {firstItem?.part_number || '-'}
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {firstItem?.serial_number || '-'}
                    </TableCell>
                    <TableCell>
                      {wo.service_type.replace(/_/g, ' ')}
                    </TableCell>
                    <TableCell>
                      <Badge className={`${statusColor(wo.status)} text-white text-xs`}>
                        {wo.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-xs">
                      {new Date(wo.received_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-7 w-7">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEdit(wo)}>
                            <Pencil className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            variant="destructive"
                            onClick={() => setDeleting(wo)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
              {data?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="text-center text-muted-foreground">
                    No work orders found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Create / Edit dialog */}
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

        <div className="space-y-1.5">
          <Label className="text-xs font-medium">
            Customer<span className="text-red-600 ml-0.5">*</span>
          </Label>
          <Select
            value={form.customer_id}
            onValueChange={(v) => onChange('customer_id', v)}
          >
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
            Battery Part Number<span className="text-red-600 ml-0.5">*</span>
          </Label>
          <Select
            value={form.part_number}
            onValueChange={(v) => onChange('part_number', v)}
          >
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

        <div className="space-y-1.5">
          <Label className="text-xs font-medium">
            Service Type<span className="text-red-600 ml-0.5">*</span>
          </Label>
          <Select
            value={form.service_type}
            onValueChange={(v) => onChange('service_type', v)}
          >
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

        <FormField
          label="Internal Work Number"
          name="internal_work_number"
          value={form.internal_work_number}
          onChange={onChange}
          placeholder="Optional"
        />
      </FormDialog>

      {/* Delete confirmation */}
      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Work Order"
        description={`Delete work order "${deleting?.work_order_number}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </div>
  );
}
