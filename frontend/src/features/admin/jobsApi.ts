import { api } from "@/lib/api";
import type { PrintJob } from "@/lib/print-job";

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
