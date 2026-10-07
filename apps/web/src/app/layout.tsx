import type { ReactNode } from "react";

export const metadata = { title: "TicketDesk", description: "Multi-tenant support desk with AI triage and AI-suggested replies" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
