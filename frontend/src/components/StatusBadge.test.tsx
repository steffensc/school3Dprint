import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "@/components/StatusBadge";

describe("StatusBadge", () => {
  it("renders the human-readable label for a status", () => {
    render(<StatusBadge status="READY_TO_PRINT" />);
    expect(screen.getByText("Ready to print")).toBeInTheDocument();
  });

  it("renders a distinct label for each known status", () => {
    render(<StatusBadge status="FINISHED" />);
    expect(screen.getByText("Finished")).toBeInTheDocument();
  });
});
