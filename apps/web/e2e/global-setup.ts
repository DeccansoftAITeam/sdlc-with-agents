import { execFileSync } from "node:child_process";
import { API_PORT, BACKEND_DIR } from "./constants";

/** Seeds a fresh tenant through the running API; the tests read it from E2E_SEED. */
export default function globalSetup(): void {
  const out = execFileSync("uv", ["run", "python", "../scripts/e2e_seed.py", `http://127.0.0.1:${API_PORT}`], {
    cwd: BACKEND_DIR,
    encoding: "utf-8",
  });
  const line = out.split(/\r?\n/).find((l) => l.startsWith("E2E_SEED="));
  if (!line) throw new Error(`e2e_seed.py printed no E2E_SEED line:\n${out}`);
  process.env.E2E_SEED = line.slice("E2E_SEED=".length);
}
