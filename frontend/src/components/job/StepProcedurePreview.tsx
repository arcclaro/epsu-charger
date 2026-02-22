import { useEffect } from 'react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { resolveProcedure } from '@/api/procedures';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { STEP_TYPE_LABELS } from '@/lib/constants';
import type { ResolvedProcedure } from '@/types';

interface Props {
  itemId: number;
  serviceType: string;
  monthsSinceService: number;
  onLoaded: (proc: ResolvedProcedure) => void;
}

export function StepProcedurePreview({ itemId, serviceType, monthsSinceService, onLoaded }: Props) {
  const { data, isLoading, error } = useApiQuery(
    () => resolveProcedure(itemId, serviceType, monthsSinceService),
    [itemId, serviceType, monthsSinceService],
  );

  useEffect(() => {
    if (data) onLoaded(data);
  }, [data, onLoaded]);

  if (isLoading) return <LoadingSpinner text="Resolving procedure..." />;
  if (error) return <p className="text-red-600">Failed to resolve procedure. This battery may not have a matching CMM.</p>;
  if (!data) return null;

  const automated = data.sections.flatMap(s => s.steps).filter(s => s.is_automated).length;
  const manual = data.total_steps - automated;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm">
        <span>CMM: <span className="font-mono font-medium">{data.cmm_number}</span></span>
        <span>Rev: {data.cmm_revision}</span>
        <span>{data.total_steps} steps</span>
        <span>~{data.estimated_hours.toFixed(1)} hrs</span>
      </div>
      <div className="flex gap-2 text-xs">
        <Badge className="bg-blue-600 text-white">{automated} automated</Badge>
        <Badge className="bg-amber-600 text-white">{manual} manual</Badge>
      </div>

      <div className="space-y-3">
        {data.sections.map(section => (
          <Card key={section.section_id}>
            <CardHeader className="py-2 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <span className="font-mono text-muted-foreground">{section.section_number}</span>
                {section.title}
                {!section.is_mandatory && (
                  <Badge variant="outline" className="text-[10px]">Optional</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-3">
              <div className="space-y-1">
                {section.steps.map(step => (
                  <div
                    key={step.step_id}
                    className={`flex items-center gap-2 text-xs p-1.5 rounded ${
                      step.is_automated ? 'bg-blue-500/10' : 'bg-amber-500/10'
                    }`}
                  >
                    <span className={`h-2 w-2 rounded-full shrink-0 ${step.is_automated ? 'bg-blue-500' : 'bg-amber-500'}`} />
                    <span className="font-mono text-muted-foreground w-6">{step.step_number}</span>
                    <span className="flex-1 truncate">{step.label}</span>
                    <span className="text-muted-foreground shrink-0">
                      {STEP_TYPE_LABELS[step.step_type] ?? step.step_type}
                    </span>
                    {step.requires_tools.length > 0 && (
                      <Badge variant="outline" className="text-[10px]">Tools</Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
