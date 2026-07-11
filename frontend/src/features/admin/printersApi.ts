import { api } from "@/lib/api";
import type { Printer, PrinterDriverType, PrinterStatus, PrinterTestResult } from "@/lib/printer";

export interface CreatePrinterPayload {
  name: string;
  driver_type: PrinterDriverType;
  host?: string | null;
  port?: number | null;
  serial_number?: string | null;
  location?: string | null;
  access_code?: string | null;
}

export interface UpdatePrinterPayload {
  name?: string;
  host?: string | null;
  port?: number | null;
  serial_number?: string | null;
  location?: string | null;
  access_code?: string | null;
  is_active?: boolean;
}

export async function listPrinters(): Promise<Printer[]> {
  const { data } = await api.get<Printer[]>("/admin/printers");
  return data;
}

export async function createPrinter(payload: CreatePrinterPayload): Promise<Printer> {
  const { data } = await api.post<Printer>("/admin/printers", payload);
  return data;
}

export async function updatePrinter(
  printerId: string,
  payload: UpdatePrinterPayload,
): Promise<Printer> {
  const { data } = await api.patch<Printer>(`/admin/printers/${printerId}`, payload);
  return data;
}

export async function deletePrinter(printerId: string): Promise<void> {
  await api.delete(`/admin/printers/${printerId}`);
}

export async function testPrinterConnection(printerId: string): Promise<PrinterTestResult> {
  const { data } = await api.post<PrinterTestResult>(
    `/admin/printers/${printerId}/test-connection`,
  );
  return data;
}

export async function getPrinterStatus(printerId: string): Promise<PrinterStatus> {
  const { data } = await api.get<PrinterStatus>(`/admin/printers/${printerId}/status`);
  return data;
}
