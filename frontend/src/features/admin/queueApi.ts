import { api } from "@/lib/api";
import type { PrintJob } from "@/lib/print-job";

export async function getQueue(): Promise<PrintJob[]> {
  const { data } = await api.get<PrintJob[]>("/admin/queue");
  return data;
}

export async function reorderQueue(orderedJobIds: string[]): Promise<PrintJob[]> {
  const { data } = await api.post<PrintJob[]>("/admin/queue/reorder", {
    ordered_job_ids: orderedJobIds,
  });
  return data;
}

export async function moveJobUp(jobId: string): Promise<PrintJob[]> {
  const { data } = await api.post<PrintJob[]>(`/admin/queue/${jobId}/move-up`);
  return data;
}

export async function moveJobDown(jobId: string): Promise<PrintJob[]> {
  const { data } = await api.post<PrintJob[]>(`/admin/queue/${jobId}/move-down`);
  return data;
}

export async function sliceJob(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/slice`);
  return data;
}

export async function enqueueJob(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/enqueue`);
  return data;
}

export async function removeFromQueue(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/remove-from-queue`);
  return data;
}
