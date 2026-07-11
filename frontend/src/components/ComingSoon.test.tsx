import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComingSoon } from "@/components/ComingSoon";

describe("ComingSoon", () => {
  it("renders the given title and phase", () => {
    render(<ComingSoon title="Widgets" phase="Phase 42" />);
    expect(screen.getByText("Widgets")).toBeInTheDocument();
    expect(screen.getByText(/Phase 42/)).toBeInTheDocument();
  });
});
