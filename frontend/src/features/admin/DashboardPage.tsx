import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listUsers } from "@/features/admin/api";
import { listAllJobs } from "@/features/admin/jobsApi";
import { listPrinters } from "@/features/admin/printersApi";

export function AdminDashboardPage() {
  const { data: users } = useQuery({ queryKey: ["admin", "users"], queryFn: listUsers });
  const { data: jobs } = useQuery({ queryKey: ["admin", "jobs"], queryFn: listAllJobs });
  const { data: printers } = useQuery({ queryKey: ["admin", "printers"], queryFn: listPrinters });

  const openApprovals = jobs?.filter((j) => j.status === "SUBMITTED").length;
  const queueLength = jobs?.filter((j) => j.queue_position !== null).length;
  const activePrints = jobs?.filter((j) => j.status === "PRINTING").length;
  const activePrinters = printers?.filter((p) => p.is_active).length;

  const tiles = [
    { label: "Total users", value: users?.length ?? "—" },
    { label: "Open approvals", value: openApprovals ?? "—" },
    { label: "Queue length", value: queueLength ?? "—" },
    { label: "Active prints", value: activePrints ?? "—" },
    { label: "Printers configured", value: activePrinters ?? "—" },
    { label: "Storage used", value: "—" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Admin Dashboard</h1>
        <p className="text-sm text-muted-foreground">System overview for SchoolPrint.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tiles.map((tile) => (
          <Card key={tile.label}>
            <CardHeader>
              <CardDescription>{tile.label}</CardDescription>
              <CardTitle className="text-2xl">{tile.value}</CardTitle>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </div>
    </div>
  );
}
