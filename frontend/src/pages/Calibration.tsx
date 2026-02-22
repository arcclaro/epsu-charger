import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getStationCalibrations } from '@/api/calibration';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function Calibration() {
  const { data, isLoading, error } = useApiQuery(() => getStationCalibrations(), []);

  return (
    <div>
      <PageHeader title="Calibration" description="Station equipment calibration status" />
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load calibration data</p>
      ) : (
        <div className="grid grid-cols-4 gap-3">
          {data?.map(cal => (
            <Card key={cal.station_id}>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm">Station {cal.station_id}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 pb-3 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">PSU</span>
                  <Badge variant="secondary" className={`text-[10px] ${cal.psu_cal_status === 'valid' ? 'bg-green-600' : 'bg-amber-600'} text-white`}>
                    {cal.psu_cal_status || 'unknown'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">DC Load</span>
                  <Badge variant="secondary" className={`text-[10px] ${cal.dc_load_cal_status === 'valid' ? 'bg-green-600' : 'bg-amber-600'} text-white`}>
                    {cal.dc_load_cal_status || 'unknown'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
