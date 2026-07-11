import { api } from "@/lib/api";
import type { SystemStatus, VersionInfo } from "@/lib/system";

export async function getSystemStatus(): Promise<SystemStatus> {
  const { data } = await api.get<SystemStatus>("/admin/system/status");
  return data;
}

export async function getVersionInfo(): Promise<VersionInfo> {
  const { data } = await api.get<VersionInfo>("/admin/system/version");
  return data;
}
