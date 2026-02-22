import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTechPubs, createTechPub, updateTechPub, deleteTechPub, bulkReplaceApplicability } from '@/api/techPubs';
import type { TechPub, TechPubApplicabilityEntry } from '@/types';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Trash2 } from 'lucide-react';
import { SERVICE_TYPES } from '@/lib/constants';

const SERVICE_TYPE_COLORS: Record<string, string> = {
  inspection_test: 'text-blue-400',
  repair: 'text-amber-400',
  overhaul: 'text-emerald-400',
};

function serviceTypeLabel(value: string): string {
  return SERVICE_TYPES.find((s) => s.value === value)?.label ?? value;
}

const emptyForm = {
  cmm_number: '',
  title: '',
  revision: '',
  revision_date: '',
  ata_chapter: '',
  issued_by: '',
  notes: '',
};

const columns: Column<TechPub>[] = [
  { header: 'CMM Number', accessor: 'cmm_number', className: 'font-mono text-xs' },
  { header: 'Title', accessor: 'title', className: 'font-medium' },
  { header: 'Revision', accessor: (t) => t.revision || '-' },
  { header: 'ATA', accessor: (t) => t.ata_chapter || '-' },
  {
    header: 'Part Numbers',
    accessor: (t) => {
      const entries = t.applicability ?? [];
      const fallback = entries.length === 0
        ? t.applicable_part_numbers.map((p) => ({ part_number: p, service_type: 'inspection_test' }))
        : [];
      const display = entries.length > 0 ? entries : fallback;

      return (
        <div className="flex flex-wrap gap-1">
          {display.slice(0, 3).map((entry, i) => (
            <Badge key={`${entry.part_number}-${entry.service_type}-${i}`} variant="outline" className="text-xs font-mono gap-1">
              {entry.part_number}
              <span className={SERVICE_TYPE_COLORS[entry.service_type] ?? 'text-muted-foreground'}>
                ({serviceTypeLabel(entry.service_type)})
              </span>
            </Badge>
          ))}
          {display.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{display.length - 3}
            </Badge>
          )}
        </div>
      );
    },
  },
];

const ATA_PATTERN = /^\d{2}-\d{2}(-\d{2})?$/;

export function AdminTechPubs() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(() => getTechPubs(), []);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<TechPub | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [applicabilityRows, setApplicabilityRows] = useState<TechPubApplicabilityEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<TechPub | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [ataError, setAtaError] = useState('');

  const filtered = data?.filter(
    (t) =>
      !search ||
      t.cmm_number.toLowerCase().includes(search.toLowerCase()) ||
      t.title.toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setApplicabilityRows([]);
    setAtaError('');
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
      issued_by: t.issued_by ?? t.manufacturer ?? '',
      notes: t.notes ?? '',
    });

    if (t.applicability && t.applicability.length > 0) {
      setApplicabilityRows(t.applicability.map((a) => ({ part_number: a.part_number, service_type: a.service_type })));
    } else if (t.applicable_part_numbers.length > 0) {
      setApplicabilityRows(t.applicable_part_numbers.map((p) => ({ part_number: p, service_type: 'inspection_test' })));
    } else {
      setApplicabilityRows([]);
    }

    setAtaError('');
    setFormOpen(true);
  }, []);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
    if (name === 'ata_chapter') {
      setAtaError('');
    }
  }, []);

  const addApplicabilityRow = useCallback(() => {
    setApplicabilityRows((rows) => [...rows, { part_number: '', service_type: 'inspection_test' }]);
  }, []);

  const removeApplicabilityRow = useCallback((index: number) => {
    setApplicabilityRows((rows) => rows.filter((_, i) => i !== index));
  }, []);

  const updateApplicabilityRow = useCallback((index: number, field: keyof TechPubApplicabilityEntry, value: string) => {
    setApplicabilityRows((rows) =>
      rows.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    );
  }, []);

  const handleSave = useCallback(async () => {
    // Validate ATA chapter format if provided
    if (form.ata_chapter && !ATA_PATTERN.test(form.ata_chapter)) {
      setAtaError('Format must be xx-yy or xx-yy-zz (e.g. 20-40 or 20-40-00)');
      return;
    }

    setSaving(true);
    try {
      const payload = {
        cmm_number: form.cmm_number,
        title: form.title,
        revision: form.revision || undefined,
        revision_date: form.revision_date || undefined,
        ata_chapter: form.ata_chapter || undefined,
        issued_by: form.issued_by || undefined,
        manufacturer: form.issued_by || undefined,
        applicable_part_numbers: applicabilityRows
          .map((r) => r.part_number.trim())
          .filter(Boolean),
        notes: form.notes || undefined,
      };

      let savedId: number;
      if (editing) {
        const result = await updateTechPub(editing.id, payload);
        savedId = result.id;
      } else {
        const result = await createTechPub(payload);
        savedId = result.id;
      }

      // Bulk replace applicability rows
      const validRows = applicabilityRows.filter((r) => r.part_number.trim());
      if (validRows.length > 0) {
        await bulkReplaceApplicability(savedId, validRows.map((r) => ({
          part_number: r.part_number.trim(),
          service_type: r.service_type,
        })));
      } else {
        await bulkReplaceApplicability(savedId, []);
      }

      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save tech pub failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, applicabilityRows, refetch]);

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
        wide
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField label="CMM Number" name="cmm_number" value={form.cmm_number} onChange={onChange} required />
          <FormField label="Title" name="title" value={form.title} onChange={onChange} required className="col-span-2" />
          <FormField label="Revision" name="revision" value={form.revision} onChange={onChange} />
          <FormField label="Revision Date" name="revision_date" value={form.revision_date} onChange={onChange} type="date" />
          <div className="space-y-1.5">
            <FormField label="ATA Chapter" name="ata_chapter" value={form.ata_chapter} onChange={onChange} placeholder="e.g. 20-40-00" />
            {ataError && (
              <p className="text-xs text-red-500">{ataError}</p>
            )}
          </div>
          <FormField label="Manufacturer" name="issued_by" value={form.issued_by} onChange={onChange} />

          {/* Applicability Rows */}
          <div className="col-span-2 space-y-2">
            <Label className="text-xs font-medium">Applicable Part Numbers</Label>
            {applicabilityRows.length > 0 && (
              <div className="space-y-2">
                {applicabilityRows.map((row, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      value={row.part_number}
                      onChange={(e) => updateApplicabilityRow(index, 'part_number', e.target.value)}
                      placeholder="Part number"
                      className="h-8 text-sm font-mono flex-1"
                    />
                    <Select
                      value={row.service_type}
                      onValueChange={(val) => updateApplicabilityRow(index, 'service_type', val)}
                    >
                      <SelectTrigger className="h-8 text-sm w-[180px]">
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
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-red-500"
                      onClick={() => removeApplicabilityRow(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 text-xs"
              onClick={addApplicabilityRow}
            >
              <Plus className="h-3.5 w-3.5 mr-1" />
              Add Part Number
            </Button>
          </div>

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
