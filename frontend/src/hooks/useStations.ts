import { createContext, useContext } from 'react';
import type { StationStatus } from '@/types';

export interface StationContextValue {
  stations: StationStatus[];
  awaitingTasks: Map<number, { id: number; task_number: number; label: string; step_type: string }>;
  connected: boolean;
}

export const StationContext = createContext<StationContextValue>({
  stations: [],
  awaitingTasks: new Map(),
  connected: false,
});

export function useStations() {
  return useContext(StationContext);
}
