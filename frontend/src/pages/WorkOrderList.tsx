import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrders } from '@/api/workOrders';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Search } from 'lucide-react';

export default function WorkOrderList() {
  const [search, setSearch] = useState('');
  const { data, isLoading, error } = useApiQuery(() => getWorkOrders({ search: search || undefined }), [search]);

  const statusColor = (s: string) => {
    switch (s) {
      case 'received': return 'bg-blue-600';
      case 'in_progress': return 'bg-amber-600';
      case 'completed': return 'bg-green-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div>
      <PageHeader
        title="Work Orders"
        description="Customer service orders"
      />
      <div className="mb-4 relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search work orders..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load work orders</p>
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>WO Number</TableHead>
                <TableHead>Customer Ref</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Priority</TableHead>
                <TableHead>Items</TableHead>
                <TableHead>Received</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map(wo => (
                <TableRow key={wo.id} className="cursor-pointer hover:bg-accent/50">
                  <TableCell>
                    <Link to={`/work-orders/${wo.id}`} className="text-blue-600 hover:underline font-medium">
                      {wo.work_order_number}
                    </Link>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{wo.customer_reference || '-'}</TableCell>
                  <TableCell>{wo.service_type.replace(/_/g, ' ')}</TableCell>
                  <TableCell>
                    <Badge className={`${statusColor(wo.status)} text-white text-xs`}>{wo.status}</Badge>
                  </TableCell>
                  <TableCell>{wo.priority}</TableCell>
                  <TableCell>{wo.item_count ?? wo.items?.length ?? '-'}</TableCell>
                  <TableCell className="text-muted-foreground text-xs">
                    {new Date(wo.received_date).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
              {data?.length === 0 && (
                <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground">No work orders found</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
