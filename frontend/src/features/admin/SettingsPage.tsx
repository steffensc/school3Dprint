import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlayIcon, SaveIcon, Trash2Icon } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  getRetentionSettings,
  getStorageOverview,
  runRetentionNow,
  updateRetentionSettings,
} from "@/features/admin/retentionApi";
import { formatBytes } from "@/lib/retention";

export function AdminSettingsPage() {
  const queryClient = useQueryClient();
  const { data: retention, isLoading: retentionLoading } = useQuery({
    queryKey: ["admin", "settings", "retention"],
    queryFn: getRetentionSettings,
  });
  const { data: storage } = useQuery({
    queryKey: ["admin", "storage", "overview"],
    queryFn: getStorageOverview,
  });

  const [finishedDays, setFinishedDays] = React.useState("");
  const [rejectedDays, setRejectedDays] = React.useState("");
  const [failedDays, setFailedDays] = React.useState("");

  React.useEffect(() => {
    if (retention) {
      setFinishedDays(String(retention.retention_days_finished));
      setRejectedDays(String(retention.retention_days_rejected));
      setFailedDays(String(retention.retention_days_failed));
    }
  }, [retention]);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin", "settings", "retention"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "storage", "overview"] });
  };

  const saveMutation = useMutation({
    mutationFn: () =>
      updateRetentionSettings({
        retention_days_finished: Number(finishedDays),
        retention_days_rejected: Number(rejectedDays),
        retention_days_failed: Number(failedDays),
      }),
    onSuccess: () => {
      toast.success("Retention settings saved");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const runNowMutation = useMutation({
    mutationFn: runRetentionNow,
    onSuccess: (result) => {
      toast.success(
        result.deleted_job_count === 0
          ? "Nothing to clean up right now"
          : `Cleaned up ${result.deleted_job_count} job(s), freed ${formatBytes(result.bytes_freed)}`,
      );
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const diskUsedPercent = storage
    ? (storage.disk_used_bytes / Math.max(1, storage.disk_total_bytes)) * 100
    : 0;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">
          Retention rules for old files, and current storage usage.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Storage overview</CardTitle>
          <CardDescription>What's currently on disk under SchoolPrint's storage root.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {storage && (
            <>
              <div className="flex flex-col gap-1.5">
                <div className="flex items-center justify-between text-sm">
                  <span>
                    {formatBytes(storage.disk_used_bytes)} used of{" "}
                    {formatBytes(storage.disk_total_bytes)}
                  </span>
                  <span className="text-muted-foreground">
                    {formatBytes(storage.disk_free_bytes)} free
                  </span>
                </div>
                <Progress value={diskUsedPercent} />
              </div>
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                <StatTile label="Uploads" value={formatBytes(storage.uploads_bytes)} />
                <StatTile label="Sliced artifacts" value={formatBytes(storage.sliced_bytes)} />
                <StatTile label="Active files" value={String(storage.active_uploaded_files)} />
                <StatTile
                  label="Pending cleanup"
                  value={String(storage.jobs_pending_retention)}
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Retention</CardTitle>
          <CardDescription>
            How long finished, rejected, and failed jobs' files are kept before automatic
            deletion. A daily background job applies these rules; you can also run it manually.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {retentionLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="retention-finished">Finished jobs (days)</Label>
              <Input
                id="retention-finished"
                type="number"
                min={1}
                value={finishedDays}
                onChange={(e) => setFinishedDays(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="retention-rejected">Rejected jobs (days)</Label>
              <Input
                id="retention-rejected"
                type="number"
                min={1}
                value={rejectedDays}
                onChange={(e) => setRejectedDays(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="retention-failed">Failed jobs (days)</Label>
              <Input
                id="retention-failed"
                type="number"
                min={1}
                value={failedDays}
                onChange={(e) => setFailedDays(e.target.value)}
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              disabled={saveMutation.isPending}
              onClick={() => saveMutation.mutate()}
            >
              <SaveIcon /> Save settings
            </Button>
            <Button
              variant="outline"
              disabled={runNowMutation.isPending}
              onClick={() => runNowMutation.mutate()}
            >
              {runNowMutation.isPending ? (
                <>
                  <PlayIcon /> Running...
                </>
              ) : (
                <>
                  <Trash2Icon /> Run cleanup now
                </>
              )}
            </Button>
          </div>
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
