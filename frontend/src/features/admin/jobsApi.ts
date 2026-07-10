import { api } from "@/lib/api";
import type { PrintJob, PrintJobLiveStatus } from "@/lib/print-job";

export async function listAllJobs(): Promise<PrintJob[]> {
  const { data } = await api.get<PrintJob[]>("/admin/jobs");
  return data;
}

export async function approveJob(jobId: string, teacherNote?: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/approve`, {
    teacher_note: teacherNote,
  });
  return data;
}

export async function rejectJob(jobId: string, teacherNote?: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/reject`, {
    teacher_note: teacherNote,
  });
  return data;
}

export async function unapproveJob(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/unapprove`);
  return data;
}

export async function startPrint(jobId: string, printerId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/start-print`, {
    printer_id: printerId,
  });
  return data;
}

export async function pausePrint(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/pause-print`);
  return data;
}

export async function resumePrint(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/resume-print`);
  return data;
}

export async function cancelPrint(jobId: string): Promise<PrintJob> {
  const { data } = await api.post<PrintJob>(`/admin/jobs/${jobId}/cancel-print`);
  return data;
}

export async function getJobLiveStatus(jobId: string): Promise<PrintJobLiveStatus> {
  const { data } = await api.get<PrintJobLiveStatus>(`/admin/jobs/${jobId}/live-status`);
  return data;
}
