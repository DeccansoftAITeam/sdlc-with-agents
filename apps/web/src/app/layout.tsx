import type { ReactNode } from "react";

export const metadata = { title: "TicketDesk", description: "Multi-tenant support desk with AI triage and AI-suggested replies" };

// Minimal styling on purpose: this course is about the delivery process, not UI design.
const css = `
body { font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; background: #fff; }
label { display: block; margin: 0.5rem 0; }
input { display: block; padding: 0.4rem; }
table { border-collapse: collapse; }
th, td { text-align: left; padding: 0.4rem 0.8rem; border-bottom: 1px solid #ccc; }
.badge-breach { font-weight: 600; color: #8a1c1c; border: 1px solid #8a1c1c; border-radius: 4px; padding: 0 0.4rem; }
`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <style>{css}</style>
        {children}
      </body>
    </html>
  );
}
