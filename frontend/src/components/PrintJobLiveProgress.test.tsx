import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PrintJobLiveProgress } from "@/components/PrintJobLiveProgress";
import type { PrintJobLiveStatus } from "@/lib/print-job";

function renderWithQueryClient(children: React.ReactNode) {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>,
  );
}

describe("PrintJobLiveProgress", () => {
  it("renders nothing while the live status hasn't loaded yet", () => {
    const { container } = renderWithQueryClient(
      <PrintJobLiveProgress
        jobId="job-1"
        queryKeyPrefix="test"
        fetchLiveStatus={() => new Promise<PrintJobLiveStatus>(() => {})}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders progress and temperatures once loaded", async () => {
    const status: PrintJobLiveStatus = {
      status: "PRINTING",
      progress: 42.3,
      nozzle_actual: 210.4,
      nozzle_target: 215,
      bed_actual: 59.8,
      bed_target: 60,
    };

    renderWithQueryClient(
      <PrintJobLiveProgress
        jobId="job-1"
        queryKeyPrefix="test"
        fetchLiveStatus={() => Promise.resolve(status)}
      />,
    );

    await waitFor(() => expect(screen.getByText("42% complete")).toBeInTheDocument());
    expect(screen.getByText(/Nozzle 210.*Bed 60/)).toBeInTheDocument();
  });
});
