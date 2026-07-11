import { useQuery } from "@tanstack/react-query";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { listMyJobs } from "@/features/user/api";
import { useAuth } from "@/lib/auth";

const ACTIVE_STATUSES = new Set([
  "SUBMITTED",
  "APPROVED",
  "QUEUED",
  "READY_TO_PRINT",
  "SLICING",
  "SLICED",
  "PRINTING",
  "PAUSED",
]);

export function UserDashboardPage() {
  const { user } = useAuth();
  const { data: jobs } = useQuery({ queryKey: ["user", "jobs"], queryFn: listMyJobs });

  const activeJobs = jobs?.filter((j) => ACTIVE_STATUSES.has(j.status)) ?? [];
  const finishedJobs = jobs?.filter((j) => j.status === "FINISHED") ?? [];
  const nextQueued = jobs
    ?.filter((j) => j.queue_position !== null)
    .sort((a, b) => (a.queue_position ?? 0) - (b.queue_position ?? 0))[0];

  const stats = [
    { label: "Total uploads", value: jobs?.length ?? "—" },
    { label: "Active jobs", value: jobs ? activeJobs.length : "—" },
    { label: "Finished prints", value: jobs ? finishedJobs.length : "—" },
    { label: "Next in queue", value: nextQueued ? `#${nextQueued.queue_position}` : "—" },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Welcome, {user?.display_name}</h1>
        <p className="text-sm text-muted-foreground">Overview of your 3D print jobs.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader>
              <CardDescription>{stat.label}</CardDescription>
              <CardTitle className="text-2xl">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent />
          </Card>
        ))}
      </div>
    </div>
  );
}
