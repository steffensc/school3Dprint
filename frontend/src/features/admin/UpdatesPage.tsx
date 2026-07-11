import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2Icon, DownloadIcon, RefreshCwIcon, XCircleIcon } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { checkForUpdate, getUpdateStatus, installUpdate } from "@/features/admin/updatesApi";
import { getVersionInfo } from "@/features/admin/systemApi";
import { updateRunStatusLabels } from "@/lib/update";

export function AdminUpdatesPage() {
  const queryClient = useQueryClient();

  const { data: version } = useQuery({
    queryKey: ["admin", "system", "version"],
    queryFn: getVersionInfo,
    staleTime: Infinity,
  });

  const {
    data: check,
    isFetching: isChecking,
    refetch: refetchCheck,
  } = useQuery({
    queryKey: ["admin", "updates", "check"],
    queryFn: checkForUpdate,
    enabled: false,
  });

  const { data: run } = useQuery({
    queryKey: ["admin", "updates", "status"],
    queryFn: getUpdateStatus,
    refetchInterval: (query) => (query.state.data?.status === "RUNNING" ? 2000 : false),
  });

  const checkMutation = useMutation({
    mutationFn: () => refetchCheck(),
  });

  const installMutation = useMutation({
    mutationFn: installUpdate,
    onSuccess: (result) => {
      if (result.status === "SUCCEEDED") {
        toast.success("Update installed successfully");
      } else {
        toast.error("Update failed - see the log below");
      }
      queryClient.invalidateQueries({ queryKey: ["admin", "updates", "status"] });
      queryClient.invalidateQueries({ queryKey: ["admin", "system", "version"] });
    },
    onError: (err) => {
      // A successful update restarts the backend, so a network error here
      // can also just mean the container is mid-restart; the status
      // endpoint will pick the result back up once it's healthy again.
      toast.error(
        `${(err as Error).message} (if the update was actually installed, the backend may just be restarting)`,
      );
      queryClient.invalidateQueries({ queryKey: ["admin", "updates", "status"] });
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Updates</h1>
        <p className="text-sm text-muted-foreground">
          Check for new SchoolPrint releases on GitHub and install them.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Current version</CardTitle>
          <CardDescription>What's currently running.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Badge variant="secondary">{version?.container_version ?? "—"}</Badge>
          <span className="text-sm text-muted-foreground">{version?.environment}</span>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Check for updates</CardTitle>
          <CardDescription>Compares the running version against GitHub Releases.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div>
            <Button disabled={isChecking} onClick={() => checkMutation.mutate()}>
              <RefreshCwIcon /> {isChecking ? "Checking..." : "Check for updates"}
            </Button>
          </div>

          {check?.error && (
            <p className="text-sm text-destructive">{check.error}</p>
          )}

          {check && !check.error && (
            <div className="flex flex-col gap-2 rounded-md border p-3 text-sm">
              <div className="flex items-center gap-2">
                <span>Latest release:</span>
                <Badge variant={check.update_available ? "warning" : "success"}>
                  {check.latest_version ?? "unknown"}
                </Badge>
                {check.update_available ? (
                  <span className="text-muted-foreground">an update is available</span>
                ) : (
                  <span className="text-muted-foreground">you're up to date</span>
                )}
              </div>
              {check.release_url && (
                <a
                  className="text-primary underline"
                  href={check.release_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  View release notes
                </a>
              )}
              <Button
                className="w-fit"
                disabled={!check.update_available || installMutation.isPending}
                onClick={() => installMutation.mutate()}
              >
                <DownloadIcon />
                {installMutation.isPending ? "Installing..." : "Install update"}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Update log</CardTitle>
          <CardDescription>Most recent install attempt.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {!run && <p className="text-sm text-muted-foreground">No update has been installed yet.</p>}
          {run && (
            <>
              <div className="flex items-center gap-2 text-sm">
                {run.status === "SUCCEEDED" && (
                  <CheckCircle2Icon className="size-4 text-success" />
                )}
                {run.status === "FAILED" && <XCircleIcon className="size-4 text-destructive" />}
                <Badge
                  variant={
                    run.status === "SUCCEEDED"
                      ? "success"
                      : run.status === "FAILED"
                        ? "destructive"
                        : "secondary"
                  }
                >
                  {updateRunStatusLabels[run.status]}
                </Badge>
                <span className="text-muted-foreground">
                  {run.from_version} {run.to_version ? `→ ${run.to_version}` : ""}
                </span>
              </div>
              {run.log && (
                <pre className="max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs whitespace-pre-wrap">
                  {run.log}
                </pre>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
