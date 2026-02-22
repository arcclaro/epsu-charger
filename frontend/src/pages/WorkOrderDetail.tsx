import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrder } from '@/api/workOrders';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Play } from 'lucide-react';

export default function WorkOrderDetail() {
  const { woId } = useParams<{ woId: string }>();
  const { data: wo, isLoading, error } = useApiQuery(() => getWorkOrder(Number(woId)), [woId]);

  if (isLoading) return <LoadingSpinner />;
  if (error || !wo) return <p className="text-red-600">Failed to load work order</p>;

  const itemStatusColor = (s: string) => {
    switch (s) {
      case 'pending': return 'bg-gray-600';
      case 'testing': return 'bg-blue-600';
      case 'passed': return 'bg-green-600';
      case 'failed': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div>
      <PageHeader title={wo.work_order_number} description={`Service: ${wo.service_type.replace(/_/g, ' ')}`} />

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader className="py-3 px-4"><CardTitle className="text-sm">Status</CardTitle></CardHeader>
          <CardContent className="px-4 pb-3">
            <Badge className={`${wo.status === 'completed' ? 'bg-green-600' : wo.status === 'in_progress' ? 'bg-amber-600' : 'bg-blue-600'} text-white`}>
              {wo.status}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="py-3 px-4"><CardTitle className="text-sm">Priority</CardTitle></CardHeader>
          <CardContent className="px-4 pb-3"><p className="capitalize">{wo.priority}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="py-3 px-4"><CardTitle className="text-sm">Customer Ref</CardTitle></CardHeader>
          <CardContent className="px-4 pb-3"><p>{wo.customer_reference || '-'}</p></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">Battery Items ({wo.items?.length ?? 0})</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Serial</TableHead>
              <TableHead>Part Number</TableHead>
              <TableHead>Amendment</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Result</TableHead>
              <TableHead>Station</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {wo.items?.map(item => (
              <TableRow key={item.id}>
                <TableCell className="font-mono">{item.serial_number}</TableCell>
                <TableCell className="font-mono">{item.part_number}</TableCell>
                <TableCell>{item.amendment || '-'}</TableCell>
                <TableCell>
                  <Badge className={`${itemStatusColor(item.status)} text-white text-xs`}>
                    {item.status}
                  </Badge>
                </TableCell>
                <TableCell>{item.result || '-'}</TableCell>
                <TableCell>{item.current_station_id ?? '-'}</TableCell>
                <TableCell>
                  {item.status === 'pending' && (
                    <Button size="sm" variant="outline" asChild>
                      <Link to={`/work-orders/${wo.id}/items/${item.id}/start-job`}>
                        <Play className="h-3 w-3 mr-1" />Start Job
                      </Link>
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
