#!/usr/bin/env node
// Fail if a NEXT_PUBLIC_* variable looks like a secret: public env vars ship to every browser.
const fs = require("fs");
const { execSync } = require("child_process");
const files = execSync("git ls-files", { encoding: "utf8" }).split("\n").filter((f) => /(^|\/)\.env(\.|$)|next\.config\./.test(f));
const bad = /NEXT_PUBLIC_[A-Z0-9_]*(SECRET|TOKEN|KEY|PASSWORD|PRIVATE)/;
let failed = false;
for (const f of files) {
  if (!fs.existsSync(f)) continue;
  fs.readFileSync(f, "utf8").split("\n").forEach((line, i) => {
    if (bad.test(line)) { console.log(`${f}:${i + 1}: secret-looking public env var`); failed = true; }
  });
}
process.exit(failed ? 1 : 0);
