import { useReducer, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { useApiQuery } from '@/hooks/useApiQuery';
import { getWorkOrder } from '@/api/workOrders';
import { StepSelectItem } from '@/components/job/StepSelectItem';
import { StepSelectStation } from '@/components/job/StepSelectStation';
import { StepServiceConfig } from '@/components/job/StepServiceConfig';
import { StepProcedurePreview } from '@/components/job/StepProcedurePreview';
import { StepConfirmStart } from '@/components/job/StepConfirmStart';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { ResolvedProcedure } from '@/types';

const STEPS = ['Battery', 'Station', 'Service Config', 'Preview', 'Confirm'];

interface WizardState {
  step: number;
  stationId: number | null;
  serviceType: string;
  monthsSinceService: number;
  startedBy: string;
  procedure: ResolvedProcedure | null;
}

type Action =
  | { type: 'SET_STEP'; step: number }
  | { type: 'SET_STATION'; stationId: number }
  | { type: 'SET_SERVICE'; serviceType: string; monthsSinceService: number }
  | { type: 'SET_STARTED_BY'; startedBy: string }
  | { type: 'SET_PROCEDURE'; procedure: ResolvedProcedure };

function reducer(state: WizardState, action: Action): WizardState {
  switch (action.type) {
    case 'SET_STEP': return { ...state, step: action.step };
    case 'SET_STATION': return { ...state, stationId: action.stationId };
    case 'SET_SERVICE': return { ...state, serviceType: action.serviceType, monthsSinceService: action.monthsSinceService };
    case 'SET_STARTED_BY': return { ...state, startedBy: action.startedBy };
    case 'SET_PROCEDURE': return { ...state, procedure: action.procedure };
    default: return state;
  }
}

export default function JobStart() {
  const { woId, itemId } = useParams<{ woId: string; itemId: string }>();
  const navigate = useNavigate();
  const { data: wo, isLoading, error } = useApiQuery(() => getWorkOrder(Number(woId)), [woId]);

  const savedBy = localStorage.getItem('battery_bench_technician') ?? '';

  const [state, dispatch] = useReducer(reducer, {
    step: 0,
    stationId: null,
    serviceType: 'capacity_test',
    monthsSinceService: 0,
    startedBy: savedBy,
    procedure: null,
  });

  const item = wo?.items?.find(i => i.id === Number(itemId));

  useEffect(() => {
    if (state.startedBy) {
      localStorage.setItem('battery_bench_technician', state.startedBy);
    }
  }, [state.startedBy]);

  if (isLoading) return <LoadingSpinner text="Loading work order..." />;
  if (error || !wo) return <p className="text-red-600">Failed to load work order</p>;
  if (!item) return <p className="text-red-600">Battery item not found</p>;

  const canNext = () => {
    switch (state.step) {
      case 0: return true;
      case 1: return state.stationId !== null;
      case 2: return state.serviceType !== '' && state.startedBy.trim() !== '';
      case 3: return state.procedure !== null;
      case 4: return true;
      default: return false;
    }
  };

  return (
    <div>
      <PageHeader
        title="Start Job"
        description={`${wo.work_order_number} — ${item.serial_number}`}
      />

      {/* Stepper */}
      <div className="flex items-center gap-1 mb-6">
        {STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-1">
            <div
              className={`flex items-center justify-center h-7 w-7 rounded-full text-xs font-medium transition-colors ${
                i === state.step
                  ? 'bg-primary text-primary-foreground'
                  : i < state.step
                    ? 'bg-green-600 text-white'
                    : 'bg-muted text-muted-foreground'
              }`}
            >
              {i < state.step ? '✓' : i + 1}
            </div>
            <span className={`text-xs ${i === state.step ? 'text-foreground font-medium' : 'text-muted-foreground'}`}>
              {label}
            </span>
            {i < STEPS.length - 1 && <div className="w-8 h-px bg-border mx-1" />}
          </div>
        ))}
      </div>

      {/* Step content */}
      <div className="mb-6">
        {state.step === 0 && <StepSelectItem item={item} wo={wo} />}
        {state.step === 1 && (
          <StepSelectStation
            selectedId={state.stationId}
            onSelect={id => dispatch({ type: 'SET_STATION', stationId: id })}
          />
        )}
        {state.step === 2 && (
          <StepServiceConfig
            serviceType={state.serviceType}
            monthsSinceService={state.monthsSinceService}
            startedBy={state.startedBy}
            onServiceTypeChange={v => dispatch({ type: 'SET_SERVICE', serviceType: v, monthsSinceService: state.monthsSinceService })}
            onMonthsChange={v => dispatch({ type: 'SET_SERVICE', serviceType: state.serviceType, monthsSinceService: v })}
            onStartedByChange={v => dispatch({ type: 'SET_STARTED_BY', startedBy: v })}
          />
        )}
        {state.step === 3 && (
          <StepProcedurePreview
            itemId={Number(itemId)}
            serviceType={state.serviceType}
            monthsSinceService={state.monthsSinceService}
            onLoaded={proc => dispatch({ type: 'SET_PROCEDURE', procedure: proc })}
          />
        )}
        {state.step === 4 && (
          <StepConfirmStart
            item={item}
            wo={wo}
            stationId={state.stationId!}
            serviceType={state.serviceType}
            monthsSinceService={state.monthsSinceService}
            startedBy={state.startedBy}
            procedure={state.procedure!}
            onSuccess={(jobId) => navigate(`/jobs/${jobId}`)}
          />
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => dispatch({ type: 'SET_STEP', step: state.step - 1 })}
          disabled={state.step === 0}
        >
          <ChevronLeft className="h-4 w-4 mr-1" />Back
        </Button>
        {state.step < 4 && (
          <Button
            onClick={() => dispatch({ type: 'SET_STEP', step: state.step + 1 })}
            disabled={!canNext()}
          >
            Next<ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>
    </div>
  );
}
