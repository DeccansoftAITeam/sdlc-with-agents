/** TD-007/AC-9: the breach badge text. A text label, never colour alone, and only while active. */

export type Breach = { type: "first_response" | "resolution"; breached_at: string; active: boolean };

const TYPE_LABEL: Record<Breach["type"], string> = {
  first_response: "First response",
  resolution: "Resolution",
};

export function breachLabel(breach: Breach | null | undefined, now: Date = new Date()): string | null {
  if (!breach?.active) return null;
  const minutes = Math.floor((now.getTime() - new Date(breach.breached_at).getTime()) / 60_000);
  return `${TYPE_LABEL[breach.type]} breached ${ago(minutes)}`;
}

function ago(minutes: number): string {
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (minutes < 24 * 60) return `${Math.floor(minutes / 60)}h ago`;
  return `${Math.floor(minutes / (24 * 60))}d ago`;
}
