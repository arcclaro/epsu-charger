import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getAwaitingInput } from '@/api/jobTasks';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { STEP_TYPE_LABELS } from '@/lib/constants';
import { Pencil } from 'lucide-react';

export default function StationAwaiting() {
  const { id } = useParams<{ id: string }>();
  const stationId = Number(id);
  const { data, isLoading, error } = useApiQuery(() => getAwaitingInput(stationId), [stationId]);

  return (
    <div>
      <PageHeader title={`Station ${stationId} — Awaiting Input`} />
      {isLoading ? <LoadingSpinner /> : error ? (
        <p className="text-red-600">Failed to load tasks</p>
      ) : data?.length === 0 ? (
        <p className="text-muted-foreground">No tasks awaiting input on this station.</p>
      ) : (
        <div className="space-y-3">
          {data?.map(task => (
            <Card key={task.id} className="border-amber-500/30">
              <CardContent className="p-4 flex items-center gap-4">
                <Badge className="bg-amber-500 text-white shrink-0">#{task.task_number}</Badge>
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{task.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {STEP_TYPE_LABELS[task.step_type] ?? task.step_type}
                    {task.description && ` — ${task.description}`}
                  </p>
                </div>
                <Button size="sm" asChild>
                  <Link to={`/jobs/${task.work_job_id}/tasks/${task.id}`}>
                    <Pencil className="h-3 w-3 mr-1" />Enter Data
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
