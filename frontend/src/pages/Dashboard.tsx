import { StationGrid } from '@/components/station/StationGrid';
import { PageHeader } from '@/components/common/PageHeader';
import { useStations } from '@/hooks/useStations';

export default function Dashboard() {
  const { stations, connected } = useStations();
  const running = stations.filter(s => s.state === 'running').length;
  const errors = stations.filter(s => s.state === 'error').length;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description={
          connected
            ? `${stations.length} stations online · ${running} running · ${errors} errors`
            : 'Connecting to WebSocket...'
        }
      />
      <StationGrid />
    </div>
  );
}
