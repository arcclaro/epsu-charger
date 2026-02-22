import { useApiQuery } from '@/hooks/useApiQuery';
import { getAvailableTools } from '@/api/jobTasks';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import type { Tool } from '@/types';

interface Props {
  requiresTools: string[];
  selectedToolIds: number[];
  onToggle: (toolId: number) => void;
}

export function ToolSelector({ requiresTools, selectedToolIds, onToggle }: Props) {
  const category = requiresTools[0] ?? undefined;
  const { data: tools, isLoading } = useApiQuery(
    () => getAvailableTools(category),
    [category],
  );

  if (requiresTools.length === 0) return null;

  const isExpired = (tool: Tool) => {
    if (!tool.valid_until) return false;
    return new Date(tool.valid_until) < new Date();
  };

  return (
    <div className="space-y-2">
      <Label>Tools Required ({requiresTools.join(', ')})</Label>
      {isLoading ? (
        <p className="text-xs text-muted-foreground">Loading tools...</p>
      ) : (
        <div className="space-y-1">
          {tools?.map(tool => {
            const expired = isExpired(tool);
            const selected = selectedToolIds.includes(tool.id);
            return (
              <div
                key={tool.id}
                onClick={() => !expired && onToggle(tool.id)}
                className={`flex items-center gap-3 p-2 rounded border text-sm cursor-pointer transition-colors ${
                  expired
                    ? 'opacity-50 cursor-not-allowed border-red-500/30'
                    : selected
                      ? 'border-primary bg-primary/10'
                      : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{tool.tool_id_display ?? tool.serial_number}</p>
                  <p className="text-xs text-muted-foreground truncate">{tool.description}</p>
                </div>
                {expired ? (
                  <Badge variant="destructive" className="text-[10px]">Cal Expired</Badge>
                ) : tool.valid_until ? (
                  <Badge variant="secondary" className="bg-green-600/20 text-green-400 text-[10px]">
                    Cal Valid
                  </Badge>
                ) : null}
              </div>
            );
          })}
          {tools?.length === 0 && <p className="text-xs text-muted-foreground">No tools available</p>}
        </div>
      )}
    </div>
  );
}
