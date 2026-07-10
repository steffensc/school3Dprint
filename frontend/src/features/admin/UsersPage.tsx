import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlusIcon, KeyRoundIcon } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { createUser, listUsers, resetUserPassword, setUserActive } from "@/features/admin/api";
import type { User, UserRole } from "@/lib/types";

export function AdminUsersPage() {
  const queryClient = useQueryClient();
  const { data: users, isLoading } = useQuery({ queryKey: ["admin", "users"], queryFn: listUsers });
  const [createOpen, setCreateOpen] = React.useState(false);
  const [resetTarget, setResetTarget] = React.useState<User | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] });

  const toggleActiveMutation = useMutation({
    mutationFn: (user: User) => setUserActive(user.id, !user.is_active),
    onSuccess: (_data, user) => {
      toast.success(`${user.display_name} ${user.is_active ? "disabled" : "enabled"}`);
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">User Management</h1>
          <p className="text-sm text-muted-foreground">Create accounts, reset passwords, manage access.</p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusIcon /> New user
            </Button>
          </DialogTrigger>
          <CreateUserDialog
            onCreated={() => {
              setCreateOpen(false);
              invalidate();
            }}
          />
        </Dialog>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Username</TableHead>
            <TableHead>Display name</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Class</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                Loading...
              </TableCell>
            </TableRow>
          )}
          {users?.map((u) => (
            <TableRow key={u.id}>
              <TableCell className="font-medium">{u.username}</TableCell>
              <TableCell>{u.display_name}</TableCell>
              <TableCell>
                <Badge variant={u.role === "ADMIN" ? "default" : "secondary"}>{u.role}</Badge>
              </TableCell>
              <TableCell>{u.class_name ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={u.is_active ? "success" : "destructive"}>
                  {u.is_active ? "Active" : "Disabled"}
                </Badge>
              </TableCell>
              <TableCell className="flex justify-end gap-2">
                <Button variant="outline" size="sm" onClick={() => setResetTarget(u)}>
                  <KeyRoundIcon /> Reset password
                </Button>
                <Button
                  variant={u.is_active ? "destructive" : "secondary"}
                  size="sm"
                  onClick={() => toggleActiveMutation.mutate(u)}
                >
                  {u.is_active ? "Disable" : "Enable"}
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={resetTarget !== null} onOpenChange={(open) => !open && setResetTarget(null)}>
        {resetTarget && (
          <ResetPasswordDialog user={resetTarget} onDone={() => setResetTarget(null)} />
        )}
      </Dialog>
    </div>
  );
}

function CreateUserDialog({ onCreated }: { onCreated: () => void }) {
  const [username, setUsername] = React.useState("");
  const [displayName, setDisplayName] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [role, setRole] = React.useState<UserRole>("USER");
  const [className, setClassName] = React.useState("");

  const mutation = useMutation({
    mutationFn: () =>
      createUser({
        username,
        display_name: displayName,
        password,
        role,
        class_name: className || null,
      }),
    onSuccess: () => {
      toast.success("User created");
      onCreated();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Create user</DialogTitle>
      </DialogHeader>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="new-username">Username</Label>
          <Input id="new-username" value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="new-display-name">Display name</Label>
          <Input
            id="new-display-name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="new-password">Initial password</Label>
          <Input
            id="new-password"
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Role</Label>
          <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="USER">User (student)</SelectItem>
              <SelectItem value="ADMIN">Admin (teacher)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="new-class">Class (optional)</Label>
          <Input id="new-class" value={className} onChange={(e) => setClassName(e.target.value)} />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Create user"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}

function ResetPasswordDialog({ user, onDone }: { user: User; onDone: () => void }) {
  const [password, setPassword] = React.useState("");

  const mutation = useMutation({
    mutationFn: () => resetUserPassword(user.id, password),
    onSuccess: () => {
      toast.success(`Password reset for ${user.display_name}`);
      onDone();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Reset password for {user.display_name}</DialogTitle>
      </DialogHeader>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="reset-password">New password</Label>
          <Input
            id="reset-password"
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Resetting..." : "Reset password"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
