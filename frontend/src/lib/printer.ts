export type PrinterDriverType = "BAMBU_LAN" | "OCTOPRINT" | "MOONRAKER" | "DUMMY";

export const driverTypeLabels: Record<PrinterDriverType, string> = {
  BAMBU_LAN: "Bambu Lab (LAN mode)",
  OCTOPRINT: "OctoPrint (unsupported)",
  MOONRAKER: "Moonraker (unsupported)",
  DUMMY: "Dummy (testing/demo)",
};

export interface Printer {
  id: string;
  name: string;
  driver_type: PrinterDriverType;
  host: string | null;
  port: number | null;
  serial_number: string | null;
  location: string | null;
  is_active: boolean;
  has_access_code: boolean;
  created_at: string;
}

export interface PrinterStatus {
  status: string;
  progress: number;
  nozzle_actual: number;
  nozzle_target: number;
  bed_actual: number;
  bed_target: number;
}

export interface PrinterTestResult {
  success: boolean;
  message: string;
}
