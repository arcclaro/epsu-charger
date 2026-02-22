import { useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkJobs } from '@/api/workJobs';
import { getCustomers } from '@/api/customers';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Link } from 'react-router-dom';
import { Search } from 'lucide-react';

export default function Sessions() {
  const [search, setSearch] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [customerId, setCustomerId] = useState<string>('');

  const { data: customers } = useApiQuery(() => getCustomers(), []);

  const { data, isLoading, error } = useApiQuery(
    () =>
      getWorkJobs({
        search: search || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        customer_id: customerId ? Number(customerId) : undefined,
      }),
    [search, fromDate, toDate, customerId],
  );

  return (
    <div>
      <PageHeader title="Sessions" description="Work job sessions (legacy view)" />

      <Card className="mb-4 p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <Label htmlFor="search" className="text-xs text-muted-foreground">Work Order</Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="search"
                placeholder="Search work orders..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>

          <div className="space-y-1">
            <Label htmlFor="from-date" className="text-xs text-muted-foreground">Date From</Label>
            <Input
              id="from-date"
              type="date"
              value={fromDate}
              onChange={e => setFromDate(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <Label htmlFor="to-date" className="text-xs text-muted-foreground">Date To</Label>
            <Input
              id="to-date"
              type="date"
              value={toDate}
              onChange={e => setToDate(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <Label htmlFor="customer" className="text-xs text-muted-foreground">Customer</Label>
            <Select value={customerId} onValueChange={setCustomerId}>
              <SelectTrigger id="customer">
                <SelectValue placeholder="All customers" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All customers</SelectItem>
                {customers?.map(c => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

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
