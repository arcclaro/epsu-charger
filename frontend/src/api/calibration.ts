import { get, put } from './client';

export interface StationCalibration {
  station_id: number;
  psu_last_cal?: string;
  psu_next_cal?: string;
  psu_cal_status?: string;
  dc_load_last_cal?: string;
  dc_load_next_cal?: string;
  dc_load_cal_status?: string;
  [key: string]: unknown;
}

export function getStationCalibrations(): Promise<StationCalibration[]> {
  return get('/station-calibration');
}

export function getStationCalibration(stationId: number): Promise<StationCalibration> {
  return get(`/station-calibration/${stationId}`);
}

export function getPsuCalProcedure(): Promise<unknown[]> {
  return get('/station-calibration/procedures/psu');
}

export function getDcLoadCalProcedure(): Promise<unknown[]> {
  return get('/station-calibration/procedures/dc-load');
}

export function updateStationCalibration(
  stationId: number,
  unit: string,
  data: Record<string, unknown>,
): Promise<StationCalibration> {
  return put(`/station-calibration/${stationId}/${unit}`, data);
}
