export interface RetentionSettings {
  retention_days_finished: number;
  retention_days_rejected: number;
  retention_days_failed: number;
}

export interface RetentionRunResult {
  deleted_job_count: number;
  bytes_freed: number;
}

export interface StorageOverview {
  disk_total_bytes: number;
  disk_used_bytes: number;
  disk_free_bytes: number;
  uploads_bytes: number;
  sliced_bytes: number;
  active_uploaded_files: number;
  jobs_pending_retention: number;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const exponent = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)));
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}
