import { Badge } from '@/components/ui/badge';

interface Props {
  criteriaType?: string;
  criteriaValue?: string;
  measuredValue?: unknown;
}

export function PassCriteriaDisplay({ criteriaType, criteriaValue, measuredValue }: Props) {
  if (!criteriaType || criteriaType === 'none') return null;

  const parseRange = (val: string) => {
    try { return JSON.parse(val); } catch { return null; }
  };

  let description = '';
  let suggestion: 'pass' | 'fail' | null = null;
  const num = typeof measuredValue === 'number' ? measuredValue : null;

  switch (criteriaType) {
    case 'min_value': {
      description = `Minimum: ${criteriaValue}`;
      if (num !== null && criteriaValue) suggestion = num >= Number(criteriaValue) ? 'pass' : 'fail';
      break;
    }
    case 'max_value': {
      description = `Maximum: ${criteriaValue}`;
      if (num !== null && criteriaValue) suggestion = num <= Number(criteriaValue) ? 'pass' : 'fail';
      break;
    }
    case 'range': {
      const range = parseRange(criteriaValue ?? '');
      if (range) {
        description = `Range: ${range.min ?? '?'} – ${range.max ?? '?'}`;
        if (num !== null) {
          suggestion = (range.min == null || num >= range.min) && (range.max == null || num <= range.max) ? 'pass' : 'fail';
        }
      }
      break;
    }
    case 'boolean': {
      description = `Expected: ${criteriaValue}`;
      break;
    }
    case 'expression': {
      description = `Expression: ${criteriaValue}`;
      break;
    }
    default:
      description = `${criteriaType}: ${criteriaValue}`;
  }

  return (
    <div className="flex items-center gap-3 p-2 rounded bg-muted/50 text-sm">
      <span className="text-muted-foreground">Pass criteria:</span>
      <span>{description}</span>
      {suggestion && (
        <Badge className={`${suggestion === 'pass' ? 'bg-green-600' : 'bg-red-600'} text-white text-xs`}>
          Suggests: {suggestion}
        </Badge>
      )}
    </div>
  );
}
