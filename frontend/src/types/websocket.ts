import type { StationStatus } from './station';
import type { JobTask } from './jobTask';

export interface WsStationUpdate {
  type: 'update';
  data: StationStatus[];
}

export interface WsInitial {
  type: 'initial';
  data: StationStatus[];
}

export interface WsTaskAwaiting {
  type: 'task_awaiting_input';
  station_id: number;
  task: Pick<JobTask, 'id' | 'task_number' | 'label' | 'step_type' | 'status' | 'params'> & {
    measurement_key?: string;
    measurement_unit?: string;
  };
}

export type WsMessage = WsStationUpdate | WsInitial | WsTaskAwaiting;
