import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlugZapIcon, PlusIcon, TrashIcon } from "lucide-react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  createPrinter,
  deletePrinter,
  listPrinters,
  testPrinterConnection,
  updatePrinter,
  type CreatePrinterPayload,
} from "@/features/admin/printersApi";
import { driverTypeLabels, type Printer, type PrinterDriverType } from "@/lib/printer";

export function AdminPrintersPage() {
  const queryClient = useQueryClient();
  const { data: printers, isLoading } = useQuery({
    queryKey: ["admin", "printers"],
    queryFn: listPrinters,
  });
  const [createOpen, setCreateOpen] = React.useState(false);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["admin", "printers"] });

  const toggleActiveMutation = useMutation({
    mutationFn: (printer: Printer) => updatePrinter(printer.id, { is_active: !printer.is_active }),
    onSuccess: (_data, printer) => {
      toast.success(`${printer.name} ${printer.is_active ? "deactivated" : "activated"}`);
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const testMutation = useMutation({
    mutationFn: (printer: Printer) => testPrinterConnection(printer.id),
    onSuccess: (result) => {
      if (result.success) {
        toast.success(result.message);
      } else {
        toast.error(result.message);
      }
    },
    onError: (err) => toast.error((err as Error).message),
  });

  const deleteMutation = useMutation({
    mutationFn: (printer: Printer) => deletePrinter(printer.id),
    onSuccess: (_data, printer) => {
      toast.success(`${printer.name} deleted`);
      invalidate();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Printers</h1>
          <p className="text-sm text-muted-foreground">
            Manage the printers this SchoolPrint instance can send jobs to.
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusIcon /> New printer
            </Button>
          </DialogTrigger>
          <CreatePrinterDialog
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
            <TableHead>Name</TableHead>
            <TableHead>Driver</TableHead>
            <TableHead>Host</TableHead>
            <TableHead>Location</TableHead>
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
          {printers?.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-center text-muted-foreground">
                No printers configured yet.
              </TableCell>
            </TableRow>
          )}
          {printers?.map((printer) => (
            <TableRow key={printer.id}>
              <TableCell className="font-medium">{printer.name}</TableCell>
              <TableCell>{driverTypeLabels[printer.driver_type]}</TableCell>
              <TableCell>
                {printer.host ? `${printer.host}${printer.port ? `:${printer.port}` : ""}` : "—"}
              </TableCell>
              <TableCell>{printer.location ?? "—"}</TableCell>
              <TableCell>
                <Badge variant={printer.is_active ? "success" : "destructive"}>
                  {printer.is_active ? "Active" : "Disabled"}
                </Badge>
              </TableCell>
              <TableCell className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={testMutation.isPending}
                  onClick={() => testMutation.mutate(printer)}
                >
                  <PlugZapIcon /> Test
                </Button>
                <Button
                  variant={printer.is_active ? "destructive" : "secondary"}
                  size="sm"
                  onClick={() => toggleActiveMutation.mutate(printer)}
                >
                  {printer.is_active ? "Disable" : "Enable"}
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    if (window.confirm(`Delete printer "${printer.name}"?`)) {
                      deleteMutation.mutate(printer);
                    }
                  }}
                >
                  <TrashIcon />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function CreatePrinterDialog({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = React.useState("");
  const [driverType, setDriverType] = React.useState<PrinterDriverType>("DUMMY");
  const [host, setHost] = React.useState("");
  const [port, setPort] = React.useState("");
  const [serialNumber, setSerialNumber] = React.useState("");
  const [location, setLocation] = React.useState("");
  const [accessCode, setAccessCode] = React.useState("");

  const mutation = useMutation({
    mutationFn: () => {
      const payload: CreatePrinterPayload = {
        name,
        driver_type: driverType,
        host: host || null,
        port: port ? Number(port) : null,
        serial_number: serialNumber || null,
        location: location || null,
        access_code: accessCode || null,
      };
      return createPrinter(payload);
    },
    onSuccess: () => {
      toast.success("Printer created");
      onCreated();
    },
    onError: (err) => toast.error((err as Error).message),
  });

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Add printer</DialogTitle>
      </DialogHeader>
      <form
        className="flex flex-col gap-4"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="printer-name">Name</Label>
          <Input id="printer-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label>Driver</Label>
          <Select
            value={driverType}
            onValueChange={(v) => setDriverType(v as PrinterDriverType)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="DUMMY">Dummy (testing/demo)</SelectItem>
              <SelectItem value="BAMBU_LAN">Bambu Lab (LAN mode)</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {driverType === "BAMBU_LAN" && (
          <>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="printer-host">IP address</Label>
              <Input
                id="printer-host"
                value={host}
                onChange={(e) => setHost(e.target.value)}
                placeholder="192.168.1.42"
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="printer-port">MQTT port (optional, default 8883)</Label>
              <Input
                id="printer-port"
                type="number"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                placeholder="8883"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="printer-serial">Serial number</Label>
              <Input
                id="printer-serial"
                value={serialNumber}
                onChange={(e) => setSerialNumber(e.target.value)}
                placeholder="01P00A000000001"
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="printer-access-code">Access code</Label>
              <Input
                id="printer-access-code"
                type="password"
                value={accessCode}
                onChange={(e) => setAccessCode(e.target.value)}
                placeholder="From the printer's network settings screen"
              />
            </div>
          </>
        )}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="printer-location">Location (optional)</Label>
          <Input
            id="printer-location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Room 3, cart 2"
          />
        </div>
        <DialogFooter>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating..." : "Add printer"}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  );
}
