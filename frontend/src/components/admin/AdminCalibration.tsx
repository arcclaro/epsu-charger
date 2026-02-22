import { useState, useCallback } from 'react';
import { useApiQuery } from '@/hooks/useApiQuery';
import {
  getStationCalibrations,
  updateStationCalibration,
  type StationCalibration,
} from '@/api/calibration';
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

function calStatusBadge(status?: string) {
  if (!status) return null;
  const color =
    status === 'valid' ? 'bg-green-600' : status === 'due_soon' ? 'bg-amber-600' : 'bg-red-600';
  return (
    <Badge variant="secondary" className={`${color} text-white text-xs`}>
      {status}
    </Badge>
  );
}

export function AdminCalibration() {
  const { data, isLoading, error, refetch } = useApiQuery(
    () => getStationCalibrations(),
    []
  );
  const [editTarget, setEditTarget] = useState<EditTarget | null>(null);
  const [form, setForm] = useState({ last_cal: '', next_cal: '' });
  const [saving, setSaving] = useState(false);

  const openEdit = useCallback(
    (station: StationCalibration, unit: 'psu' | 'dc_load') => {
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
      await updateStationCalibration(editTarget.stationId, editTarget.unit, {
        last_cal: form.last_cal || null,
        next_cal: form.next_cal || null,
      });
      setEditTarget(null);
      refetch();
    } catch (e) {
      console.error('Update calibration failed:', e);
    } finally {
      setSaving(false);
    }
  }, [editTarget, form, refetch]);

  const onChange = useCallback((name: string, value: string) => {
    setForm((f) => ({ ...f, [name]: value }));
  }, []);

  if (isLoading) return <LoadingSpinner />;
  if (error) return <p className="text-red-400 text-sm">Failed to load calibration data</p>;

  return (
    <>
      <h3 className="text-sm font-semibold mb-3">Station Calibration Dates</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {data?.map((station) => (
          <Card key={station.station_id}>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-sm">Station {station.station_id}</CardTitle>
            </CardHeader>
            <CardContent className="px-3 pb-3 space-y-2">
              {/* PSU */}
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-muted-foreground">PSU Cal:</span>{' '}
                  {station.psu_last_cal
                    ? new Date(station.psu_last_cal).toLocaleDateString()
                    : 'N/A'}
                  {' → '}
                  {station.psu_next_cal
                    ? new Date(station.psu_next_cal).toLocaleDateString()
                    : 'N/A'}
                </div>
                <div className="flex items-center gap-1">
                  {calStatusBadge(station.psu_cal_status)}
                  <Button
                    variant="ghost"
                    size="icon-xs"
                    onClick={() => openEdit(station, 'psu')}
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>
                </div>
              </div>
              {/* DC Load */}
              <div className="flex items-center justify-between text-xs">
                <div>
                  <span className="text-muted-foreground">DC Load Cal:</span>{' '}
                  {station.dc_load_last_cal
                    ? new Date(station.dc_load_last_cal).toLocaleDateString()
                    : 'N/A'}
                  {' → '}
                  {station.dc_load_next_cal
                    ? new Date(station.dc_load_next_cal).toLocaleDateString()
                    : 'N/A'}
                </div>
                <div className="flex items-center gap-1">
                  {calStatusBadge(station.dc_load_cal_status)}
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
        title={editTarget?.label ?? 'Edit Calibration'}
        loading={saving}
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Last Calibration"
            name="last_cal"
            value={form.last_cal}
            onChange={onChange}
            type="date"
          />
          <FormField
            label="Next Calibration"
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
