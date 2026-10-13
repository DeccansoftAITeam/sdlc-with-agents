import { execFileSync } from "node:child_process";
import { API_PORT, backend } from "../playwright.config";

/** Seeds a fresh tenant through the running API; the tests read it from E2E_SEED. */
export default function globalSetup(): void {
  const out = execFileSync("uv", ["run", "python", "../scripts/e2e_seed.py", `http://127.0.0.1:${API_PORT}`], {
    cwd: backend,
    encoding: "utf-8",
  });
  process.env.E2E_SEED = out.trim().split("\n").pop();
}
