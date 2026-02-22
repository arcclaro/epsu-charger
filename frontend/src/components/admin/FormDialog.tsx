import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface FormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: () => void;
  title: string;
  loading?: boolean;
  wide?: boolean;
  children: React.ReactNode;
}

export function FormDialog({
  open,
  onClose,
  onSubmit,
  title,
  loading,
  wide,
  children,
}: FormDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className={cn('gap-0', wide ? 'sm:max-w-2xl' : 'sm:max-w-lg')}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader className="pb-4">
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription className="sr-only">
            {title} form
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh] pr-3">
          <div className="space-y-3 pb-1">{children}</div>
        </ScrollArea>
        <DialogFooter className="pt-4 border-t mt-4">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={loading}>
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
