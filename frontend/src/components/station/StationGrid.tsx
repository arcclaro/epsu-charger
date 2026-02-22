import { StationCard } from './StationCard';
import { useStations } from '@/hooks/useStations';
import { STATION_COUNT } from '@/lib/constants';
import type { StationStatus } from '@/types';

const emptyStation = (id: number): StationStatus => ({
  station_id: id,
  state: 'empty',
  temperature_c: 0,
  temperature_valid: false,
  voltage_mv: 0,
  current_ma: 0,
  eeprom_present: false,
  error_message: null,
  session_id: null,
  work_order_item_id: null,
  work_job_id: null,
  test_phase: 'idle',
  current_task_label: null,
  elapsed_time_s: 0,
  battery_config: null,
});

export function StationGrid() {
  const { stations, awaitingTasks } = useStations();

  const stationMap = new Map(stations.map(s => [s.station_id, s]));

  return (
    <div className="grid grid-cols-4 gap-3">
      {Array.from({ length: STATION_COUNT }, (_, i) => i + 1).map(id => (
        <StationCard
          key={id}
          station={stationMap.get(id) ?? emptyStation(id)}
          hasAwaitingTask={awaitingTasks.has(id)}
        />
      ))}
    </div>
  );
}
