import { get, post } from './client';
import type { JobTask, ManualResultSubmit, StartJobRequest, StartJobResponse, Tool } from '@/types';

export function startJob(req: StartJobRequest): Promise<StartJobResponse> {
  return post('/job-tasks/start-job', req);
}

export function getJobTasks(jobId: number): Promise<JobTask[]> {
  return get(`/job-tasks/job/${jobId}`);
}

export function getTask(taskId: number): Promise<JobTask> {
  return get(`/job-tasks/${taskId}`);
}

export function submitTask(taskId: number, data: ManualResultSubmit): Promise<{ success: boolean; message: string }> {
  return post(`/job-tasks/${taskId}/submit`, data);
}

export function skipTask(taskId: number, reason: string): Promise<{ success: boolean; message: string }> {
  return post(`/job-tasks/${taskId}/skip`, { reason });
}

export function getAwaitingInput(stationId: number): Promise<JobTask[]> {
  return get(`/job-tasks/awaiting-input/${stationId}`);
}

export function getAvailableTools(category?: string): Promise<Tool[]> {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  return get(`/job-tasks/tools/available${params}`);
}
