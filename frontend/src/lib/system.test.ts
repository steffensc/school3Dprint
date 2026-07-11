import { describe, expect, it } from "vitest";

import { formatUptime } from "@/lib/system";

describe("formatUptime", () => {
  it("formats seconds under a minute", () => {
    expect(formatUptime(30)).toBe("0m");
  });

  it("formats minutes", () => {
    expect(formatUptime(125)).toBe("2m");
  });

  it("formats hours and minutes", () => {
    expect(formatUptime(3 * 3600 + 15 * 60)).toBe("3h 15m");
  });

  it("formats days and hours", () => {
    expect(formatUptime(2 * 86400 + 5 * 3600)).toBe("2d 5h");
  });
});
