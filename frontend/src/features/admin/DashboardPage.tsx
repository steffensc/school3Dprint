import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listUsers } from "@/features/admin/api";

export function AdminDashboardPage() {
  const { data: users } = useQuery({ queryKey: ["admin", "users"], queryFn: listUsers });

  const tiles = [
    { label: "Total users", value: users?.length ?? "—" },
    { label: "Open approvals", value: "—" },
    { label: "Queue length", value: "—" },
    { label: "Active prints", value: "—" },
    { label: "Printers online", value: "—" },
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
