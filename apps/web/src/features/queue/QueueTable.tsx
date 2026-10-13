import { type Breach, breachLabel } from "./badge";

export type QueueTicket = { number: number; subject: string; status: string; priority: string; breach: Breach | null };

/** Renders tickets in the API's order: the API floats breach-active tickets first (AC-3). */
export function QueueTable({ tickets, now }: { tickets: QueueTicket[]; now?: Date }) {
  if (tickets.length === 0) return <p>No tickets yet.</p>;
  return (
    <table>
      <caption>Ticket queue</caption>
      <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Subject</th>
          <th scope="col">Status</th>
          <th scope="col">Priority</th>
          <th scope="col">SLA</th>
        </tr>
      </thead>
      <tbody>
        {tickets.map((t) => {
          const label = breachLabel(t.breach, now);
          return (
            <tr key={t.number}>
              <td>{t.number}</td>
              <td>{t.subject}</td>
              <td>{t.status}</td>
              <td>{t.priority}</td>
              <td>{label && <span className="badge-breach">{label}</span>}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
