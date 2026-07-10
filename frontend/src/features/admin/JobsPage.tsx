import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckIcon, RotateCcwIcon, XIcon } from "lucide-react";
import { toast } from "sonner";

import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { approveJob, listAllJobs, rejectJob, unapproveJob } from "@/features/admin/jobsApi";
import type { PrintJob } from "@/lib/print-job";

type PendingAction = { job: PrintJob; kind: "approve" | "reject" };

export function AdminJobsPage() {
  const queryClient = useQueryClient();
  const { data: jobs, isLoading } = useQuery({ queryKey: ["admin", "jobs"], queryFn: listAllJobs });
  const [pendingAction, setPendingAction] = React.useState<PendingAction | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "jobs"] });

  const unapproveMutation = useMutation({
    mutationFn: (job: PrintJob) => unapproveJob(job.id),
    onSuccess: () => {
      toast.success("Approval withdrawn");
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">Print job requests</h1>
        <p className="text-sm text-muted-foreground">Review, approve, or reject submitted models.</p>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>User</TableHead>
            <TableHead>Class</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Submitted</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={7} className="text-center text-muted-foreground">
                Loading...
              </TableCell>
            </TableRow>
          )}
          {jobs?.map((job) => (
            <TableRow key={job.id}>
              <TableCell className="font-medium">{job.title}</TableCell>
              <TableCell>{job.owner?.display_name ?? "—"}</TableCell>
              <TableCell>{job.owner?.class_name ?? "—"}</TableCell>
              <TableCell>{job.uploaded_file.original_filename}</TableCell>
              <TableCell>{new Date(job.created_at).toLocaleString()}</TableCell>
              <TableCell>
                <StatusBadge status={job.status} />
              </TableCell>
              <TableCell className="flex justify-end gap-2">
                {job.status === "SUBMITTED" && (
                  <>
                    <Button size="sm" onClick={() => setPendingAction({ job, kind: "approve" })}>
                      <CheckIcon /> Approve
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => setPendingAction({ job, kind: "reject" })}
                    >
                      <XIcon /> Reject
                    </Button>
                  </>
                )}
                {job.status === "APPROVED" && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => unapproveMutation.mutate(job)}
                  >
                    <RotateCcwIcon /> Withdraw approval
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={pendingAction !== null} onOpenChange={(open) => !open && setPendingAction(null)}>
        {pendingAction && (
          <JobActionDialog
            action={pendingAction}
            onDone={() => {
              setPendingAction(null);
              invalidate();
            }}
          />
        )}
      </Dialog>
    </div>
  );
}

function JobActionDialog({
  action,
  onDone,
}: {
  action: PendingAction;
  onDone: () => void;
}) {
  const [note, setNote] = React.useState("");
  const isApprove = action.kind === "approve";

  const mutation = useMutation({
    mutationFn: () =>
      isApprove ? approveJob(action.job.id, note) : rejectJob(action.job.id, note),
    onSuccess: () => {
      toast.success(isApprove ? "Job approved" : "Job rejected");
      onDone();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>
          {isApprove ? "Approve" : "Reject"} "{action.job.title}"
        </DialogTitle>
      </DialogHeader>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <Textarea
          placeholder="Comment for the student (optional)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        <DialogFooter>
          <Button type="submit" variant={isApprove ? "default" : "destructive"} disabled={mutation.isPending}>
            {mutation.isPending ? "Saving..." : isApprove ? "Approve" : "Reject"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
