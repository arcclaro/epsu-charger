import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { TASK_STATUS_COLORS, STATE_COLORS, STATE_LABELS } from '@/lib/constants';

export function TaskStatusBadge({ status }: { status: string }) {
  const color = TASK_STATUS_COLORS[status] ?? 'bg-gray-500';
  return (
    <Badge variant="secondary" className={cn(color, 'text-white text-xs')}>
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}

export function StationStateBadge({ state }: { state: string }) {
  const color = STATE_COLORS[state] ?? 'bg-gray-500';
  const label = STATE_LABELS[state] ?? state;
  return (
    <Badge variant="secondary" className={cn(color, 'text-white text-xs')}>
      {label}
    </Badge>
  );
}

export function PassFailBadge({ result }: { result?: string | null }) {
  if (!result) return null;
  const color = result === 'pass' ? 'bg-green-600' : result === 'fail' ? 'bg-red-600' : 'bg-gray-500';
  return (
    <Badge variant="secondary" className={cn(color, 'text-white text-xs uppercase')}>
      {result}
    </Badge>
  );
}
