import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkJobs } from '@/api/workJobs';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Link } from 'react-router-dom';

export default function Sessions() {
  const { data, isLoading, error } = useApiQuery(() => getWorkJobs(), []);

  return (
    <div>
      <PageHeader title="Sessions" description="Work job sessions (legacy view)" />
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load sessions</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Job ID</TableHead>
                <TableHead>WO Number</TableHead>
                <TableHead>Battery</TableHead>
                <TableHead>Station</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Result</TableHead>
                <TableHead>Started</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(j => (
                <TableRow key={j.id}>
                  <TableCell>
                    <Link to={`/jobs/${j.id}`} className="text-blue-600 hover:underline">#{j.id}</Link>
                  </TableCell>
                  <TableCell className="font-mono">{j.work_order_number || '-'}</TableCell>
                  <TableCell className="font-mono text-xs">{j.battery_serial || '-'}</TableCell>
                  <TableCell>Stn {j.station_id}</TableCell>
                  <TableCell>
                    <Badge variant="secondary" className={`text-xs ${j.status === 'completed' ? 'bg-green-600' : j.status === 'in_progress' ? 'bg-blue-600' : 'bg-gray-600'} text-white`}>
                      {j.status}
                    </Badge>
                  </TableCell>
                  <TableCell>{j.overall_result || '-'}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {j.started_at ? new Date(j.started_at).toLocaleString() : '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
