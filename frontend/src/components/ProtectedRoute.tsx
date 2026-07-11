import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/lib/auth";
import type { UserRole } from "@/lib/types";

export function ProtectedRoute({ requiredRole }: { requiredRole?: UserRole }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-full min-h-[50vh] items-center justify-center text-muted-foreground">
        Loading...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
