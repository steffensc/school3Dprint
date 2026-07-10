export type PrintJobStatus =
  | "SUBMITTED"
  | "REJECTED"
  | "APPROVED"
  | "QUEUED"
  | "READY_TO_PRINT"
  | "SLICING"
  | "SLICED"
  | "PRINTING"
  | "PAUSED"
  | "FINISHED"
  | "FAILED"
  | "CANCELLED"
  | "EXPIRED"
  | "DELETED";

export interface UploadedFileOut {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  sha256: string;
  created_at: string;
}

export interface PrintJobOwnerOut {
  id: string;
  username: string;
  display_name: string;
  class_name: string | null;
}

export interface PrintJob {
  id: string;
  title: string;
  status: PrintJobStatus;
  queue_position: number | null;
  student_note: string | null;
  teacher_note: string | null;
  estimated_print_time_seconds: number | null;
  estimated_filament_grams: number | null;
  created_at: string;
  approved_at: string | null;
  rejected_at: string | null;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  failed_at: string | null;
  expires_at: string | null;
  uploaded_file: UploadedFileOut;
  owner?: PrintJobOwnerOut | null;
}

export const statusLabels: Record<PrintJobStatus, string> = {
  SUBMITTED: "Submitted",
  REJECTED: "Rejected",
  APPROVED: "Approved",
  QUEUED: "In queue",
  READY_TO_PRINT: "Ready to print",
  SLICING: "Slicing",
  SLICED: "Sliced",
  PRINTING: "Printing",
  PAUSED: "Paused",
  FINISHED: "Finished",
  FAILED: "Failed",
  CANCELLED: "Cancelled",
  EXPIRED: "Expired",
  DELETED: "Deleted",
};

export const statusBadgeVariant: Record<
  PrintJobStatus,
  "default" | "secondary" | "destructive" | "success" | "warning" | "outline"
> = {
  SUBMITTED: "secondary",
  REJECTED: "destructive",
  APPROVED: "default",
  QUEUED: "default",
  READY_TO_PRINT: "default",
  SLICING: "warning",
  SLICED: "default",
  PRINTING: "warning",
  PAUSED: "warning",
  FINISHED: "success",
  FAILED: "destructive",
  CANCELLED: "outline",
  EXPIRED: "outline",
  DELETED: "outline",
};
