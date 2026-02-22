import { useParams, Link } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { useStations } from '@/hooks/useStations';
import { PageHeader } from '@/components/common/PageHeader';
import { StationStateBadge } from '@/components/common/StatusBadge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { formatVoltage, formatCurrent, formatTemp, formatDuration } from '@/lib/formatters';
import { PHASE_LABELS } from '@/lib/constants';
import { sendControl, stopStation } from '@/api/stations';
import { AlertTriangle, Play, Square, Zap, Wrench } from 'lucide-react';

const StationChart = lazy(() => import('@/components/station/StationChart'));

export default function StationDetail() {
  const { id } = useParams<{ id: string }>();
  const stationId = Number(id);
  const { stations, awaitingTasks } = useStations();
  const station = stations.find(s => s.station_id === stationId);
  const awaiting = awaitingTasks.get(stationId);

  if (!station) {
    return (
      <div>
        <PageHeader title={`Station ${stationId}`} />
        <p className="text-muted-foreground">Waiting for station data...</p>
      </div>
    );
  }

  const s = station;

  return (
    <div>
      <PageHeader
        title={`Station ${stationId}`}
        actions={<StationStateBadge state={s.state} />}
      />

      {awaiting && (
        <div className="mb-4 p-3 rounded-md bg-amber-500/10 border border-amber-500/30 flex items-center gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-amber-400 font-medium">Task awaiting input</p>
            <p className="text-xs text-muted-foreground truncate">{awaiting.label}</p>
          </div>
          <Button size="sm" variant="outline" asChild>
            <Link to={`/jobs/${s.work_job_id}/tasks/${awaiting.id}`}>Enter Data</Link>
          </Button>
        </div>
      )}

      <div className="grid grid-cols-4 gap-3 mb-4">
        <Card>
          <CardHeader className="py-2 px-3"><CardTitle className="text-xs text-muted-foreground">Voltage</CardTitle></CardHeader>
          <CardContent className="px-3 pb-3">
            <p className="text-xl font-mono">{formatVoltage(s.voltage_mv)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="py-2 px-3"><CardTitle className="text-xs text-muted-foreground">Current</CardTitle></CardHeader>
          <CardContent className="px-3 pb-3">
            <p className="text-xl font-mono">{formatCurrent(s.current_ma)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="py-2 px-3"><CardTitle className="text-xs text-muted-foreground">Temperature</CardTitle></CardHeader>
          <CardContent className="px-3 pb-3">
            <p className="text-xl font-mono">{s.temperature_valid ? formatTemp(s.temperature_c) : '--'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="py-2 px-3"><CardTitle className="text-xs text-muted-foreground">Elapsed</CardTitle></CardHeader>
          <CardContent className="px-3 pb-3">
            <p className="text-xl font-mono">{formatDuration(s.elapsed_time_s)}</p>
          </CardContent>
        </Card>
      </div>

      {s.state === 'running' && (
        <Card className="mb-4">
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-xs text-muted-foreground">Test Progress</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3 space-y-1">
            <p className="text-sm">{PHASE_LABELS[s.test_phase] ?? s.test_phase}</p>
            {s.current_task_label && <p className="text-xs text-blue-600">{s.current_task_label}</p>}
            {s.work_job_id && (
              <Link to={`/jobs/${s.work_job_id}`} className="text-xs text-blue-600 hover:underline">
                View Job Progress →
              </Link>
            )}
          </CardContent>
        </Card>
      )}

      {s.battery_config && (
        <Card className="mb-4">
          <CardHeader className="py-2 px-3">
            <CardTitle className="text-xs text-muted-foreground">Battery</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3 text-sm space-y-1">
            <p><span className="text-muted-foreground">P/N:</span> {s.battery_config.part_number}</p>
            <p><span className="text-muted-foreground">S/N:</span> {s.battery_config.serial_number}</p>
            {s.battery_config.amendment && (
              <p><span className="text-muted-foreground">Amendment:</span> {s.battery_config.amendment}</p>
            )}
          </CardContent>
        </Card>
      )}

      <Suspense fallback={<Skeleton className="h-64 w-full" />}>
        <StationChart stationId={stationId} />
      </Suspense>

      <Card className="mt-4">
        <CardHeader className="py-2 px-3">
          <CardTitle className="text-xs text-muted-foreground">Manual Controls</CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3 flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => sendControl({ station_id: stationId, command: 'charge' })}
            disabled={s.state === 'running'}
          >
            <Zap className="h-3 w-3 mr-1" />Charge
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => sendControl({ station_id: stationId, command: 'discharge' })}
            disabled={s.state === 'running'}
          >
            <Play className="h-3 w-3 mr-1" />Discharge
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => stopStation(stationId)}
            disabled={s.state !== 'running'}
          >
            <Square className="h-3 w-3 mr-1" />Stop
          </Button>
          {(s.state === 'empty' || s.state === 'ready') && (
            <Button size="sm" variant="outline" asChild>
              <Link to={`/station/${stationId}/test`}>
                <Wrench className="h-3 w-3 mr-1" />Test Equipment
              </Link>
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
