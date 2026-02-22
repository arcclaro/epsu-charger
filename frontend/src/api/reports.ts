import { get, post, del } from './client';

export function generateReport(sessionId: number): Promise<{ success: boolean; message: string; session_id: number }> {
  return post(`/reports/${sessionId}/generate`);
}

export function getReportStatus(sessionId: number): Promise<{ exists: boolean; size_bytes?: number; modified_at?: string }> {
  return get(`/reports/${sessionId}/status`);
}

export function deleteReport(sessionId: number): Promise<{ success: boolean; message: string }> {
  return del(`/reports/${sessionId}`);
}

export function getReportDownloadUrl(sessionId: number): string {
  return `/api/reports/${sessionId}/download`;
}
