import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { WorkOrderItem, WorkOrder } from '@/types';

export function StepSelectItem({ item, wo }: { item: WorkOrderItem; wo: WorkOrder }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">Confirm battery details for testing.</p>
      <Card>
        <CardHeader className="py-3 px-4">
          <CardTitle className="text-sm">Battery Information</CardTitle>
        </CardHeader>
        <CardContent className="px-4 pb-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-muted-foreground text-xs">Serial Number</p>
            <p className="font-mono font-medium">{item.serial_number}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Part Number</p>
            <p className="font-mono font-medium">{item.part_number}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Revision</p>
            <p className="font-mono">{item.revision}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Amendment</p>
            <p className="font-mono">{item.amendment || '-'}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Work Order</p>
            <p className="font-mono">{wo.work_order_number}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Reported Condition</p>
            <p>{item.reported_condition || 'Normal'}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
