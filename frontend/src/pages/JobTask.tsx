import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getTask, submitTask, skipTask } from '@/api/jobTasks';
import { MeasurementInput } from '@/components/task/MeasurementInput';
import { ToolSelector } from '@/components/task/ToolSelector';
import { PassCriteriaDisplay } from '@/components/task/PassCriteriaDisplay';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { STEP_TYPE_LABELS } from '@/lib/constants';
import { Loader2, Send, SkipForward } from 'lucide-react';
import type { StepResult } from '@/types';

export default function JobTask() {
  const { jobId, taskId } = useParams<{ jobId: string; taskId: string }>();
  const navigate = useNavigate();
  const { data: task, isLoading, error } = useApiQuery(() => getTask(Number(taskId)), [taskId]);

  const [measuredValue, setMeasuredValue] = useState<unknown>('');
  const [stepResult, setStepResult] = useState<StepResult>('pass');
  const [notes, setNotes] = useState('');
  const [performedBy, setPerformedBy] = useState(localStorage.getItem('battery_bench_technician') ?? '');
  const [selectedToolIds, setSelectedToolIds] = useState<number[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [skipDialogOpen, setSkipDialogOpen] = useState(false);
  const [skipReason, setSkipReason] = useState('');

  useEffect(() => {
    if (performedBy) {
      localStorage.setItem('battery_bench_technician', performedBy);
    }
  }, [performedBy]);

  if (isLoading) return <LoadingSpinner text="Loading task..." />;
  if (error || !task) return <p className="text-red-600">Failed to load task</p>;

  const measurementKey = (task.params as Record<string, unknown>)?.measurement_key as string
    ?? task.step_type.replace('measure_', '') + (task.step_type.startsWith('measure_') ? '' : '_value');
  const measurementUnit = (task.params as Record<string, unknown>)?.measurement_unit as string | undefined;
  const measurementLabel = (task.params as Record<string, unknown>)?.measurement_label as string | undefined;
  const passCriteriaType = (task.params as Record<string, unknown>)?.pass_criteria_type as string | undefined;
  const passCriteriaValue = (task.params as Record<string, unknown>)?.pass_criteria_value as string | undefined;
  const requiresTools = ((task.params as Record<string, unknown>)?.requires_tools as string[]) ?? [];

  const handleToggleTool = (toolId: number) => {
    setSelectedToolIds(prev =>
      prev.includes(toolId) ? prev.filter(id => id !== toolId) : [...prev, toolId],
    );
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const measured_values: Record<string, unknown> = {};
      if (measuredValue !== '' && measuredValue !== undefined) {
        measured_values[measurementKey] = measuredValue;
      }
      await submitTask(Number(taskId), {
        measured_values,
        step_result: stepResult,
        result_notes: notes,
        performed_by: performedBy,
        tool_ids: selectedToolIds.length > 0 ? selectedToolIds : undefined,
      });
      navigate(`/jobs/${jobId}`);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Submit failed');
      setSubmitting(false);
    }
  };

  const handleSkip = async () => {
    setSubmitting(true);
    try {
      await skipTask(Number(taskId), skipReason);
      navigate(`/jobs/${jobId}`);
    } catch (e) {
      setSubmitError(e instanceof Error ? e.message : 'Skip failed');
      setSubmitting(false);
    }
  };

  return (
    <div>
      <PageHeader
        title={`Task #${task.task_number}: ${task.label}`}
        description={STEP_TYPE_LABELS[task.step_type] ?? task.step_type}
      />

      {task.description && (
        <Card className="mb-4">
          <CardContent className="p-4">
            <p className="text-sm">{task.description}</p>
          </CardContent>
        </Card>
      )}

      <PassCriteriaDisplay
        criteriaType={passCriteriaType}
        criteriaValue={passCriteriaValue}
        measuredValue={measuredValue}
      />

      <div className="space-y-6 mt-4">
        {/* Measurement Input */}
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Measurement</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <MeasurementInput
              stepType={task.step_type}
              measurementKey={measurementKey}
              measurementUnit={measurementUnit}
              measurementLabel={measurementLabel}
              value={measuredValue}
              onChange={setMeasuredValue}
            />
          </CardContent>
        </Card>

        {/* Tool Selector */}
        {requiresTools.length > 0 && (
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm">Tools</CardTitle>
            </CardHeader>
            <CardContent className="px-4 pb-4">
              <ToolSelector
                requiresTools={requiresTools}
                selectedToolIds={selectedToolIds}
                onToggle={handleToggleTool}
              />
            </CardContent>
          </Card>
        )}

        {/* Result & Notes */}
        <Card>
          <CardHeader className="py-3 px-4">
            <CardTitle className="text-sm">Result</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4 space-y-4">
            <div className="space-y-2">
              <Label>Step Result</Label>
              <Select value={stepResult} onValueChange={v => setStepResult(v as StepResult)}>
                <SelectTrigger className="max-w-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pass">Pass</SelectItem>
                  <SelectItem value="fail">Fail</SelectItem>
                  <SelectItem value="info">Info Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Optional notes..."
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Performed By</Label>
              <Input
                value={performedBy}
                onChange={e => setPerformedBy(e.target.value)}
                placeholder="Your name"
                className="max-w-xs"
              />
            </div>
          </CardContent>
        </Card>

        {submitError && <p className="text-sm text-red-600">{submitError}</p>}

        {/* Actions */}
        <div className="flex gap-3">
          <Button onClick={handleSubmit} disabled={submitting || performedBy.trim() === ''} className="flex-1">
            {submitting ? (
              <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Submitting...</>
            ) : (
              <><Send className="h-4 w-4 mr-2" />Submit</>
            )}
          </Button>
          <Button variant="outline" onClick={() => setSkipDialogOpen(true)} disabled={submitting}>
            <SkipForward className="h-4 w-4 mr-1" />Skip
          </Button>
        </div>
      </div>

      {/* Skip Dialog */}
      <Dialog open={skipDialogOpen} onOpenChange={setSkipDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Skip Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Reason for skipping</Label>
            <Textarea
              value={skipReason}
              onChange={e => setSkipReason(e.target.value)}
              placeholder="Enter reason..."
              rows={3}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSkipDialogOpen(false)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={handleSkip}
              disabled={skipReason.trim() === '' || submitting}
            >
              Skip Task
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
