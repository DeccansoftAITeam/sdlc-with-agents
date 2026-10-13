/** Browser-side API calls go through the Next rewrite at /api (next.config.mjs): same origin, no CORS. */

const KEY = "ticketdesk.session";

export type Session = { slug: string; token: string };

// Course simplification: the access token lives in sessionStorage (cleared when the tab closes).
// A production app would use an httpOnly cookie set by the backend; see M8 (security).
export function saveSession(s: Session): void {
  sessionStorage.setItem(KEY, JSON.stringify(s));
}

export function loadSession(): Session | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export async function api<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json");
  if (token) headers.set("authorization", `Bearer ${token}`);
  const r = await fetch(`/api${path}`, { ...init, headers });
  if (!r.ok) {
    const problem = (await r.json().catch(() => ({}))) as { title?: string };
    throw new Error(problem.title ?? `Request failed (${r.status})`);
  }
  return (await r.json()) as T;
}
