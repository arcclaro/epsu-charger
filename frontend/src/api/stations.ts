import { get, post } from './client';
import type { StationStatus, ControlCommand, DiagnosticsReport } from '@/types';

export function getStations(): Promise<StationStatus[]> {
  return get('/stations');
}

export function getStation(id: number): Promise<StationStatus> {
  return get(`/stations/${id}`);
}

export function sendControl(cmd: ControlCommand): Promise<{ status: string; message: string }> {
  return post('/stations/control', cmd);
}

export function getStationDiagnostics(id: number): Promise<DiagnosticsReport> {
  return get(`/stations/${id}/diagnostics`);
}

export function stopStation(id: number): Promise<{ status: string }> {
  return post(`/stations/${id}/stop`);
}

export function resetStation(id: number): Promise<{ status: string }> {
  return post(`/stations/${id}/reset`);
}

export function getStationEeprom(id: number): Promise<unknown> {
  return get(`/stations/${id}/eeprom`);
}
