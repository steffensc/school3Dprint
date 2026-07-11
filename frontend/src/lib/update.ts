export interface UpdateCheckResult {
  current_version: string;
  latest_version: string | null;
  update_available: boolean;
  release_url: string | null;
  release_notes: string | null;
  published_at: string | null;
  checked_at: string;
  error: string | null;
}

export type UpdateRunStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export const updateRunStatusLabels: Record<UpdateRunStatus, string> = {
  PENDING: "Pending",
  RUNNING: "Running",
  SUCCEEDED: "Succeeded",
  FAILED: "Failed",
};

export interface UpdateRun {
  id: string;
  status: UpdateRunStatus;
  from_version: string;
  to_version: string | null;
  log: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}
