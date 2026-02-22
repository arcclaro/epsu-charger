import { memo } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { StationStateBadge } from '@/components/common/StatusBadge';
import { formatVoltage, formatCurrent, formatTemp, formatDuration } from '@/lib/formatters';
import { PHASE_LABELS } from '@/lib/constants';
import type { StationStatus } from '@/types';

interface Props {
  station: StationStatus;
  hasAwaitingTask?: boolean;
}

export const StationCard = memo(function StationCard({ station, hasAwaitingTask }: Props) {
  const s = station;
  return (
    <Link to={`/station/${s.station_id}`}>
      <Card className={`transition-colors duration-150 hover:border-primary/50 ${hasAwaitingTask ? 'border-amber-500/60 ring-1 ring-amber-500/30' : ''}`}>
        <CardContent className="p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">Stn {s.station_id}</span>
            <StationStateBadge state={s.state} />
          </div>

          {s.battery_config && (
            <p className="text-xs font-mono text-muted-foreground truncate">
              {s.battery_config.part_number}
            </p>
          )}

          {s.state !== 'empty' && (
            <div className="grid grid-cols-3 gap-1 text-xs">
              <div>
                <p className="text-muted-foreground">V</p>
                <p className="font-mono">{formatVoltage(s.voltage_mv)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">I</p>
                <p className="font-mono">{formatCurrent(s.current_ma)}</p>
              </div>
              <div>
                <p className="text-muted-foreground">T</p>
                <p className="font-mono">{s.temperature_valid ? formatTemp(s.temperature_c) : '--'}</p>
              </div>
            </div>
          )}

          {s.state === 'running' && (
            <>
              <p className="text-[10px] text-muted-foreground truncate">
                {PHASE_LABELS[s.test_phase] ?? s.test_phase}
              </p>
              {s.current_task_label && (
                <p className="text-[10px] text-blue-600 truncate">{s.current_task_label}</p>
              )}
              <p className="text-xs font-mono text-muted-foreground">{formatDuration(s.elapsed_time_s)}</p>
            </>
          )}

          {hasAwaitingTask && (
            <p className="text-[10px] text-amber-400 font-medium">Awaiting input</p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
});
