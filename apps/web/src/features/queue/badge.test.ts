import { describe, expect, it } from "vitest";
import { breachLabel } from "./badge";

const now = new Date("2026-10-13T12:00:00Z");

describe("breachLabel (TD-007/AC-9)", () => {
  it("names the SLA type and the time since breach, in words", () => {
    expect(breachLabel({ type: "first_response", breached_at: "2026-10-13T10:00:00Z", active: true }, now)).toBe(
      "First response breached 2h ago",
    );
    expect(breachLabel({ type: "resolution", breached_at: "2026-10-13T11:59:30Z", active: true }, now)).toBe(
      "Resolution breached just now",
    );
    expect(breachLabel({ type: "resolution", breached_at: "2026-10-13T11:15:00Z", active: true }, now)).toBe(
      "Resolution breached 45m ago",
    );
    expect(breachLabel({ type: "resolution", breached_at: "2026-10-10T12:00:00Z", active: true }, now)).toBe(
      "Resolution breached 3d ago",
    );
  });

  it("shows nothing unless the breach is still active (AC-12, AC-14)", () => {
    expect(breachLabel(null, now)).toBeNull();
    expect(breachLabel({ type: "first_response", breached_at: "2026-10-13T10:00:00Z", active: false }, now)).toBeNull();
  });
});
