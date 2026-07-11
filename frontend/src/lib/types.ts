export type UserRole = "ADMIN" | "USER";

export interface User {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  class_name: string | null;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}
