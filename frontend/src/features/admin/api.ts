import { api } from "@/lib/api";
import type { User, UserRole } from "@/lib/types";

export interface CreateUserPayload {
  username: string;
  display_name: string;
  password: string;
  role: UserRole;
  class_name?: string | null;
}

export interface UpdateUserPayload {
  display_name?: string;
  role?: UserRole;
  class_name?: string | null;
  is_active?: boolean;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await api.get<User[]>("/admin/users");
  return data;
}

export async function createUser(payload: CreateUserPayload): Promise<User> {
  const { data } = await api.post<User>("/admin/users", payload);
  return data;
}

export async function updateUser(userId: string, payload: UpdateUserPayload): Promise<User> {
  const { data } = await api.patch<User>(`/admin/users/${userId}`, payload);
  return data;
}

export async function resetUserPassword(userId: string, newPassword: string): Promise<User> {
  const { data } = await api.post<User>(`/admin/users/${userId}/reset-password`, {
    new_password: newPassword,
  });
  return data;
}

export async function setUserActive(userId: string, isActive: boolean): Promise<User> {
  const { data } = await api.post<User>(`/admin/users/${userId}/${isActive ? "enable" : "disable"}`);
  return data;
}
