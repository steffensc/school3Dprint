import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { getSystemStatus, getVersionInfo } from "@/features/admin/systemApi";
import { formatBytes } from "@/lib/retention";
import { formatUptime } from "@/lib/system";

export function AdminSystemPage() {
  const { data: status } = useQuery({
    queryKey: ["admin", "system", "status"],
    queryFn: getSystemStatus,
    refetchInterval: 5000,
  });
  const { data: version } = useQuery({
    queryKey: ["admin", "system", "version"],
    queryFn: getVersionInfo,
    staleTime: Infinity,
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">System status</h1>
        <p className="text-sm text-muted-foreground">
          Live host metrics for the Raspberry Pi (or other host) running SchoolPrint.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>CPU</CardTitle>
            <CardDescription>Current CPU utilisation.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-sm">
              <span>{status ? `${status.cpu_percent.toFixed(0)}%` : "—"}</span>
            </div>
            <Progress value={status?.cpu_percent ?? 0} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>RAM</CardTitle>
            <CardDescription>Current memory usage.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-sm">
              <span>
                {status
                  ? `${formatBytes(status.ram_used_bytes)} of ${formatBytes(status.ram_total_bytes)}`
                  : "—"}
              </span>
              <span className="text-muted-foreground">
                {status ? `${status.ram_percent.toFixed(0)}%` : ""}
              </span>
            </div>
            <Progress value={status?.ram_percent ?? 0} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Disk</CardTitle>
            <CardDescription>Storage volume used by the whole host.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between text-sm">
              <span>
                {status
                  ? `${formatBytes(status.disk_used_bytes)} of ${formatBytes(status.disk_total_bytes)}`
                  : "—"}
              </span>
              <span className="text-muted-foreground">
                {status ? `${formatBytes(status.disk_free_bytes)} free` : ""}
              </span>
            </div>
            <Progress
              value={
                status
                  ? (status.disk_used_bytes / Math.max(1, status.disk_total_bytes)) * 100
                  : 0
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SchoolPrint storage</CardTitle>
            <CardDescription>Uploads + sliced artifacts, and uptime.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-3 gap-4">
            <StatTile label="Uploads" value={status ? formatBytes(status.uploads_bytes) : "—"} />
            <StatTile
              label="Sliced artifacts"
              value={status ? formatBytes(status.sliced_bytes) : "—"}
            />
            <StatTile
              label="Backend uptime"
              value={status ? formatUptime(status.uptime_seconds) : "—"}
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Version</CardTitle>
          <CardDescription>Container, backend and frontend versions currently running.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatTile label="Container" value={version?.container_version ?? "—"} />
          <StatTile label="Backend" value={version?.backend_version ?? "—"} />
          <StatTile label="Frontend" value={version?.frontend_version ?? "—"} />
          <StatTile label="Git commit" value={version?.git_commit ?? "n/a"} />
        </CardContent>
      </Card>
    </div>
  );
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}
