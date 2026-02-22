import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { TechPubRef } from '@/components/common/TechPubRef';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrder } from '@/api/workOrders';
import { matchTechPub } from '@/api/techPubs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Play } from 'lucide-react';

const statusColor = (s: string) => {
  switch (s) {
    case 'received': return 'bg-blue-600';
    case 'in_progress': return 'bg-amber-600';
    case 'completed': return 'bg-green-600';
    case 'closed': return 'bg-gray-600';
    default: return 'bg-gray-600';
  }
};

const itemStatusColor = (s: string) => {
  switch (s) {
    case 'pending': return 'bg-gray-600';
    case 'testing': return 'bg-blue-600';
    case 'passed': return 'bg-green-600';
    case 'failed': return 'bg-red-600';
    default: return 'bg-gray-600';
  }
};

export default function WorkOrderDetail() {
  const { woId } = useParams<{ woId: string }>();
  const { data: wo, isLoading, error } = useApiQuery(() => getWorkOrder(Number(woId)), [woId]);

  const firstItem = wo?.items?.[0] ?? null;

  const { data: techPub } = useApiQuery(
    () => (firstItem?.part_number ? matchTechPub(firstItem.part_number) : Promise.reject('no part')),
    [firstItem?.part_number],
  );

  if (isLoading) return <LoadingSpinner />;
  if (error || !wo) return <p className="text-red-600">Failed to load work order</p>;

  return (
    <div>
      <PageHeader
        title={wo.work_order_number}
        description={`Service: ${wo.service_type.replace(/_/g, ' ')}`}
      />

      {/* WO metadata cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Status</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <Badge className={`${statusColor(wo.status)} text-white`}>
              {wo.status}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Customer</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-sm">{wo.customer_name || `ID ${wo.customer_id}`}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Service Type</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-3">
            <p className="text-sm capitalize">{wo.service_type.replace(/_/g, ' ')}</p>
          </CardContent>
        </Card>

        {wo.internal_work_number && (
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm">Internal Work #</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-3">
              <p className="text-sm font-mono">{wo.internal_work_number}</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Battery info */}
      {firstItem && (
        <Card className="mb-6">
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Battery Information</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Part Number</p>
                <p className="font-mono text-sm">{firstItem.part_number}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Serial Number</p>
                <p className="font-mono text-sm">{firstItem.serial_number}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Amendment</p>
                <p className="text-sm">{firstItem.amendment || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Item Status</p>
                <Badge className={`${itemStatusColor(firstItem.status)} text-white text-xs`}>
                  {firstItem.status}
                </Badge>
              </div>
            </div>

            {/* Tech pub reference */}
            {techPub && (
              <div className="mt-4 pt-3 border-t">
                <p className="text-xs text-muted-foreground mb-1">Tech Pub Reference</p>
                <TechPubRef
                  cmm={techPub.cmm_number}
                  revision={techPub.revision}
                  ata={techPub.ata_chapter}
                  date={techPub.revision_date}
                />
              </div>
            )}

            {/* Result info if testing completed */}
            {firstItem.result && (
              <div className="mt-4 pt-3 border-t">
                <p className="text-xs text-muted-foreground mb-1">Result</p>
                <p className="text-sm font-medium">{firstItem.result}</p>
                {firstItem.failure_reason && (
                  <p className="text-xs text-muted-foreground mt-1">{firstItem.failure_reason}</p>
                )}
              </div>
            )}

            {/* Start Job action */}
            {firstItem.status === 'pending' && (
              <div className="mt-4 pt-3 border-t">
                <Button size="sm" asChild>
                  <Link to={`/work-orders/${wo.id}/items/${firstItem.id}/start-job`}>
                    <Play className="h-3 w-3 mr-1" />
                    Start Job
                  </Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Fallback when no items */}
      {!firstItem && (
        <Card className="mb-6">
          <CardContent className="py-8 text-center text-muted-foreground">
            No battery items associated with this work order.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
