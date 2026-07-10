import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboardIcon,
  UploadIcon,
  ListChecksIcon,
  UsersIcon,
  ClipboardCheckIcon,
  ListOrderedIcon,
  PrinterIcon,
  SettingsIcon,
  ActivityIcon,
  DownloadIcon,
  LogOutIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const userNavItems: NavItem[] = [
  { to: "/user", label: "Dashboard", icon: LayoutDashboardIcon },
  { to: "/user/upload", label: "Upload", icon: UploadIcon },
  { to: "/user/jobs", label: "My Jobs", icon: ListChecksIcon },
];

const adminNavItems: NavItem[] = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboardIcon },
  { to: "/admin/users", label: "Users", icon: UsersIcon },
  { to: "/admin/jobs", label: "Job Requests", icon: ClipboardCheckIcon },
  { to: "/admin/queue", label: "Queue", icon: ListOrderedIcon },
  { to: "/admin/printers", label: "Printers", icon: PrinterIcon },
  { to: "/admin/system", label: "System", icon: ActivityIcon },
  { to: "/admin/settings", label: "Settings", icon: SettingsIcon },
  { to: "/admin/updates", label: "Updates", icon: DownloadIcon },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const navItems = user?.role === "ADMIN" ? adminNavItems : userNavItems;

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r bg-card">
        <div className="border-b px-4 py-4">
          <p className="text-sm font-semibold">SchoolPrint</p>
          <p className="text-xs text-muted-foreground">3D-Druck-Verwaltung</p>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                  isActive && "bg-accent text-accent-foreground",
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3">
          <div className="mb-2 text-xs text-muted-foreground">
            <p className="font-medium text-foreground">{user?.display_name}</p>
            <p>{user?.role}</p>
          </div>
          <Button variant="outline" size="sm" className="w-full" onClick={() => logout()}>
            <LogOutIcon /> Logout
          </Button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
