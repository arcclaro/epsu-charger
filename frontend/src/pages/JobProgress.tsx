import { useParams, Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getJobTasks } from '@/api/jobTasks';
import { getWorkJob } from '@/api/workJobs';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TaskStatusBadge, PassFailBadge } from '@/components/common/StatusBadge';
import { STEP_TYPE_LABELS } from '@/lib/constants';
import { Pencil, RefreshCw } from 'lucide-react';

export default function JobProgress() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading: jobLoading } = useApiQuery(() => getWorkJob(Number(jobId)), [jobId]);
  const { data: tasks, isLoading: tasksLoading, refetch } = useApiQuery(() => getJobTasks(Number(jobId)), [jobId]);

  if (jobLoading || tasksLoading) return <LoadingSpinner text="Loading job..." />;
  if (!job) return <p className="text-red-600">Job not found</p>;

  const completed = tasks?.filter(t => t.status === 'completed' || t.status === 'skipped').length ?? 0;
  const total = tasks?.length ?? 0;
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div>
      <PageHeader
        title={`Job #${job.id}`}
        description={`${job.work_order_number ?? ''} — ${job.battery_serial ?? ''} — Station ${job.station_id}`}
        actions={
          <Button size="sm" variant="outline" onClick={refetch}>
            <RefreshCw className="h-3 w-3 mr-1" />Refresh
          </Button>
        }
      />

      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="flex items-center gap-4 mb-2 text-sm">
            <span>Progress: {completed}/{total} tasks ({pct}%)</span>
            {job.tech_pub_cmm && <span className="font-mono text-muted-foreground">CMM: {job.tech_pub_cmm}</span>}
            <Badge variant="secondary" className={`${job.status === 'completed' ? 'bg-green-600' : 'bg-blue-600'} text-white text-xs`}>
              {job.status}
            </Badge>
            {job.overall_result && <PassFailBadge result={job.overall_result} />}
          </div>
          <Progress value={pct} className="h-2" />
        </CardContent>
      </Card>

      {/* Task Timeline */}
      <div className="space-y-2">
        {tasks?.map(task => {
          const isAwaiting = task.status === 'awaiting_input';
          return (
            <Card
              key={task.id}
              className={`transition-colors ${isAwaiting ? 'border-amber-500/60 ring-1 ring-amber-500/30' : ''}`}
            >
              <CardContent className="p-3 flex items-center gap-3">
                <Badge variant="outline" className="shrink-0 font-mono text-xs w-8 justify-center">
                  {task.task_number}
                </Badge>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className={`text-sm truncate ${isAwaiting ? 'text-amber-400 font-medium' : ''}`}>
                      {task.label}
                    </p>
                    {task.is_automated && <Badge variant="outline" className="text-[10px] shrink-0">Auto</Badge>}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {STEP_TYPE_LABELS[task.step_type] ?? task.step_type}
                  </p>
                </div>
                <TaskStatusBadge status={task.status} />
                <PassFailBadge result={task.step_result} />
                {isAwaiting && (
                  <Button size="sm" asChild>
                    <Link to={`/jobs/${jobId}/tasks/${task.id}`}>
                      <Pencil className="h-3 w-3 mr-1" />Enter Data
                    </Link>
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
