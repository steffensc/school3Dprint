import type { ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { PrintJobLiveProgress } from "@/components/PrintJobLiveProgress";
import { StatusBadge } from "@/components/StatusBadge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getMyJob, getMyJobLiveStatus } from "@/features/user/api";

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm">{value}</span>
    </div>
  );
}

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading } = useQuery({
    queryKey: ["user", "jobs", jobId],
    queryFn: () => getMyJob(jobId!),
    enabled: Boolean(jobId),
  });

  if (isLoading || !job) {
    return <p className="text-muted-foreground">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{job.title}</CardTitle>
            <StatusBadge status={job.status} />
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4">
          {(job.status === "PRINTING" || job.status === "PAUSED") && (
            <div className="col-span-2">
              <PrintJobLiveProgress
                jobId={job.id}
                queryKeyPrefix="user"
                fetchLiveStatus={getMyJobLiveStatus}
              />
            </div>
          )}
          <Field label="File" value={job.uploaded_file.original_filename} />
          <Field label="Queue position" value={job.queue_position ?? "—"} />
          <Field label="Submitted" value={new Date(job.created_at).toLocaleString()} />
          <Field
            label="Approved"
            value={job.approved_at ? new Date(job.approved_at).toLocaleString() : "—"}
          />
          <Field
            label="Printed"
            value={job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}
          />
          <Field
            label="Estimated print time"
            value={
              job.estimated_print_time_seconds
                ? `${Math.round(job.estimated_print_time_seconds / 60)} min`
                : "—"
            }
          />
          {job.student_note && (
            <div className="col-span-2">
              <Field label="Your comment" value={job.student_note} />
            </div>
          )}
          {job.teacher_note && (
            <div className="col-span-2">
              <Field label="Teacher comment" value={job.teacher_note} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
