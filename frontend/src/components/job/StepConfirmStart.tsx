import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { startJob } from '@/api/jobTasks';
import { Loader2, Rocket } from 'lucide-react';
import type { WorkOrderItem, WorkOrder, ResolvedProcedure } from '@/types';

interface Props {
  item: WorkOrderItem;
  wo: WorkOrder;
  stationId: number;
  serviceType: string;
  monthsSinceService: number;
  startedBy: string;
  procedure: ResolvedProcedure;
  onSuccess: (jobId: number) => void;
}

export function StepConfirmStart({
  item, wo, stationId, serviceType, monthsSinceService, startedBy, procedure, onSuccess,
}: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStart = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await startJob({
        work_order_item_id: item.id,
        station_id: stationId,
        service_type: serviceType,
        months_since_service: monthsSinceService,
        started_by: startedBy,
      });
      onSuccess(result.work_job_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start job');
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Review and confirm to start the job.</p>

      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">Job Summary</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Work Order</p>
            <p className="font-mono">{wo.work_order_number}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Battery</p>
            <p className="font-mono">{item.serial_number} ({item.part_number})</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Station</p>
            <p className="font-medium">Station {stationId}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Service Type</p>
            <p>{serviceType.replace(/_/g, ' ')}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">CMM</p>
            <p className="font-mono">{procedure.cmm_number} Rev {procedure.cmm_revision}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Procedure</p>
            <p>{procedure.total_steps} steps, ~{procedure.estimated_hours.toFixed(1)} hrs</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Months Since Service</p>
            <p>{monthsSinceService}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Technician</p>
            <p>{startedBy}</p>
          </div>
        </CardContent>
      </Card>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <Button onClick={handleStart} disabled={submitting} size="lg" className="w-full">
        {submitting ? (
          <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Starting Job...</>
        ) : (
          <><Rocket className="h-4 w-4 mr-2" />Start Job</>
        )}
      </Button>
    </div>
  );
}
