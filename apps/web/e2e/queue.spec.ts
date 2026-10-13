import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

type Seed = { slug: string; email: string; password: string; breached: number; calm: number };
const seed = (): Seed => JSON.parse(process.env.E2E_SEED ?? "{}") as Seed;

async function signIn(page: Page, s: Seed): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Workspace").fill(s.slug);
  await page.getByLabel("Email").fill(s.email);
  await page.getByLabel("Password").fill(s.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("heading", { name: "Queue" })).toBeVisible();
}

test("TD-007/AC-3, AC-9: breach-active ticket comes first with a text badge", async ({ page }) => {
  const s = seed();
  await signIn(page, s);
  const rows = page.getByRole("table", { name: "Ticket queue" }).getByRole("row");
  await expect(rows).toHaveCount(3); // header + 2 tickets

  const first = rows.nth(1);
  await expect(first.getByRole("cell").first()).toHaveText(String(s.breached)); // API order kept (AC-3)
  await expect(first).toContainText(/First response breached (just now|\d+[mhd] ago)/); // text, not colour (AC-9)
  await expect(rows.nth(2)).not.toContainText("breached"); // calm ticket: no badge
});

test("TD-007/AC-9: login and queue pages have no serious or critical axe violations", async ({ page }) => {
  for (const visit of [() => page.goto("/login"), () => signIn(page, seed())]) {
    await visit();
    const { violations } = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const blocking = violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(blocking.map((v) => `${v.id}: ${v.help}`)).toEqual([]);
  }
});

test("wrong password shows an error and stays on the login page", async ({ page }) => {
  const s = seed();
  await page.goto("/login");
  await page.getByLabel("Workspace").fill(s.slug);
  await page.getByLabel("Email").fill(s.email);
  await page.getByLabel("Password").fill("not-the-password");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});

test("an invalid or expired token sends the user back to sign in", async ({ page }) => {
  await page.goto("/login");
  await page.evaluate(
    (slug) => sessionStorage.setItem("ticketdesk.session", JSON.stringify({ slug, token: "expired" })),
    seed().slug,
  );
  await page.goto("/queue");
  await expect(page).toHaveURL(/\/login$/);
});
