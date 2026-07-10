import { api } from "@/lib/api";
import type { UpdateCheckResult, UpdateRun } from "@/lib/update";

export async function checkForUpdate(): Promise<UpdateCheckResult> {
  const { data } = await api.get<UpdateCheckResult>("/admin/updates/check");
  return data;
}

export async function installUpdate(): Promise<UpdateRun> {
  const { data } = await api.post<UpdateRun>("/admin/updates/install");
  return data;
}

export async function getUpdateStatus(): Promise<UpdateRun | null> {
  const { data } = await api.get<UpdateRun | null>("/admin/updates/status");
  return data;
}
