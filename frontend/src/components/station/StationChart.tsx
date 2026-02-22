import { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useStations } from '@/hooks/useStations';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface DataPoint {
  time: number;
  voltage: number;
  current: number;
  temp: number;
}

const MAX_POINTS = 300;

export default function StationChart({ stationId }: { stationId: number }) {
  const { stations } = useStations();
  const [data, setData] = useState<DataPoint[]>([]);
  const [activeChart, setActiveChart] = useState<'all' | 'voltage' | 'current' | 'temp'>('all');
  const startTime = useRef(Date.now());

  const station = stations.find(s => s.station_id === stationId);

  useEffect(() => {
    if (!station || station.state === 'empty') return;
    setData(prev => {
      const point: DataPoint = {
        time: Math.round((Date.now() - startTime.current) / 1000),
        voltage: station.voltage_mv / 1000,
        current: station.current_ma / 1000,
        temp: station.temperature_c,
      };
      const next = [...prev, point];
      return next.length > MAX_POINTS ? next.slice(-MAX_POINTS) : next;
    });
  }, [station, station?.voltage_mv, station?.current_ma, station?.temperature_c]);

  if (!station || station.state === 'empty') return null;

  return (
    <Card>
      <CardHeader className="py-2 px-3 flex-row items-center justify-between">
        <CardTitle className="text-xs text-muted-foreground">V / I / T Curves</CardTitle>
        <Tabs value={activeChart} onValueChange={v => setActiveChart(v as typeof activeChart)}>
          <TabsList className="h-7">
            <TabsTrigger value="all" className="text-xs px-2 h-5">All</TabsTrigger>
            <TabsTrigger value="voltage" className="text-xs px-2 h-5">V</TabsTrigger>
            <TabsTrigger value="current" className="text-xs px-2 h-5">I</TabsTrigger>
            <TabsTrigger value="temp" className="text-xs px-2 h-5">T</TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent className="px-3 pb-3">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="time" tick={{ fontSize: 10 }} stroke="#6b7280" />
            {(activeChart === 'all' || activeChart === 'voltage') && (
              <>
                <YAxis yAxisId="v" orientation="left" tick={{ fontSize: 10 }} stroke="#60a5fa" />
                <Area yAxisId="v" type="monotone" dataKey="voltage" stroke="#60a5fa" fill="#60a5fa" fillOpacity={0.1} name="Voltage (V)" />
              </>
            )}
            {(activeChart === 'all' || activeChart === 'current') && (
              <>
                <YAxis yAxisId="i" orientation={activeChart === 'all' ? 'right' : 'left'} tick={{ fontSize: 10 }} stroke="#34d399" />
                <Area yAxisId="i" type="monotone" dataKey="current" stroke="#34d399" fill="#34d399" fillOpacity={0.1} name="Current (A)" />
              </>
            )}
            {(activeChart === 'all' || activeChart === 'temp') && (
              <>
                <YAxis yAxisId="t" orientation="right" tick={{ fontSize: 10 }} stroke="#fbbf24" hide={activeChart === 'all'} />
                <Area yAxisId={activeChart === 'temp' ? 't' : 'i'} type="monotone" dataKey="temp" stroke="#fbbf24" fill="#fbbf24" fillOpacity={0.1} name="Temp (°C)" />
              </>
            )}
            <Tooltip
              contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '6px', fontSize: 11 }}
              labelStyle={{ color: '#9ca3af' }}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
