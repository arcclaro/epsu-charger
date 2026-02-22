import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTools, createTool, updateTool, deleteTool } from '@/api/tools';
import type { Tool } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const emptyTool = {
  part_number: '',
  serial_number: '',
  manufacturer: '',
  tool_id_display: '',
  verification_date: '',
  verification_cycle_days: '180',
  tcp_ip_address: '',
  designated_station: '',
};

const columns: Column<Tool>[] = [
  { header: 'TID', accessor: 'tool_id_display' },
  { header: 'Manufacturer', accessor: 'manufacturer' },
  { header: 'Model', accessor: 'part_number' },
  { header: 'Serial', accessor: 'serial_number', className: 'font-mono text-xs' },
  { header: 'Station', accessor: (t) => (t.designated_station != null ? String(t.designated_station) : '-') },
  { header: 'IP', accessor: 'tcp_ip_address', className: 'font-mono text-xs' },
  {
    header: 'Verification Valid',
    accessor: (t) =>
      t.valid_until ? (
        <Badge
          variant="secondary"
          className={`text-xs text-white ${
            new Date(t.valid_until) > new Date() ? 'bg-green-600' : 'bg-red-600'
          }`}
        >
          {new Date(t.valid_until).toLocaleDateString()}
        </Badge>
      ) : (
        '-'
      ),
  },
];

const stationOptions = Array.from({ length: 12 }, (_, i) => i + 1);

export function AdminTools() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(() => getTools(), []);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Tool | null>(null);
  const [form, setForm] = useState(emptyTool);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<Tool | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const filtered = data?.filter(
    (t) =>
      !search ||
      t.part_number.toLowerCase().includes(search.toLowerCase()) ||
      t.serial_number.toLowerCase().includes(search.toLowerCase()) ||
      (t.manufacturer ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (t.tool_id_display ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyTool);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((tool: Tool) => {
    setEditing(tool);
    setForm({
      part_number: tool.part_number,
      serial_number: tool.serial_number,
      manufacturer: tool.manufacturer ?? '',
      tool_id_display: tool.tool_id_display ?? '',
      verification_date: tool.verification_date ?? '',
      verification_cycle_days: tool.verification_cycle_days != null ? String(tool.verification_cycle_days) : '180',
      tcp_ip_address: tool.tcp_ip_address ?? '',
      designated_station: tool.designated_station != null ? String(tool.designated_station) : '',
    });
    setFormOpen(true);
  }, []);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        part_number: form.part_number,
        serial_number: form.serial_number,
        manufacturer: form.manufacturer,
        tool_id_display: form.tool_id_display,
        verification_date: form.verification_date || null,
        verification_cycle_days: form.verification_cycle_days ? Number(form.verification_cycle_days) : null,
        tcp_ip_address: form.tcp_ip_address || null,
        designated_station: form.designated_station ? Number(form.designated_station) : null,
      };

      if (editing) {
        await updateTool(editing.id, payload);
      } else {
        await createTool(payload);
      }
      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save tool failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, refetch]);

  const handleDelete = useCallback(async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await deleteTool(deleting.id);
      setDeleting(null);
      refetch();
    } catch (e) {
      console.error('Delete tool failed:', e);
    } finally {
      setDeleteLoading(false);
    }
  }, [deleting, refetch]);

  return (
    <>
      <AdminCrudTable
        title="Station Equipment"
        data={filtered ?? null}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search equipment..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Equipment' : 'New Equipment'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Manufacturer" name="manufacturer" value={form.manufacturer} onChange={onChange} />
          <FormField label="Part Number / Model" name="part_number" value={form.part_number} onChange={onChange} required />
          <FormField label="Serial Number" name="serial_number" value={form.serial_number} onChange={onChange} required />
          <FormField label="TID Reference" name="tool_id_display" value={form.tool_id_display} onChange={onChange} placeholder="TIDxxx" />
          <FormField label="Verification Date" name="verification_date" value={form.verification_date} onChange={onChange} type="date" />
          <FormField label="Verification Cycle (days)" name="verification_cycle_days" value={form.verification_cycle_days} onChange={onChange} type="number" />
          <FormField label="TCP/IP Address" name="tcp_ip_address" value={form.tcp_ip_address} onChange={onChange} placeholder="192.168.x.x" />
          <div className="space-y-1">
            <Label>Designated Station</Label>
            <Select
              value={form.designated_station}
              onValueChange={(value) => onChange('designated_station', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select station" />
              </SelectTrigger>
              <SelectContent>
                {stationOptions.map((n) => (
                  <SelectItem key={n} value={String(n)}>
                    Station {n}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Equipment"
        description={`Delete "${deleting?.tool_id_display || deleting?.part_number} / ${deleting?.serial_number}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
