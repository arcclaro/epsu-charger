import { useStations } from '@/hooks/useStations';
import { Card, CardContent } from '@/components/ui/card';
import { StationStateBadge } from '@/components/common/StatusBadge';
import { cn } from '@/lib/utils';
import { STATION_COUNT } from '@/lib/constants';

interface Props {
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function StepSelectStation({ selectedId, onSelect }: Props) {
  const { stations } = useStations();
  const stationMap = new Map(stations.map(s => [s.station_id, s]));

  const isAvailable = (id: number) => {
    const s = stationMap.get(id);
    return !s || s.state === 'empty' || s.state === 'ready';
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Select an available station for testing.</p>
      <div className="grid grid-cols-4 gap-3">
        {Array.from({ length: STATION_COUNT }, (_, i) => i + 1).map(id => {
          const s = stationMap.get(id);
          const available = isAvailable(id);
          const selected = selectedId === id;
          return (
            <Card
              key={id}
              className={cn(
                'cursor-pointer transition-colors duration-150',
                !available && 'opacity-40 cursor-not-allowed',
                selected && 'border-primary ring-2 ring-primary/30',
                available && !selected && 'hover:border-primary/50',
              )}
              onClick={() => available && onSelect(id)}
            >
              <CardContent className="p-3 flex items-center justify-between">
                <span className="text-sm font-semibold">Stn {id}</span>
                <StationStateBadge state={s?.state ?? 'empty'} />
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
