export interface SystemStatus {
  cpu_percent: number;
  ram_total_bytes: number;
  ram_used_bytes: number;
  ram_percent: number;
  disk_total_bytes: number;
  disk_used_bytes: number;
  disk_free_bytes: number;
  uploads_bytes: number;
  sliced_bytes: number;
  uptime_seconds: number;
}

export interface VersionInfo {
  backend_version: string;
  frontend_version: string;
  container_version: string;
  git_commit: string | null;
  environment: string;
}

export function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}
