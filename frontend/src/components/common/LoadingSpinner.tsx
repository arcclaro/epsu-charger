import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export function LoadingSpinner({ className, text }: { className?: string; text?: string }) {
  return (
    <div className={cn('flex items-center justify-center gap-2 p-8 text-muted-foreground', className)}>
      <Loader2 className="h-5 w-5 animate-spin" />
      {text && <span>{text}</span>}
    </div>
  );
}
