import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTechPubs, createTechPub, updateTechPub, deleteTechPub } from '@/api/techPubs';
import type { TechPub } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';

const emptyForm = {
  cmm_number: '',
  title: '',
  revision: '',
  revision_date: '',
  ata_chapter: '',
  issued_by: '',
  applicable_part_numbers_csv: '',
  notes: '',
};

const columns: Column<TechPub>[] = [
  { header: 'CMM Number', accessor: 'cmm_number', className: 'font-mono text-xs' },
  { header: 'Title', accessor: 'title', className: 'font-medium' },
  { header: 'Revision', accessor: (t) => t.revision || '-' },
  { header: 'ATA', accessor: (t) => t.ata_chapter || '-' },
  {
    header: 'Part Numbers',
    accessor: (t) => (
      <div className="flex flex-wrap gap-1">
        {t.applicable_part_numbers.slice(0, 3).map((p) => (
          <Badge key={p} variant="outline" className="text-xs font-mono">
            {p}
          </Badge>
        ))}
        {t.applicable_part_numbers.length > 3 && (
          <Badge variant="secondary" className="text-xs">
            +{t.applicable_part_numbers.length - 3}
          </Badge>
        )}
      </div>
    ),
  },
];

export function AdminTechPubs() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(() => getTechPubs(), []);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<TechPub | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<TechPub | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const filtered = data?.filter(
    (t) =>
      !search ||
      t.cmm_number.toLowerCase().includes(search.toLowerCase()) ||
      t.title.toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((t: TechPub) => {
    setEditing(t);
    setForm({
      cmm_number: t.cmm_number,
      title: t.title,
      revision: t.revision ?? '',
      revision_date: t.revision_date ?? '',
      ata_chapter: t.ata_chapter ?? '',
      issued_by: t.issued_by ?? '',
      applicable_part_numbers_csv: t.applicable_part_numbers.join(', '),
      notes: t.notes ?? '',
    });
    setFormOpen(true);
  }, []);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const payload = {
        cmm_number: form.cmm_number,
        title: form.title,
        revision: form.revision || undefined,
        revision_date: form.revision_date || undefined,
        ata_chapter: form.ata_chapter || undefined,
        issued_by: form.issued_by || undefined,
        applicable_part_numbers: form.applicable_part_numbers_csv
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        notes: form.notes || undefined,
      };
      if (editing) {
        await updateTechPub(editing.id, payload);
      } else {
        await createTechPub(payload);
      }
      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save tech pub failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, refetch]);

  const handleDelete = useCallback(async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await deleteTechPub(deleting.id);
      setDeleting(null);
      refetch();
    } catch (e) {
      console.error('Delete tech pub failed:', e);
    } finally {
      setDeleteLoading(false);
    }
  }, [deleting, refetch]);

  return (
    <>
      <AdminCrudTable
        title="CMM Documents"
        data={filtered ?? null}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search tech pubs..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Tech Pub' : 'New Tech Pub'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField label="CMM Number" name="cmm_number" value={form.cmm_number} onChange={onChange} required />
          <FormField label="Title" name="title" value={form.title} onChange={onChange} required className="col-span-2" />
          <FormField label="Revision" name="revision" value={form.revision} onChange={onChange} />
          <FormField label="Revision Date" name="revision_date" value={form.revision_date} onChange={onChange} type="date" />
          <FormField label="ATA Chapter" name="ata_chapter" value={form.ata_chapter} onChange={onChange} />
          <FormField label="Issued By" name="issued_by" value={form.issued_by} onChange={onChange} />
          <FormField
            label="Applicable Part Numbers (comma-separated)"
            name="applicable_part_numbers_csv"
            value={form.applicable_part_numbers_csv}
            onChange={onChange}
            className="col-span-2"
            placeholder="e.g. 015797-002, 015797-003"
          />
          <FormField label="Notes" name="notes" value={form.notes} onChange={onChange} textarea className="col-span-2" />
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Tech Pub"
        description={`Delete "${deleting?.cmm_number} — ${deleting?.title}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
