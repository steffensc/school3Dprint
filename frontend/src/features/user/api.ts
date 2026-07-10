import { api } from "@/lib/api";
import type { PrintJob, PrintJobLiveStatus } from "@/lib/print-job";

export async function listMyJobs(): Promise<PrintJob[]> {
  const { data } = await api.get<PrintJob[]>("/user/jobs");
  return data;
}

export async function getMyJob(jobId: string): Promise<PrintJob> {
  const { data } = await api.get<PrintJob>(`/user/jobs/${jobId}`);
  return data;
}

export async function getMyJobLiveStatus(jobId: string): Promise<PrintJobLiveStatus> {
  const { data } = await api.get<PrintJobLiveStatus>(`/user/jobs/${jobId}/live-status`);
  return data;
}

export interface CreateUploadPayload {
  title: string;
  studentNote?: string;
  file: File;
}

export async function createUpload(payload: CreateUploadPayload): Promise<PrintJob> {
  const formData = new FormData();
  formData.append("title", payload.title);
  if (payload.studentNote) {
    formData.append("student_note", payload.studentNote);
  }
  formData.append("file", payload.file);

  const { data } = await api.post<PrintJob>("/user/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
