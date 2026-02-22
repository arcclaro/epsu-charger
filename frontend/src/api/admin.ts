import { get } from './client';

export interface SystemInfo {
  version: string;
  hostname: string;
  uptime: number;
  [key: string]: unknown;
}

export interface HealthCheck {
  status: string;
  database: string;
  influxdb: string;
  [key: string]: unknown;
}

export function getSystemInfo(): Promise<SystemInfo> {
  return get('/system/info');
}

export function getHealthCheck(): Promise<HealthCheck> {
  return get('/system/health');
}
