import { get, put } from './client';

export interface StationVerification {
  station_id: number;
  psu_last_cal?: string;
  psu_next_cal?: string;
  psu_cal_status?: string;
  dc_load_last_cal?: string;
  dc_load_next_cal?: string;
  dc_load_cal_status?: string;
  [key: string]: unknown;
}

export function getStationVerifications(): Promise<StationVerification[]> {
  return get('/station-calibration');
}

export function getStationVerification(stationId: number): Promise<StationVerification> {
  return get(`/station-calibration/${stationId}`);
}

export function getPsuVerificationProcedure(): Promise<unknown[]> {
  return get('/station-calibration/procedures/psu');
}

export function getDcLoadVerificationProcedure(): Promise<unknown[]> {
  return get('/station-calibration/procedures/dc-load');
}

export function updateStationVerification(
  stationId: number,
  unit: string,
  data: Record<string, unknown>,
): Promise<StationVerification> {
  return put(`/station-calibration/${stationId}/${unit}`, data);
}
