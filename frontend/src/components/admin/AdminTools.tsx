import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTools, createTool, updateTool, deleteTool } from '@/api/tools';
import type { Tool } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';

const emptyTool = {
  part_number: '',
  serial_number: '',
  description: '',
  manufacturer: '',
  category: '',
  calibration_date: '',
  valid_until: '',
  calibrated_by: '',
  calibration_certificate: '',
  internal_reference: '',
};

const columns: Column<Tool>[] = [
  { header: 'Part Number', accessor: 'part_number' },
  { header: 'Serial', accessor: 'serial_number', className: 'font-mono text-xs' },
  { header: 'Description', accessor: 'description' },
  { header: 'Category', accessor: 'category' },
  {
    header: 'Cal Valid',
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
      (t.description ?? '').toLowerCase().includes(search.toLowerCase())
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
      description: tool.description ?? '',
      manufacturer: tool.manufacturer ?? '',
      category: tool.category ?? '',
      calibration_date: tool.calibration_date ?? '',
      valid_until: tool.valid_until ?? '',
      calibrated_by: tool.calibrated_by ?? '',
      calibration_certificate: tool.calibration_certificate ?? '',
      internal_reference: tool.internal_reference ?? '',
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
        await updateTool(editing.id, form);
      } else {
        await createTool(form);
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
        title="Calibrated Tools"
        data={filtered ?? null}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search tools..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Tool' : 'New Tool'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Part Number" name="part_number" value={form.part_number} onChange={onChange} required />
          <FormField label="Serial Number" name="serial_number" value={form.serial_number} onChange={onChange} required />
          <FormField label="Description" name="description" value={form.description} onChange={onChange} className="col-span-2" />
          <FormField label="Manufacturer" name="manufacturer" value={form.manufacturer} onChange={onChange} />
          <FormField label="Category" name="category" value={form.category} onChange={onChange} />
          <FormField label="Calibration Date" name="calibration_date" value={form.calibration_date} onChange={onChange} type="date" />
          <FormField label="Valid Until" name="valid_until" value={form.valid_until} onChange={onChange} type="date" />
          <FormField label="Calibrated By" name="calibrated_by" value={form.calibrated_by} onChange={onChange} />
          <FormField label="Certificate" name="calibration_certificate" value={form.calibration_certificate} onChange={onChange} />
          <FormField label="Internal Reference" name="internal_reference" value={form.internal_reference} onChange={onChange} className="col-span-2" />
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Tool"
        description={`Delete tool "${deleting?.part_number} / ${deleting?.serial_number}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
