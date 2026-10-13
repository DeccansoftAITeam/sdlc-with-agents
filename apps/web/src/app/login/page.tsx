"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";
import { api, saveSession } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const slug = String(form.get("slug"));
    try {
      const { access_token } = await api<{ access_token: string }>(`/t/${encodeURIComponent(slug)}/auth/login`, {
        method: "POST",
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      saveSession({ slug, token: access_token });
      router.push("/queue");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    }
  }

  return (
    <main>
      <h1>Sign in to TicketDesk</h1>
      <form onSubmit={onSubmit}>
        <label>
          Workspace
          <input name="slug" required autoComplete="organization" />
        </label>
        <label>
          Email
          <input name="email" type="email" required autoComplete="username" />
        </label>
        <label>
          Password
          <input name="password" type="password" required autoComplete="current-password" />
        </label>
        <button type="submit">Sign in</button>
        {error && <p role="alert">{error}</p>}
      </form>
    </main>
  );
}
