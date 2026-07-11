import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { StatusBadge } from "@/components/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listMyJobs } from "@/features/user/api";

export function JobsPage() {
  const { data: jobs, isLoading } = useQuery({ queryKey: ["user", "jobs"], queryFn: listMyJobs });

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-semibold">My print jobs</h1>
        <p className="text-sm text-muted-foreground">Track the status of everything you've submitted.</p>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Title</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Queue position</TableHead>
            <TableHead>Submitted</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                Loading...
              </TableCell>
            </TableRow>
          )}
          {jobs?.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="text-center text-muted-foreground">
                No jobs yet.{" "}
                <Link to="/user/upload" className="underline">
                  Upload your first model
                </Link>
                .
              </TableCell>
            </TableRow>
          )}
          {jobs?.map((job) => (
            <TableRow key={job.id}>
              <TableCell className="font-medium">
                <Link to={`/user/jobs/${job.id}`} className="hover:underline">
                  {job.title}
                </Link>
              </TableCell>
              <TableCell>{job.uploaded_file.original_filename}</TableCell>
              <TableCell>
                <StatusBadge status={job.status} />
              </TableCell>
              <TableCell>{job.queue_position ?? "—"}</TableCell>
              <TableCell>{new Date(job.created_at).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
