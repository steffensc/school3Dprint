import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { createUpload } from "@/features/user/api";

export function UploadPage() {
  const navigate = useNavigate();
  const [title, setTitle] = React.useState("");
  const [studentNote, setStudentNote] = React.useState("");
  const [file, setFile] = React.useState<File | null>(null);

  const mutation = useMutation({
    mutationFn: () => {
      if (!file) {
        throw new Error("Please choose an STL file.");
      }
      return createUpload({ title, studentNote, file });
    },
    onSuccess: (job) => {
      toast.success("Your model was submitted. Status: waiting for approval.");
      navigate(`/user/jobs/${job.id}`);
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <div className="mx-auto max-w-lg">
      <Card>
        <CardHeader>
          <CardTitle>Upload a model</CardTitle>
          <CardDescription>
            Submit an STL file for review. A teacher will check and approve it before it is
            sliced and queued.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate();
            }}
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Keychain"
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="file">STL file</Label>
              <Input
                id="file"
                type="file"
                accept=".stl"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="note">Comment (optional)</Label>
              <Textarea
                id="note"
                value={studentNote}
                onChange={(e) => setStudentNote(e.target.value)}
                placeholder="Anything the teacher should know about this model"
              />
            </div>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Submitting..." : "Submit"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
