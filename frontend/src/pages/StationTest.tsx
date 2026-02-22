import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertTriangle } from 'lucide-react';
import { useStations } from '@/hooks/useStations';
import { sendControl, getStationDiagnostics } from '@/api/stations';
import type { DiagnosticsReport } from '@/types';

export default function StationTest() {
  const { id } = useParams<{ id: string }>();
  const stationId = Number(id);
  const { stations } = useStations();
  const station = stations.find(s => s.station_id === stationId);

  // PSU state
  const [psuVoltage, setPsuVoltage] = useState('');
  const [psuCurrent, setPsuCurrent] = useState('');
  const [psuEnabled, setPsuEnabled] = useState(false);

  // DC Load state
  const [loadCurrent, setLoadCurrent] = useState('');
  const [loadMode, setLoadMode] = useState<'CC' | 'CV'>('CC');
  const [loadEnabled, setLoadEnabled] = useState(false);

  // Diagnostics polling
  const [diagnostics, setDiagnostics] = useState<DiagnosticsReport | null>(null);

  useEffect(() => {
    let active = true;
    const poll = () => {
      getStationDiagnostics(stationId)
        .then(d => { if (active) setDiagnostics(d); })
        .catch(() => {});
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => { active = false; clearInterval(interval); };
  }, [stationId]);

  const hasActiveJob = station?.work_job_id != null;

  const handlePsuSet = () => {
    sendControl({
      station_id: stationId,
      command: 'charge',
      voltage_mv: Math.round(Number(psuVoltage) * 1000),
      current_ma: Math.round(Number(psuCurrent) * 1000),
    } as Parameters<typeof sendControl>[0]);
  };

  const handlePsuToggle = () => {
    if (psuEnabled) {
      sendControl({ station_id: stationId, command: 'stop' });
    } else {
      handlePsuSet();
    }
    setPsuEnabled(!psuEnabled);
  };

  const handleLoadSet = () => {
    sendControl({
      station_id: stationId,
      command: 'discharge',
      current_ma: Math.round(Number(loadCurrent) * 1000),
    } as Parameters<typeof sendControl>[0]);
  };

  const handleLoadToggle = () => {
    if (loadEnabled) {
      sendControl({ station_id: stationId, command: 'stop' });
    } else {
      handleLoadSet();
    }
    setLoadEnabled(!loadEnabled);
  };

  return (
    <div>
      <PageHeader
        title={`Station ${stationId} - Test Equipment`}
        actions={
          station ? (
            <Badge variant="secondary" className="text-xs">
              {station.state}
            </Badge>
          ) : null
        }
      />

      {hasActiveJob && (
        <div className="mb-4 p-3 rounded-md bg-amber-500/10 border border-amber-500/30 flex items-center gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
          <p className="text-sm text-amber-400 font-medium">
            Warning: Station has an active work job (#{station?.work_job_id}). Manual equipment control may interfere with the running test.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* PSU Panel */}
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm flex items-center justify-between">
              PSU Control
              <Badge variant={psuEnabled ? 'default' : 'secondary'} className={psuEnabled ? 'bg-green-600' : ''}>
                {psuEnabled ? 'ON' : 'OFF'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-4">
            <div className="space-y-1">
              <Label htmlFor="psu-voltage" className="text-xs text-muted-foreground">Set Voltage (V)</Label>
              <Input
                id="psu-voltage"
                type="number"
                step="0.1"
                placeholder="0.0"
                value={psuVoltage}
                onChange={e => setPsuVoltage(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="psu-current" className="text-xs text-muted-foreground">Set Current (A)</Label>
              <Input
                id="psu-current"
                type="number"
                step="0.1"
                placeholder="0.0"
                value={psuCurrent}
                onChange={e => setPsuCurrent(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handlePsuSet} disabled={!psuVoltage && !psuCurrent}>
                Apply
              </Button>
              <Button
                size="sm"
                variant={psuEnabled ? 'destructive' : 'default'}
                onClick={handlePsuToggle}
              >
                {psuEnabled ? 'Disable' : 'Enable'}
              </Button>
            </div>

            <div className="border-t pt-3 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Actual Readings</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Voltage:</span>{' '}
                  <span className="font-mono">
                    {station ? `${(station.voltage_mv / 1000).toFixed(3)} V` : '--'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Current:</span>{' '}
                  <span className="font-mono">
                    {station ? `${(station.current_ma / 1000).toFixed(3)} A` : '--'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">PSU Status:</span>{' '}
                  <span className="font-mono">{diagnostics?.psu_status ?? '--'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* DC Load Panel */}
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm flex items-center justify-between">
              DC Load Control
              <Badge variant={loadEnabled ? 'default' : 'secondary'} className={loadEnabled ? 'bg-green-600' : ''}>
                {loadEnabled ? 'ON' : 'OFF'}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-4">
            <div className="space-y-1">
              <Label htmlFor="load-current" className="text-xs text-muted-foreground">Set Current (A)</Label>
              <Input
                id="load-current"
                type="number"
                step="0.1"
                placeholder="0.0"
                value={loadCurrent}
                onChange={e => setLoadCurrent(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="load-mode" className="text-xs text-muted-foreground">Mode</Label>
              <Select value={loadMode} onValueChange={v => setLoadMode(v as 'CC' | 'CV')}>
                <SelectTrigger id="load-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CC">CC (Constant Current)</SelectItem>
                  <SelectItem value="CV">CV (Constant Voltage)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleLoadSet} disabled={!loadCurrent}>
                Apply
              </Button>
              <Button
                size="sm"
                variant={loadEnabled ? 'destructive' : 'default'}
                onClick={handleLoadToggle}
              >
                {loadEnabled ? 'Disable' : 'Enable'}
              </Button>
            </div>

            <div className="border-t pt-3 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Actual Readings</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Voltage:</span>{' '}
                  <span className="font-mono">
                    {station ? `${(station.voltage_mv / 1000).toFixed(3)} V` : '--'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Current:</span>{' '}
                  <span className="font-mono">
                    {station ? `${(station.current_ma / 1000).toFixed(3)} A` : '--'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Load Status:</span>{' '}
                  <span className="font-mono">{diagnostics?.load_status ?? '--'}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
