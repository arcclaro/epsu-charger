import { useState, useEffect } from 'react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getSystemInfo, getHealthCheck, type SystemInfo } from '@/api/admin';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

function formatUptime(seconds?: number): string {
  if (seconds == null) return '—';
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  return `${days} days ${hours} hours`;
}

function percentColor(pct: number): string {
  if (pct >= 90) return '[&_[data-slot=progress-indicator]]:bg-red-500';
  if (pct >= 70) return '[&_[data-slot=progress-indicator]]:bg-amber-500';
  return '[&_[data-slot=progress-indicator]]:bg-green-500';
}

function tempColor(temp: number): string {
  if (temp >= 80) return '[&_[data-slot=progress-indicator]]:bg-red-500';
  if (temp >= 65) return '[&_[data-slot=progress-indicator]]:bg-amber-500';
  return '[&_[data-slot=progress-indicator]]:bg-green-500';
}

interface MetricCardProps {
  title: string;
  percent: number;
  displayValue: string;
  subtitle: string;
  barClass: string;
}

function MetricCard({ title, percent, displayValue, subtitle, barClass }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="py-3 px-4">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-3 space-y-2">
        <p className="text-2xl font-bold">{displayValue}</p>
        <Progress value={percent} className={`h-2 ${barClass}`} />
        <p className="text-xs text-muted-foreground">{subtitle}</p>
      </CardContent>
    </Card>
  );
}

function buildMetricCards(info: SystemInfo): MetricCardProps[] {
  const cpuPct = info.cpu_percent ?? 0;
  const memPct = info.memory_percent ?? 0;
  const diskPct = info.disk_percent ?? 0;
  const temp = info.cpu_temp_c;
  const tempPct = temp != null ? Math.min((temp / 85) * 100, 100) : 0;

  return [
    {
      title: 'CPU',
      percent: cpuPct,
      displayValue: info.cpu_percent != null ? `${cpuPct.toFixed(1)}%` : '—',
      subtitle: info.platform ?? 'Unknown platform',
      barClass: percentColor(cpuPct),
    },
    {
      title: 'Memory',
      percent: memPct,
      displayValue: info.memory_percent != null ? `${memPct.toFixed(1)}%` : '—',
      subtitle:
        info.memory_used_mb != null && info.memory_total_mb != null
          ? `${(info.memory_used_mb / 1024).toFixed(1)} / ${(info.memory_total_mb / 1024).toFixed(1)} GB`
          : '—',
      barClass: percentColor(memPct),
    },
    {
      title: 'Disk',
      percent: diskPct,
      displayValue: info.disk_percent != null ? `${diskPct.toFixed(1)}%` : '—',
      subtitle:
        info.disk_free_gb != null && info.disk_total_gb != null
          ? `${info.disk_free_gb.toFixed(1)} GB free of ${info.disk_total_gb.toFixed(1)} GB`
          : '—',
      barClass: percentColor(diskPct),
    },
    {
      title: 'Temperature',
      percent: tempPct,
      displayValue: temp != null ? `${temp.toFixed(1)} °C` : '—',
      subtitle: temp != null ? `${temp.toFixed(1)} °C` : '—',
      barClass: temp != null ? tempColor(temp) : percentColor(0),
    },
  ];
}

export function AdminSystem() {
  const {
    data: info,
    isLoading: infoLoading,
    refetch: refetchInfo,
  } = useApiQuery(() => getSystemInfo(), []);
  const { data: health, isLoading: healthLoading } = useApiQuery(() => getHealthCheck(), []);

  // Auto-refresh system info every 10 seconds
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => {
      refetchInfo();
      setTick((t) => t + 1);
    }, 10_000);
    return () => clearInterval(id);
  }, [refetchInfo]);

  const metrics = info ? buildMetricCards(info) : [];

  return (
    <div className="space-y-4">
      {/* Metric cards */}
      {infoLoading && !info ? (
        <LoadingSpinner />
      ) : info ? (
        <>
          <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
            {metrics.map((m) => (
              <MetricCard key={m.title} {...m} />
            ))}
          </div>

          {/* System summary row */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm">System Info</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-sm">
                <p>
                  <span className="text-muted-foreground">Hostname:</span>{' '}
                  {info.hostname}
                </p>
                <p>
                  <span className="text-muted-foreground">Platform:</span>{' '}
                  {info.platform}
                </p>
                <p>
                  <span className="text-muted-foreground">Version:</span>{' '}
                  {info.version}
                </p>
                <p>
                  <span className="text-muted-foreground">Python:</span>{' '}
                  {info.python}
                </p>
                <p>
                  <span className="text-muted-foreground">Stations:</span>{' '}
                  {info.stations}
                </p>
                <p>
                  <span className="text-muted-foreground">Uptime:</span>{' '}
                  {formatUptime(info.uptime_s)}
                </p>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="px-4 py-3">
            <p className="text-muted-foreground">System info unavailable</p>
          </CardContent>
        </Card>
      )}

      {/* Health check card */}
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
