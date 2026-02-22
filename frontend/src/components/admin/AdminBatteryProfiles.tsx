import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import {
  getBatteryProfiles,
  createBatteryProfile,
  updateBatteryProfile,
  deleteBatteryProfile,
  type BatteryProfile,
} from '@/api/batteryProfiles';
import { AdminCrudTable, type Column } from './AdminCrudTable';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { ConfirmDialog } from './ConfirmDialog';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Separator className="col-span-2 my-1" />
      <p className="col-span-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        {children}
      </p>
    </>
  );
}

function ToggleField({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <Label className="text-xs">{label}</Label>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
}

const emptyForm: Record<string, string | boolean> = {
  part_number: '',
  amendment: '',
  description: '',
  manufacturer: '',
  nominal_voltage_v: '',
  capacity_ah: '',
  num_cells: '',
  chemistry: '',
  std_charge_current_ma: '',
  std_charge_duration_h: '',
  std_charge_voltage_limit_mv: '',
  std_charge_temp_max_c: '',
  cap_test_current_a: '',
  cap_test_voltage_min_mv: '',
  cap_test_duration_min: '',
  cap_test_temp_max_c: '',
  fast_charge_enabled: false,
  fast_charge_current_a: '',
  fast_charge_max_duration_min: '',
  fast_charge_delta_v_mv: '',
  trickle_charge_current_ma: '',
  trickle_charge_voltage_max_mv: '',
  partial_charge_duration_h: '',
  rest_period_age_threshold_months: '',
  rest_period_duration_h: '',
  emergency_temp_max_c: '',
  emergency_temp_min_c: '',
  delta_v_enabled: false,
  fast_discharge_enabled: false,
  notes: '',
};

const columns: Column<BatteryProfile>[] = [
  { header: 'Part Number', accessor: 'part_number', className: 'font-mono text-xs' },
  { header: 'Description', accessor: 'description', className: 'font-medium' },
  { header: 'Manufacturer', accessor: 'manufacturer' },
  { header: 'Chemistry', accessor: 'chemistry' },
  { header: 'Capacity (Ah)', accessor: (p) => String(p.capacity_ah) },
  { header: 'Cells', accessor: (p) => String(p.num_cells) },
];

export function AdminBatteryProfiles() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error, refetch } = useApiQuery(
    () => getBatteryProfiles(),
    []
  );
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<BatteryProfile | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<BatteryProfile | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const filtered = data?.filter(
    (p) =>
      !search ||
      p.part_number.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase()) ||
      p.manufacturer.toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = useCallback(() => {
    setEditing(null);
    setForm(emptyForm);
    setFormOpen(true);
  }, []);

  const openEdit = useCallback((p: BatteryProfile) => {
    setEditing(p);
    const f: Record<string, string | boolean> = {};
    for (const key of Object.keys(emptyForm)) {
      const val = (p as unknown as Record<string, unknown>)[key];
      if (typeof emptyForm[key] === 'boolean') {
        f[key] = !!val;
      } else {
        f[key] = val != null ? String(val) : '';
      }
    }
    setForm(f);
    setFormOpen(true);
  }, []);

  const onStr = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const onBool = useCallback((name: string, value: boolean) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(form)) {
        if (typeof v === 'boolean') {
          payload[k] = v;
        } else if (v === '') {
          // skip empty optional strings
        } else if (
          [
            'nominal_voltage_v', 'capacity_ah', 'num_cells',
            'std_charge_current_ma', 'std_charge_duration_h', 'std_charge_voltage_limit_mv', 'std_charge_temp_max_c',
            'cap_test_current_a', 'cap_test_voltage_min_mv', 'cap_test_duration_min', 'cap_test_temp_max_c',
            'fast_charge_current_a', 'fast_charge_max_duration_min', 'fast_charge_delta_v_mv',
            'trickle_charge_current_ma', 'trickle_charge_voltage_max_mv', 'partial_charge_duration_h',
            'rest_period_age_threshold_months', 'rest_period_duration_h',
            'emergency_temp_max_c', 'emergency_temp_min_c',
          ].includes(k)
        ) {
          payload[k] = Number(v);
        } else {
          payload[k] = v;
        }
      }
      if (editing) {
        await updateBatteryProfile(editing.id, payload);
      } else {
        await createBatteryProfile(payload);
      }
      setFormOpen(false);
      refetch();
    } catch (e) {
      console.error('Save battery profile failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editing, form, refetch]);

  const handleDelete = useCallback(async () => {
    if (!deleting) return;
    setDeleteLoading(true);
    try {
      await deleteBatteryProfile(deleting.id);
      setDeleting(null);
      refetch();
    } catch (e) {
      console.error('Delete battery profile failed:', e);
    } finally {
      setDeleteLoading(false);
    }
  }, [deleting, refetch]);

  const s = (name: string) => form[name] as string;
  const b = (name: string) => form[name] as boolean;

  return (
    <>
      <AdminCrudTable
        title="Battery Profiles"
        data={filtered ?? null}
        columns={columns}
        isLoading={isLoading}
        error={error}
        onAdd={openCreate}
        onEdit={openEdit}
        onDelete={setDeleting}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search profiles..."
      />

      <FormDialog
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleSave}
        title={editing ? 'Edit Battery Profile' : 'New Battery Profile'}
        loading={saving}
        wide
      >
        <div className="grid grid-cols-2 gap-3">
          {/* Basic Info */}
          <p className="col-span-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Basic Information
          </p>
          <FormField label="Part Number" name="part_number" value={s('part_number')} onChange={onStr} required />
          <FormField label="Amendment" name="amendment" value={s('amendment')} onChange={onStr} />
          <FormField label="Description" name="description" value={s('description')} onChange={onStr} required className="col-span-2" />
          <FormField label="Manufacturer" name="manufacturer" value={s('manufacturer')} onChange={onStr} required />
          <FormField label="Chemistry" name="chemistry" value={s('chemistry')} onChange={onStr} required placeholder="NiCd, NiMH, Li-Ion" />

          {/* Electrical */}
          <SectionLabel>Electrical</SectionLabel>
          <FormField label="Nominal Voltage (V)" name="nominal_voltage_v" value={s('nominal_voltage_v')} onChange={onStr} type="number" required />
          <FormField label="Capacity (Ah)" name="capacity_ah" value={s('capacity_ah')} onChange={onStr} type="number" required />
          <FormField label="Number of Cells" name="num_cells" value={s('num_cells')} onChange={onStr} type="number" required />

          {/* Standard Charge */}
          <SectionLabel>Standard Charge</SectionLabel>
          <FormField label="Charge Current (mA)" name="std_charge_current_ma" value={s('std_charge_current_ma')} onChange={onStr} type="number" />
          <FormField label="Charge Duration (h)" name="std_charge_duration_h" value={s('std_charge_duration_h')} onChange={onStr} type="number" />
          <FormField label="Voltage Limit (mV)" name="std_charge_voltage_limit_mv" value={s('std_charge_voltage_limit_mv')} onChange={onStr} type="number" />
          <FormField label="Temp Max (C)" name="std_charge_temp_max_c" value={s('std_charge_temp_max_c')} onChange={onStr} type="number" />

          {/* Capacity Test */}
          <SectionLabel>Capacity Test</SectionLabel>
          <FormField label="Test Current (A)" name="cap_test_current_a" value={s('cap_test_current_a')} onChange={onStr} type="number" />
          <FormField label="Voltage Min (mV)" name="cap_test_voltage_min_mv" value={s('cap_test_voltage_min_mv')} onChange={onStr} type="number" />
          <FormField label="Duration (min)" name="cap_test_duration_min" value={s('cap_test_duration_min')} onChange={onStr} type="number" />
          <FormField label="Temp Max (C)" name="cap_test_temp_max_c" value={s('cap_test_temp_max_c')} onChange={onStr} type="number" />

          {/* Fast Charge */}
          <SectionLabel>Fast Charge</SectionLabel>
          <ToggleField label="Fast Charge Enabled" checked={b('fast_charge_enabled')} onChange={(v) => onBool('fast_charge_enabled', v)} />
          <ToggleField label="Delta-V Enabled" checked={b('delta_v_enabled')} onChange={(v) => onBool('delta_v_enabled', v)} />
          <FormField label="Fast Charge Current (A)" name="fast_charge_current_a" value={s('fast_charge_current_a')} onChange={onStr} type="number" />
          <FormField label="Max Duration (min)" name="fast_charge_max_duration_min" value={s('fast_charge_max_duration_min')} onChange={onStr} type="number" />
          <FormField label="Delta-V (mV)" name="fast_charge_delta_v_mv" value={s('fast_charge_delta_v_mv')} onChange={onStr} type="number" />
          <FormField label="Trickle Current (mA)" name="trickle_charge_current_ma" value={s('trickle_charge_current_ma')} onChange={onStr} type="number" />
          <FormField label="Trickle Voltage Max (mV)" name="trickle_charge_voltage_max_mv" value={s('trickle_charge_voltage_max_mv')} onChange={onStr} type="number" />
          <FormField label="Partial Charge Duration (h)" name="partial_charge_duration_h" value={s('partial_charge_duration_h')} onChange={onStr} type="number" />

          {/* Safety / Rest */}
          <SectionLabel>Safety & Rest</SectionLabel>
          <ToggleField label="Fast Discharge Enabled" checked={b('fast_discharge_enabled')} onChange={(v) => onBool('fast_discharge_enabled', v)} />
          <div />
          <FormField label="Rest Age Threshold (months)" name="rest_period_age_threshold_months" value={s('rest_period_age_threshold_months')} onChange={onStr} type="number" />
          <FormField label="Rest Duration (h)" name="rest_period_duration_h" value={s('rest_period_duration_h')} onChange={onStr} type="number" />
          <FormField label="Emergency Temp Max (C)" name="emergency_temp_max_c" value={s('emergency_temp_max_c')} onChange={onStr} type="number" />
          <FormField label="Emergency Temp Min (C)" name="emergency_temp_min_c" value={s('emergency_temp_min_c')} onChange={onStr} type="number" />

          {/* Notes */}
          <SectionLabel>Notes</SectionLabel>
          <FormField label="Notes" name="notes" value={s('notes')} onChange={onStr} textarea className="col-span-2" />
        </div>
      </FormDialog>

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        title="Delete Battery Profile"
        description={`Delete profile "${deleting?.part_number} — ${deleting?.description}"? This cannot be undone.`}
        loading={deleteLoading}
      />
    </>
  );
}
