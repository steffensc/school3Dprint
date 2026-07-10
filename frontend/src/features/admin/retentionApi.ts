import { api } from "@/lib/api";
import type { RetentionRunResult, RetentionSettings, StorageOverview } from "@/lib/retention";

export async function getRetentionSettings(): Promise<RetentionSettings> {
  const { data } = await api.get<RetentionSettings>("/admin/settings/retention");
  return data;
}

export async function updateRetentionSettings(
  payload: Partial<RetentionSettings>,
): Promise<RetentionSettings> {
  const { data } = await api.put<RetentionSettings>("/admin/settings/retention", payload);
  return data;
}

export async function runRetentionNow(): Promise<RetentionRunResult> {
  const { data } = await api.post<RetentionRunResult>("/admin/retention/run");
  return data;
}

export async function getStorageOverview(): Promise<StorageOverview> {
  const { data } = await api.get<StorageOverview>("/admin/storage/overview");
  return data;
}
