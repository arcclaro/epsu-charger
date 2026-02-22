import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import {
  getStationVerifications,
  updateStationVerification,
  type StationVerification,
} from '@/api/verification';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FormDialog } from './FormDialog';
import { FormField } from './FormField';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { Pencil } from 'lucide-react';

type EditTarget = {
  stationId: number;
  unit: 'psu' | 'dc_load';
  label: string;
  lastCal: string;
  nextCal: string;
};

function verificationStatusBadge(status?: string) {
  if (!status) return null;
  const color =
    status === 'valid' ? 'bg-green-600' : status === 'due_soon' ? 'bg-amber-600' : 'bg-red-600';
  return (
    <Badge variant="secondary" className={`${color} text-white text-xs`}>
      {status}
    </Badge>
  );
}

export function AdminVerification() {
  const { data, isLoading, error, refetch } = useApiQuery(
    () => getStationVerifications(),
    []
  );
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [form, setForm] = useState({ last_cal: '', next_cal: '' });
  const [saving, setSaving] = useState(false);

  const openEdit = useCallback(
    (station: StationVerification, unit: 'psu' | 'dc_load') => {
      const label = `Station ${station.station_id} — ${unit === 'psu' ? 'PSU' : 'DC Load'}`;
      setEditTarget({
        stationId: station.station_id,
        unit,
        label,
        lastCal:
          unit === 'psu'
            ? station.psu_last_cal ?? ''
            : station.dc_load_last_cal ?? '',
        nextCal:
          unit === 'psu'
            ? station.psu_next_cal ?? ''
            : station.dc_load_next_cal ?? '',
      });
      setForm({
        last_cal:
          unit === 'psu'
            ? station.psu_last_cal ?? ''
            : station.dc_load_last_cal ?? '',
        next_cal:
          unit === 'psu'
            ? station.psu_next_cal ?? ''
            : station.dc_load_next_cal ?? '',
      });
    },
    []
  );

  const handleSave = useCallback(async () => {
    if (!editTarget) return;
    setSaving(true);
    try {
      await updateStationVerification(editTarget.stationId, editTarget.unit, {
        last_cal: form.last_cal || null,
        next_cal: form.next_cal || null,
      });
      setEditTarget(null);
      refetch();
    } catch (e) {
      console.error('Update verification failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editTarget, form, refetch]);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <p className="text-red-600 text-sm">Failed to load verification data</p>;

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold">Station Verification Dates</h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => alert('Procedure not yet implemented')}
        >
          Start Automated Verification
        </Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {data?.map((station) => (
          <Card key={station.station_id}>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-sm">Station {station.station_id}</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* PSU Verification */}
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-muted-foreground">PSU Verification:</span>{' '}
                  {station.psu_last_cal
                    ? new Date(station.psu_last_cal).toLocaleDateString()
                    : 'N/A'}
                  {' → '}
                  {station.psu_next_cal
                    ? new Date(station.psu_next_cal).toLocaleDateString()
                    : 'N/A'}
                </div>
                <div className="flex items-center gap-1">
                  {verificationStatusBadge(station.psu_cal_status)}
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => openEdit(station, 'psu')}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              {/* DC Load Verification */}
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-muted-foreground">DC Load Verification:</span>{' '}
                  {station.dc_load_last_cal
                    ? new Date(station.dc_load_last_cal).toLocaleDateString()
                    : 'N/A'}
                  {' → '}
                  {station.dc_load_next_cal
                    ? new Date(station.dc_load_next_cal).toLocaleDateString()
                    : 'N/A'}
                </div>
                <div className="flex items-center gap-1">
                  {verificationStatusBadge(station.dc_load_cal_status)}
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => openEdit(station, 'dc_load')}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {data?.length === 0 && (
          <p className="text-muted-foreground text-sm col-span-2">No stations found</p>
        )}
      </div>

      <FormDialog
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        onSubmit={handleSave}
        title={editTarget?.label ?? 'Edit Verification'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Last Verification"
            name="last_cal"
            value={form.last_cal}
            onChange={onChange}
            type="date"
          />
          <FormField
            label="Next Verification"
            name="next_cal"
            value={form.next_cal}
            onChange={onChange}
            type="date"
          />
        </div>
      </FormDialog>
    </>
  );
}
