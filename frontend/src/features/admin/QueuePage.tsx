import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  ListPlusIcon,
  PauseIcon,
  PlayIcon,
  PrinterIcon,
  ScissorsIcon,
  SquareIcon,
  XIcon,
} from "lucide-react";
import { toast } from "sonner";

import { PrintJobLiveProgress } from "@/components/PrintJobLiveProgress";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  cancelPrint,
  getJobLiveStatus,
  listAllJobs,
  pausePrint,
  resumePrint,
  startPrint,
} from "@/features/admin/jobsApi";
import {
  enqueueJob,
  getQueue,
  moveJobDown,
  moveJobUp,
  removeFromQueue,
  sliceJob,
} from "@/features/admin/queueApi";
import { listPrinters } from "@/features/admin/printersApi";
import { StatusBadge } from "@/components/StatusBadge";
import type { PrintJob } from "@/lib/print-job";

export function AdminQueuePage() {
  const queryClient = useQueryClient();
  const { data: queue, isLoading: queueLoading } = useQuery({
    queryKey: ["admin", "queue"],
    queryFn: getQueue,
  });
  const { data: allJobs } = useQuery({ queryKey: ["admin", "jobs"], queryFn: listAllJobs });
  const { data: printers } = useQuery({ queryKey: ["admin", "printers"], queryFn: listPrinters });
  const [startTarget, setStartTarget] = React.useState<PrintJob | null>(null);

  const approvedNotQueued =
    allJobs?.filter((j) => j.status === "APPROVED" || j.status === "SLICED") ?? [];
  const printingJobs = allJobs?.filter((j) => j.status === "PRINTING" || j.status === "PAUSED") ?? [];
  const activePrinters = printers?.filter((p) => p.is_active) ?? [];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin", "queue"] });
    queryClient.invalidateQueries({ queryKey: ["admin", "jobs"] });
  };

  const pauseMutation = useMutation({
    mutationFn: (job: PrintJob) => pausePrint(job.id),
    onSuccess: () => {
      toast.success("Print paused");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });
  const resumeMutation = useMutation({
    mutationFn: (job: PrintJob) => resumePrint(job.id),
    onSuccess: () => {
      toast.success("Print resumed");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });
  const cancelMutation = useMutation({
    mutationFn: (job: PrintJob) => cancelPrint(job.id),
    onSuccess: () => {
      toast.success("Print cancelled");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const moveUpMutation = useMutation({
    mutationFn: (job: PrintJob) => moveJobUp(job.id),
    onSuccess: invalidate,
    onError: (err) => toast.error((err as Error).message),
  });
  const moveDownMutation = useMutation({
    mutationFn: (job: PrintJob) => moveJobDown(job.id),
    onSuccess: invalidate,
    onError: (err) => toast.error((err as Error).message),
  });
  const removeMutation = useMutation({
    mutationFn: (job: PrintJob) => removeFromQueue(job.id),
    onSuccess: () => {
      toast.success("Removed from queue");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });
  const enqueueMutation = useMutation({
    mutationFn: (job: PrintJob) => enqueueJob(job.id),
    onSuccess: () => {
      toast.success("Added to queue");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });
  const sliceMutation = useMutation({
    mutationFn: (job: PrintJob) => sliceJob(job.id),
    onSuccess: () => {
      toast.success("Slicing complete");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Print queue</h1>
        <p className="text-sm text-muted-foreground">Order jobs and manage what's ready to print.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Currently printing</CardTitle>
          <CardDescription>Jobs actively running on a printer right now.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {printingJobs.length === 0 && (
            <p className="text-sm text-muted-foreground">No printer is currently busy.</p>
          )}
          {printingJobs.map((job) => (
            <div key={job.id} className="flex flex-col gap-2 rounded-md border px-3 py-2">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium">{job.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {job.owner?.display_name} · {job.printer?.name ?? "Unknown printer"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={job.status} />
                  {job.status === "PRINTING" && (
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={pauseMutation.isPending}
                      onClick={() => pauseMutation.mutate(job)}
                    >
                      <PauseIcon />
                    </Button>
                  )}
                  {job.status === "PAUSED" && (
                    <Button
                      variant="outline"
                      size="icon"
                      disabled={resumeMutation.isPending}
                      onClick={() => resumeMutation.mutate(job)}
                    >
                      <PlayIcon />
                    </Button>
                  )}
                  <Button
                    variant="destructive"
                    size="icon"
                    disabled={cancelMutation.isPending}
                    onClick={() => cancelMutation.mutate(job)}
                  >
                    <SquareIcon />
                  </Button>
                </div>
              </div>
              <PrintJobLiveProgress
                jobId={job.id}
                queryKeyPrefix="admin"
                fetchLiveStatus={getJobLiveStatus}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Queue</CardTitle>
          <CardDescription>Jobs in print order.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {queueLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
          {queue?.length === 0 && (
            <p className="text-sm text-muted-foreground">The queue is empty.</p>
          )}
          {queue?.map((job, index) => (
            <div
              key={job.id}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div className="flex items-center gap-3">
                <span className="flex size-6 items-center justify-center rounded-full bg-secondary text-xs font-semibold">
                  {job.queue_position}
                </span>
                <div>
                  <p className="text-sm font-medium">{job.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {job.owner?.display_name} · {job.uploaded_file.original_filename}
                  </p>
                </div>
              </div>
              <div className="flex gap-1">
                <Button
                  size="sm"
                  disabled={activePrinters.length === 0}
                  onClick={() => setStartTarget(job)}
                  title={activePrinters.length === 0 ? "No active printers configured" : undefined}
                >
                  <PrinterIcon /> Start print
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  disabled={index === 0}
                  onClick={() => moveUpMutation.mutate(job)}
                >
                  <ArrowUpIcon />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  disabled={index === queue.length - 1}
                  onClick={() => moveDownMutation.mutate(job)}
                >
                  <ArrowDownIcon />
                </Button>
                <Button variant="destructive" size="icon" onClick={() => removeMutation.mutate(job)}>
                  <XIcon />
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Approved, not yet queued</CardTitle>
          <CardDescription>Add approved jobs to the print queue.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {approvedNotQueued.length === 0 && (
            <p className="text-sm text-muted-foreground">Nothing waiting to be queued.</p>
          )}
          {approvedNotQueued.map((job) => (
            <div
              key={job.id}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div className="flex items-center gap-2">
                <div>
                  <p className="text-sm font-medium">{job.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {job.owner?.display_name} · {job.uploaded_file.original_filename}
                  </p>
                </div>
                <StatusBadge status={job.status} />
              </div>
              <div className="flex gap-2">
                {job.status === "APPROVED" && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={sliceMutation.isPending}
                    onClick={() => sliceMutation.mutate(job)}
                  >
                    <ScissorsIcon /> Slice
                  </Button>
                )}
                <Button size="sm" onClick={() => enqueueMutation.mutate(job)}>
                  <ListPlusIcon /> Add to queue
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Dialog open={startTarget !== null} onOpenChange={(open) => !open && setStartTarget(null)}>
        {startTarget && (
          <StartPrintDialog
            job={startTarget}
            printers={activePrinters}
            onDone={() => {
              setStartTarget(null);
              invalidate();
            }}
          />
        )}
      </Dialog>
    </div>
  );
}

function StartPrintDialog({
  job,
  printers,
  onDone,
}: {
  job: PrintJob;
  printers: { id: string; name: string }[];
  onDone: () => void;
}) {
  const [printerId, setPrinterId] = React.useState(printers[0]?.id ?? "");

  const mutation = useMutation({
    mutationFn: () => startPrint(job.id, printerId),
    onSuccess: () => {
      toast.success(`Print started on ${printers.find((p) => p.id === printerId)?.name}`);
      onDone();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Start print: "{job.title}"</DialogTitle>
      </DialogHeader>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <Select value={printerId} onValueChange={setPrinterId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a printer" />
            </SelectTrigger>
            <SelectContent>
              {printers.map((printer) => (
                <SelectItem key={printer.id} value={printer.id}>
                  {printer.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <DialogFooter>
          <Button type="submit" disabled={mutation.isPending || !printerId}>
            {mutation.isPending ? "Starting..." : "Start print"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
