import { useQuery } from "@tanstack/react-query";

import { Progress } from "@/components/ui/progress";
import type { PrintJobLiveStatus } from "@/lib/print-job";

export function PrintJobLiveProgress({
  jobId,
  queryKeyPrefix,
  fetchLiveStatus,
}: {
  jobId: string;
  queryKeyPrefix: string;
  fetchLiveStatus: (jobId: string) => Promise<PrintJobLiveStatus>;
}) {
  const { data } = useQuery({
    queryKey: [queryKeyPrefix, "live-status", jobId],
    queryFn: () => fetchLiveStatus(jobId),
    refetchInterval: 2000,
  });

  if (!data) {
    return null;
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>{data.progress.toFixed(0)}% complete</span>
        {data.nozzle_actual != null && data.bed_actual != null && (
          <span>
            Nozzle {data.nozzle_actual.toFixed(0)}°C / {data.nozzle_target?.toFixed(0) ?? 0}°C ·
            Bed {data.bed_actual.toFixed(0)}°C / {data.bed_target?.toFixed(0) ?? 0}°C
          </span>
        )}
      </div>
      <Progress value={data.progress} />
    </div>
  );
}
