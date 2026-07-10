import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/AppLayout";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth";
import { AdminDashboardPage } from "@/features/admin/DashboardPage";
import { AdminJobsPage } from "@/features/admin/JobsPage";
import { AdminPrintersPage } from "@/features/admin/PrintersPage";
import { AdminQueuePage } from "@/features/admin/QueuePage";
import { AdminSettingsPage } from "@/features/admin/SettingsPage";
import { AdminSystemPage } from "@/features/admin/SystemPage";
import { AdminUpdatesPage } from "@/features/admin/UpdatesPage";
import { AdminUsersPage } from "@/features/admin/UsersPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { UserDashboardPage } from "@/features/user/DashboardPage";
import { JobDetailPage } from "@/features/user/JobDetailPage";
import { JobsPage } from "@/features/user/JobsPage";
import { UploadPage } from "@/features/user/UploadPage";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute requiredRole="USER" />}>
        <Route element={<AppLayout />}>
          <Route path="/user" element={<UserDashboardPage />} />
          <Route path="/user/upload" element={<UploadPage />} />
          <Route path="/user/jobs" element={<JobsPage />} />
          <Route path="/user/jobs/:jobId" element={<JobDetailPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute requiredRole="ADMIN" />}>
        <Route element={<AppLayout />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/jobs" element={<AdminJobsPage />} />
          <Route path="/admin/queue" element={<AdminQueuePage />} />
          <Route path="/admin/printers" element={<AdminPrintersPage />} />
          <Route path="/admin/settings" element={<AdminSettingsPage />} />
          <Route path="/admin/system" element={<AdminSystemPage />} />
          <Route path="/admin/updates" element={<AdminUpdatesPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<RoleHomeRedirect />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function RoleHomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user?.role === "ADMIN" ? "/admin" : "/user"} replace />;
}
