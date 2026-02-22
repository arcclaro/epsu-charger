import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getSystemInfo, getHealthCheck } from '@/api/admin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function AdminSystem() {
  const { data: info, isLoading: infoLoading } = useApiQuery(() => getSystemInfo(), []);
  const { data: health, isLoading: healthLoading } = useApiQuery(() => getHealthCheck(), []);

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">System Info</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-3">
          {infoLoading ? (
            <LoadingSpinner />
          ) : info ? (
            <div className="space-y-1 text-sm">
              {Object.entries(info).map(([k, v]) => (
                <p key={k}>
                  <span className="text-muted-foreground">{k}:</span> {String(v)}
                </p>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Unavailable</p>
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">Health Check</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-3">
          {healthLoading ? (
            <LoadingSpinner />
          ) : health ? (
            <div className="space-y-2 text-sm">
              {Object.entries(health).map(([k, v]) => (
                <div key={k} className="flex justify-between">
                  <span className="text-muted-foreground">{k}</span>
                  <Badge
                    variant="secondary"
                    className={`${
                      v === 'ok' || v === 'healthy'
                        ? 'bg-green-600'
                        : 'bg-amber-600'
                    } text-white text-xs`}
                  >
                    {String(v)}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Unavailable</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
