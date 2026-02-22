import { get } from './client';

export interface SystemInfo {
  version: string;
  hostname: string;
  platform: string;
  python: string;
  stations: number;
  cpu_percent?: number;
  memory_used_mb?: number;
  memory_total_mb?: number;
  memory_percent?: number;
  disk_free_gb?: number;
  disk_total_gb?: number;
  disk_percent?: number;
  cpu_temp_c?: number;
  uptime_s?: number;
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
