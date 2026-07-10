import { Badge } from "@/components/ui/badge";
import { statusBadgeVariant, statusLabels, type PrintJobStatus } from "@/lib/print-job";

export function StatusBadge({ status }: { status: PrintJobStatus }) {
  return <Badge variant={statusBadgeVariant[status]}>{statusLabels[status]}</Badge>;
}
