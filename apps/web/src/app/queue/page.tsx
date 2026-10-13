"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { type QueueTicket, QueueTable } from "@/features/queue/QueueTable";
import { ApiError, api, clearSession, loadSession } from "@/lib/api";

export default function QueuePage() {
  const router = useRouter();
  const [tickets, setTickets] = useState<QueueTicket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const session = loadSession();
    if (!session) {
      router.replace("/login");
      return;
    }
    api<{ items: QueueTicket[] }>(`/t/${encodeURIComponent(session.slug)}/tickets`, {}, session.token)
      .then((page) => setTickets(page.items))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          clearSession(); // expired token: sign in again
          router.replace("/login");
          return;
        }
        setError(err instanceof Error ? err.message : "Could not load tickets");
      });
  }, [router]);

  return (
    <main>
      <h1>Queue</h1>
      {error && <p role="alert">{error}</p>}
      {tickets === null && !error ? <p>Loading…</p> : tickets && <QueueTable tickets={tickets} />}
    </main>
  );
}
