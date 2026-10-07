import { describe, expect, it } from "vitest";
import { appTitle } from "./title";

describe("appTitle", () => {
  it("trims and falls back", () => {
    expect(appTitle("  TicketDesk ")).toBe("TicketDesk");
    expect(appTitle("   ")).toBe("App");
  });
});
