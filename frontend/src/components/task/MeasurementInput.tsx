import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import type { StepType } from '@/types';

interface Props {
  stepType: StepType;
  measurementKey?: string;
  measurementUnit?: string;
  measurementLabel?: string;
  value: unknown;
  onChange: (value: unknown) => void;
}

const inputConfig: Record<string, { type: 'number'; step: string; unit: string } | { type: 'textarea' } | { type: 'checkbox' }> = {
  measure_resistance: { type: 'number', step: '0.01', unit: 'MOhm' },
  measure_voltage: { type: 'number', step: '0.001', unit: 'V' },
  measure_weight: { type: 'number', step: '0.01', unit: 'kg' },
  measure_temperature: { type: 'number', step: '0.1', unit: '°C' },
  visual_check: { type: 'textarea' },
  functional_check: { type: 'textarea' },
  operator_action: { type: 'checkbox' },
};

export function MeasurementInput({ stepType, measurementKey, measurementUnit, measurementLabel, value, onChange }: Props) {
  const config = inputConfig[stepType];

  if (!config) {
    // record_value or evaluate_result — generic number input
    if (stepType === 'record_value') {
      return (
        <div className="space-y-2">
          <Label>{measurementLabel ?? measurementKey ?? 'Value'}</Label>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              step="0.001"
              value={value as string ?? ''}
              onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))}
              className="max-w-xs"
            />
            {measurementUnit && <span className="text-sm text-muted-foreground">{measurementUnit}</span>}
          </div>
        </div>
      );
    }
    if (stepType === 'evaluate_result') {
      return (
        <div className="space-y-2">
          <Label>Evaluation</Label>
          <p className="text-sm text-muted-foreground">Review the results and select pass/fail below.</p>
        </div>
      );
    }
    return null;
  }

  if (config.type === 'number') {
    return (
      <div className="space-y-2">
        <Label>{measurementLabel ?? measurementKey ?? 'Measurement'}</Label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            step={config.step}
            value={value as string ?? ''}
            onChange={e => onChange(e.target.value === '' ? '' : Number(e.target.value))}
            className="max-w-xs"
            autoFocus
          />
          <span className="text-sm text-muted-foreground">{measurementUnit ?? config.unit}</span>
        </div>
      </div>
    );
  }

  if (config.type === 'textarea') {
    return (
      <div className="space-y-2">
        <Label>{stepType === 'visual_check' ? 'Visual Inspection Notes' : 'Functional Check Notes'}</Label>
        <Textarea
          value={value as string ?? ''}
          onChange={e => onChange(e.target.value)}
          placeholder="Enter observations..."
          rows={3}
        />
      </div>
    );
  }

  if (config.type === 'checkbox') {
    return (
      <div className="flex items-center gap-3 py-2">
        <Switch
          checked={value as boolean ?? false}
          onCheckedChange={onChange}
        />
        <Label>Action completed</Label>
      </div>
    );
  }

  return null;
}
